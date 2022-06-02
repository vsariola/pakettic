from cmath import inf
import copy
from functools import singledispatch
import math
import random
from typing import Any, Callable, Union
import tqdm
from pakettic import ast, parser, printer

_FLIPPABLE_OPS = ["*", "+", "&", "~", "|", ">", "<", ">=", "<=", "~=", "=="]
_FLIPPED_OPS = ["*", "+", "&", "~", "|", "<", ">", "<=", ">=", "~=", "=="]
_PLUSMINUS_OPS = ["+", "-"]
_MULDIV_OPS = ["*", "/"]
_AND_OR_XOR_OPS = ["&", "|", "~"]
_LOWERS = list(chr(i) for i in range(ord('a'), ord('z') + 1))
_RESERVED = {'_G', 'TIC', 'SCN', 'BDR', 'OVR', '_VERSION', 'assert', 'btn', 'btnp',
             'circ', 'circb', 'clip', 'cls', 'collectgarbage', 'coroutine', 'debug',
             'dofile', 'elli', 'ellib', 'error', 'exit', 'fget', 'font', 'fset',
             'getmetatable', 'ipairs', 'key', 'keyp', 'line', 'load', 'loadfile',
             'map', 'math', 'memcpy', 'memset', 'mget', 'mouse', 'mset', 'music',
             'next', 'package', 'pairs', 'pcall', 'peek', 'peek1', 'peek2', 'peek4',
             'pix', 'pmem', 'poke', 'poke1', 'poke2', 'poke4', 'print', 'rawequal',
             'rawget', 'rawlen', 'rawset', 'rect', 'rectb', 'require', 'reset',
             'select', 'setmetatable', 'sfx', 'spr', 'str', 'string', 'sync',
             'table', 'textri', 'time', 'tonumber', 'tostring', 'trace', 'tri',
             'trib', 'tstamp', 'ttri', 'type', 'vbank', 'xpcall'}


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


def funcs_to_loads(root: ast.Node):
    """
    Transforms an abstract syntax tree by converting all function()...end into load'...'
        Parameters:
            root (ast.Node): Root of the abstract syntax tree
        Returns:
            new_root (ast.Node): Root of the new, transformed abstract syntax tree
    """
    def _trans(node: ast.Node) -> ast.Node:
        if isinstance(node, ast.Func) and len(node.args) == 0:
            code = printer.Formatter(double_quotes=True).format(node.body)
            return ast.Call(func=ast.Name("load"), args=[ast.LiteralString(code)])
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
            if type(node.left) == ast.BinOp:
                if (node.op in _PLUSMINUS_OPS and node.left.op in _PLUSMINUS_OPS) or (node.op in _MULDIV_OPS and node.left.op in _MULDIV_OPS):
                    def _mutation():
                        node.left.right, node.right = node.right, node.left.right
                        node.op, node.left.op = node.left.op, node.op
                    mutations.append(_mutation)
                if node.op in _AND_OR_XOR_OPS and node.left.op == node.op:
                    def _mutation():
                        node.left.right, node.right = node.right, node.left.right
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
            if len(node.args) == 0:
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


@singledispatch
def apply_trans(root: ast.Node, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    """
    Applies a transformation to an abstract syntax tree recursively
        Parameters:
            root (ast.Node): Root of the syntax tree to transform
            trans (Callable[[ast.Node], ast.Node]): Callback function that takes a node and returns a transformed node
        Returns:
            new_root (ast.Node): Root of the new, transformed abstract syntax tree
    """
    return trans(root)


@ apply_trans.register
def _(node: ast.Block, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Block([apply_trans(s, trans) for s in node.stats]))


@ apply_trans.register
def _(node: ast.Do, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Do(apply_trans(node.block, trans)))


@ apply_trans.register
def _(node: ast.Assign, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Assign(targets=[apply_trans(t, trans) for t in node.targets], values=[apply_trans(v, trans) for v in node.values]))


@ apply_trans.register
def _(node: ast.While, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.While(apply_trans(node.condition, trans), apply_trans(node.block, trans)))


@ apply_trans.register
def _(node: ast.Repeat, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Repeat(apply_trans(node.condition, trans), apply_trans(node.block, trans)))


@ apply_trans.register
def _(node: ast.ForRange, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.ForRange(apply_trans(node.var, trans), apply_trans(node.lb, trans), apply_trans(node.ub, trans), apply_trans(node.step, trans), apply_trans(node.body, trans)))


@ apply_trans.register
def _(node: ast.ForIn, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.ForIn([apply_trans(n, trans) for n in node.names], [apply_trans(i, trans) for i in node.exps], body=apply_trans(node.body, trans)))


@ apply_trans.register
def _(node: ast.Local, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Local([apply_trans(t, trans) for t in node.targets], value=[apply_trans(v, trans) for v in node.values]))


@ apply_trans.register
def _(node: ast.Func, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Func(args=[apply_trans(a, trans) for a in node.args], body=apply_trans(node.body, trans), oneline=node.oneline))


@ apply_trans.register
def _(node: ast.Index, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Index(apply_trans(node.obj, trans), apply_trans(node.item, trans)))


@ apply_trans.register
def _(node: ast.Table, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Table([apply_trans(f, trans) for f in node.fields]))


@ apply_trans.register
def _(node: ast.Field, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Field(value=apply_trans(node.value, trans), key=apply_trans(node.key, trans)))


@ apply_trans.register
def _(node: ast.Call, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Call(func=apply_trans(node.func, trans), args=[apply_trans(a, trans) for a in node.args]))


@ apply_trans.register
def _(node: ast.MethodCall, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.MethodCall(value=apply_trans(node.value, trans), method=node.method, args=[apply_trans(a, trans) for a in node.args]))


@ apply_trans.register
def _(node: ast.If, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.If(test=apply_trans(node.test, trans), body=apply_trans(node.body, trans), orelse=apply_trans(node.orelse, trans)))


@ apply_trans.register
def _(node: ast.BinOp, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.BinOp(left=apply_trans(node.left, trans), op=node.op, right=apply_trans(node.right, trans)))


@ apply_trans.register
def _(node: ast.Alt, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Alt([apply_trans(a, trans) for a in node.alts]))


@ apply_trans.register
def _(node: ast.Perm, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Perm([apply_trans(s, trans) for s in node.stats], allow_reorder=node.allow_reorder))


@ apply_trans.register
def _(node: ast.UnaryOp, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.UnaryOp(op=node.op, operand=apply_trans(node.operand, trans)))


@ apply_trans.register
def _(node: ast.Hint, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Hint(block=apply_trans(node.block, trans), no_hex=node.no_hex, double_quotes=node.double_quotes))


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
