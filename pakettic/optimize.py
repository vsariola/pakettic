from cmath import inf
import copy
from functools import singledispatch
import inspect
import math
import random
from typing import Any, Callable, Optional, Union, get_args, get_origin, get_type_hints
import tqdm
from pakettic import ast, parser
from dataclasses import replace

_FLIPPABLE_OPS = [">", "<", ">=", "<=", "~=", "=="]
_FLIPPED_OPS = ["<", ">", "<=", ">=", "~=", "=="]
_REORDERABLE_OPS = ["+", "-", "*", "/", "&", "|", "~"]
_REORDERABLE_RIGHT = [["+", "-"], ["+", "-"], ["*", "/"], ["*", "/"], ["&"], ["|"], ["~"]]
_REORDERABLE_LEFT = [True, False, True, False, True, True, True]

_LOWERS = list(chr(i) for i in range(ord('a'), ord('z') + 1))
_RESERVED = {'_G', 'BDR', 'SCN', 'BOOT', 'TIC', 'OVR', 'MENU', '_VERSION',
             'assert', 'btn', 'btnp', 'circ', 'circb', 'clip', 'cls',
             'collectgarbage', 'coroutine', 'debug', 'dofile', 'elli', 'ellib',
             'error', 'exit', 'fget', 'font', 'fset', 'getmetatable', 'ipairs',
             'key', 'keyp', 'line', 'load', 'loadfile', 'map', 'math', 'memcpy',
             'memset', 'mget', 'mouse', 'mset', 'music', 'next', 'package',
             'pairs', 'pcall', 'peek', 'peek1', 'peek2', 'peek4', 'pix', 'pmem',
             'poke', 'poke1', 'poke2', 'poke4', 'print', 'rawequal', 'rawget',
             'rawlen', 'rawset', 'rect', 'rectb', 'require', 'reset', 'select',
             'self', 'setmetatable', 'sfx', 'spr', 'str', 'string', 'sync', 'table',
             'textri', 'time', 'tonumber', 'tostring', 'trace', 'tri', 'trib',
             'tstamp', 'ttri', 'type', 'vbank', 'xpcall'}
_TWO = ast.Numeral(2)


def loads_to_funcs(root: ast.Node) -> ast.Node:
    """
    Transforms an abstract syntax tree by converting all load'...' into function()...end
        Parameters:
            root (ast.Node): Root of the abstract syntax tree
        Returns:
            new_root (ast.Node): Root of the new, transformed abstract syntax tree
    """
    def _trans(node: ast.Node) -> ast.Node:
        if isinstance(node, ast.Call) and node.func == ast.Name("load") and len(node.args) == 1 and isinstance(node.args[0], ast.LiteralString):
            body = parser.parse_string(node.args[0].value)
            return ast.Func(body=body, args=[])
        else:
            return node
    return apply_trans(root, _trans)


def mutate(root: ast.Node, rand: random.Random) -> ast.Node:
    """
    Mutates an abstract syntax tree by making small modification to it,
    e.g. flipping binary operators or changing variable names
        Parameters:
            root (ast.Node): Root of the abstract syntax tree
            rand (random.Random): Random number generator to use
        Returns:
            new_root (ast.Node): Root of the new, mutated abstract syntax tree
    """
    new_root = copy.deepcopy(root)
    mutations = []

    used_names = set()
    used_labels = set()

    def _check_mutations(node: ast.Node):
        if type(node) == ast.BinOp:
            try:
                i = _FLIPPABLE_OPS.index(node.op)

                def _mutation():
                    node.left, node.right = node.right, node.left
                    node.op = _FLIPPED_OPS[i]
                mutations.append(_mutation)
            except:
                pass
            try:
                i = _REORDERABLE_OPS.index(node.op)
                node2 = node
                while type(node2.left) == ast.BinOp and node2.left.op in _REORDERABLE_RIGHT[i]:
                    def _mutation(a=node2.left, b=node):
                        a.right, b.right = b.right, a.right
                        a.op, b.op = b.op, a.op
                    mutations.append(_mutation)
                    node2 = node2.left
                if _REORDERABLE_LEFT[i]:
                    def _mutation():
                        node2.left, node.right = node.right, node2.left
                    mutations.append(_mutation)
            except:
                pass
            if node.op == "*" and node.left == node.right:
                def _mutation():
                    node.op = "^"
                    node.right = _TWO
                mutations.append(_mutation)
            if node.op == "^" and node.right == _TWO:
                def _mutation():
                    node.op = "*"
                    node.right = copy.deepcopy(node.left)
                mutations.append(_mutation)
        elif type(node) == ast.Name:
            used_names.add(node.id)
        elif type(node) == ast.Label:
            used_labels.add(node.name)
        elif type(node) == ast.Goto:
            used_labels.add(node.target)
        elif type(node) == ast.Alt:
            for i, _ in enumerate(node.alts[1:]):
                def _mutation(i=i):
                    node.alts[0], node.alts[i + 1] = node.alts[i + 1], node.alts[0]
                mutations.append(_mutation)
        elif type(node) == ast.Perm:
            if node.allow_reorder:
                for i in range(len(node.stats)):
                    for j in range(i + 1, len(node.stats)):
                        def _mutation(i=i, j=j):
                            node.stats[i], node.stats[j] = node.stats[j], node.stats[i]
                        mutations.append(_mutation)
        elif type(node) == ast.Func:
            if len(node.args) == 0 or (len(node.args) == 1 and type(node.args[0]) == ast.Ellipsis):
                def _mutation():
                    node.oneline = not node.oneline
                mutations.append(_mutation)
        elif type(node) == ast.ForRange:
            if node.step is None or node.step == ast.Numeral(1):
                def _mutation():
                    node.step = ast.Numeral(1) if node.step is None else None
                mutations.append(_mutation)
        elif type(node) == ast.Hint:
            def _mutation():
                node.double_quotes = not node.double_quotes
            mutations.append(_mutation)

            def _mutation2():
                node.no_hex = not node.no_hex
            mutations.append(_mutation2)

    visit(new_root, _check_mutations)
    used_names = sorted(used_names.difference(_RESERVED))

    def var_repl(id_a, id_b):
        def _mut():
            def _repl(node):
                if type(node) == ast.Name:
                    if node.id == id_a:
                        node.id = id_b
                    elif node.id == id_b:
                        node.id = id_a
            visit(new_root, _repl)
        return _mut
    # if both a and b are in used_names, we have both copies of a,b and b,a in the list
    # but that's probably ok: swapping variables head to head is usually better idea
    # that swapping variables with new ones
    mutations.extend((var_repl(a, b) for a in used_names for b in _LOWERS if a != b))

    def label_repl(name_a, name_b):
        def _mut():
            def _repl(node):
                if type(node) == ast.Label:
                    if node.name == name_a:
                        node.name = name_b
                    elif node.name == name_b:
                        node.name = name_a
                if type(node) == ast.Goto:
                    if node.target == name_a:
                        node.target = name_b
                    elif node.target == name_b:
                        node.target = name_a
            visit(new_root, _repl)
        return _mut
    used_labels = sorted(used_labels)
    mutations.extend((label_repl(a, b) for a in used_labels for b in _LOWERS if a != b))
    mutation = rand.choice(mutations)
    mutation()
    return new_root


def anneal(state: Any, cost_func: Callable[[Any, int], int], steps: int, start_temp: float, end_temp: float, seed: int, mutate_func: Callable[[Any], Any] = mutate) -> Any:
    """
    Perform simulated annealing optimization, using exponential temperature schedule.
    See https://en.wikipedia.org/wiki/Simulated_annealing
        Parameters:
            state: Starting state for the
            cost_func (Callable[[Any, int], int]): Callback function, with the first parameter the state and second parameter the cost of best solution so far
            steps (int): how many steps the optimization algorithms takes
            start_temp (float): starting temperature for the optimization
            end_temp (float): end temperature for the optimization
            mutate_func (Callable[[Any], Any]): Callback function state -> state that performs a small mutation in the code
        Returns:
            best (Any): The best solution found
    """
    current_cost = cost_func(state, inf)
    best_cost = current_cost
    best = state
    r = random.Random(seed)  # deterministic seed, to have deterministic results
    bar = tqdm.tqdm(range(steps), position=1, leave=False)
    for i in bar:
        alpha = i / (steps - 1)
        temp = math.exp((1 - alpha) * math.log(start_temp) + alpha * math.log(end_temp))
        candidate = mutate_func(state, r)
        cand_cost = cost_func(candidate, best_cost)
        if cand_cost < current_cost or math.exp(-(cand_cost - current_cost) / temp) >= r.random():
            current_cost = cand_cost
            state = candidate
        if cand_cost < best_cost:
            best_cost = cand_cost
            best = candidate
        bar.set_description(f"B:{best_cost} C:{current_cost} A:{cand_cost} T: {temp:.1f}")
        if best_cost <= 0:
            break
    return best


def lahc(state: Any, cost_func: Callable[[Any, int], int], steps: int, list_length: int, init_margin: int, seed: int, mutate_func: Callable[[Any], Any] = mutate) -> Any:
    """
    Optimize a function using Late Acceptance Hill Climbing
    See https://arxiv.org/pdf/1806.09328.pdf
        Parameters:
            state: Starting state for the
            cost_func (Callable[[Any, int], int]): Callback function, with the first parameter the state and second parameter the cost of best solution so far
            steps (int): how many steps the optimization algorithms takes
            list_length (int): length of the history in the algorithm
            init_margin (int): how much margin, in bytes, to add to the initial best cost
            mutate_func (Callable[[Any], Any]): Callback function state -> state that performs a small mutation in the code
        Returns:
            best (Any): The best solution found
    """
    current_cost = cost_func(state, inf)
    best_cost = current_cost
    history = [best_cost + init_margin] * list_length
    best = state
    r = random.Random(seed)  # deterministic seed, to have deterministic results
    bar = tqdm.tqdm(range(steps), position=1, leave=False)
    for i in bar:
        candidate = mutate_func(state, r)
        cand_cost = cost_func(candidate, best_cost)
        v = i % list_length
        if cand_cost < history[v] or cand_cost <= current_cost:
            current_cost = cand_cost
            state = candidate
        if current_cost < history[v]:
            history[v] = current_cost
        if cand_cost < best_cost:
            best_cost = cand_cost
            best = candidate
        bar.set_description(f"B:{best_cost} C:{current_cost} A:{cand_cost}")
        if best_cost <= 0:
            break
    return best


def dlas(state: Any, cost_func: Callable[[Any, int], int], steps: int, list_length: int, init_margin: int, seed: int, mutate_func: Callable[[Any], Any] = mutate) -> Any:
    """
    Optimize a function using Diversified Late Acceptance Search
    See https://arxiv.org/pdf/1806.09328.pdf
        Parameters:
            state: Starting state for the
            cost_func (Callable[[Any, int], int]): Callback function, with the first parameter the state and second parameter the cost of best solution so far
            steps (int): how many steps the optimization algorithms takes
            list_length (int): length of the history in the algorithm
            init_margin (int): how much margin, in bytes, to add to the initial best cost
            mutate_func (Callable[[Any], Any]): Callback function state -> state that performs a small mutation in the code
        Returns:
            best (Any): The best solution found
    """
    current_cost = cost_func(state, inf)
    best_cost = current_cost
    cost_max = best_cost + init_margin
    history = [cost_max] * list_length
    N = list_length
    best = state
    r = random.Random(seed)  # deterministic seed, to have deterministic results
    bar = tqdm.tqdm(range(steps), position=1, leave=False)
    for i in bar:
        prev_cost = current_cost
        candidate = mutate_func(state, r)
        cand_cost = cost_func(candidate, best_cost)
        v = i % list_length
        if cand_cost == current_cost or cand_cost < cost_max:
            current_cost = cand_cost
            state = candidate
        if current_cost > history[v]:
            history[v] = current_cost
        elif current_cost < history[v] and current_cost < prev_cost:
            if history[v] == cost_max:
                N -= 1
            history[v] = current_cost
            if N <= 0:
                cost_max = max(history)
                N = history.count(cost_max)
        if cand_cost < best_cost:
            best_cost = cand_cost
            best = candidate
        bar.set_description(f"B:{best_cost} C:{current_cost} M:{cost_max} A:{cand_cost}")
        if best_cost <= 0:
            break
    return best


def apply_trans(node: ast.Node, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    """
    Applies a transformation to an abstract syntax tree recursively
        Parameters:
            node (ast.Node): Root of the syntax tree to transform
            trans (Callable[[ast.Node], ast.Node]): Callback function that takes a node and returns a transformed node
        Returns:
            new_node (ast.Node): Root of the new, transformed abstract syntax tree
    """
    if node is None:
        return trans(node)
    replaces = dict()
    try:
        for name, typehint in get_type_hints(node).items():
            attr = getattr(node, name)
            origin = get_origin(typehint)
            args = get_args(typehint)
            if origin is list and len(args) > 0 and issubclass(args[0], ast.Node):
                replaces[name] = [apply_trans(e, trans) for e in attr]
            elif origin is Optional:
                if attr is not None:
                    replaces[name] = apply_trans(attr, trans)
            elif inspect.isclass(typehint) and issubclass(typehint, ast.Node):
                replaces[name] = apply_trans(attr, trans)
    except TypeError:
        pass
    return trans(replace(node, **replaces))


@singledispatch
def visit(node: ast.Node, visitor: Callable[[ast.Node], None]):
    """
    Visit each node of an abstract syntax tree recursively
        Parameters:
            node (ast.Node): A (root) node of the syntax tree to visit
            visitor (Callable[[ast.Node], Node]): Callback function called for each node
    """
    visitor(node)


@ visit.register
def _(node: ast.Block, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for s in node.stats:
        visit(s, visitor)


@ visit.register
def _(node: ast.Return, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for e in node.exps:
        visit(e, visitor)


@ visit.register
def _(node: ast.Do, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.block, visitor)


@ visit.register
def _(node: ast.Assign, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for t in node.targets:
        visit(t, visitor)
    for v in node.values:
        visit(v, visitor)


@ visit.register
def _(node: ast.While, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.condition, visitor)
    visit(node.block, visitor)


@ visit.register
def _(node: ast.Repeat, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.block, visitor)
    visit(node.condition, visitor)


@ visit.register
def _(node: ast.ForRange, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.var, visitor)
    visit(node.lb, visitor)
    visit(node.ub, visitor)
    visit(node.step, visitor)
    visit(node.body, visitor)


@ visit.register
def _(node: ast.ForIn, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for i in node.names:
        visit(i, visitor)
    for i in node.exps:
        visit(i, visitor)
    visit(node.body, visitor)


@ visit.register
def _(node: ast.Local, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for t in node.targets:
        visit(t, visitor)
    for v in node.values:
        visit(v, visitor)


@ visit.register
def _(node: ast.Func, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for a in node.args:
        visit(a, visitor)
    visit(node.body, visitor)


@ visit.register
def _(node: ast.Index, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.obj, visitor)
    visit(node.item, visitor)


@ visit.register
def _(node: ast.Table, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for f in node.fields:
        visit(f, visitor)


@ visit.register
def _(node: ast.Field, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.key, visitor)
    visit(node.value, visitor)


@ visit.register(ast.MethodCall)
@ visit.register(ast.Call)
def _(node: Union[ast.Call, ast.MethodCall], visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.func, visitor)
    for a in node.args:
        visit(a, visitor)


@ visit.register
def _(node: ast.If, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.test, visitor)
    visit(node.body, visitor)
    visit(node.orelse, visitor)


@ visit.register
def _(node: ast.BinOp, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.left, visitor)
    visit(node.right, visitor)


@ visit.register
def _(node: ast.UnaryOp, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.operand, visitor)


@ visit.register
def _(node: ast.Alt, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for a in node.alts:
        visit(a, visitor)


@ visit.register
def _(node: ast.Perm, visitor: Callable[[ast.Node], None]):
    visitor(node)
    for s in node.stats:
        visit(s, visitor)


@ visit.register
def _(node: ast.Hint, visitor: Callable[[ast.Node], None]):
    visitor(node)
    visit(node.block, visitor)
