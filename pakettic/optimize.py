from collections import deque
from functools import singledispatch, wraps
import inspect
import itertools
import math
import pickle
import signal
import random
from typing import Any, Callable, Optional, get_args, get_origin, get_type_hints
import tqdm
from pakettic import ast, parser
from dataclasses import dataclass, replace
from multiprocessing import Pool


def _toBase26(num):
    s = ""
    while (num > 0):
        s += (chr(ord('z') - (num - 1) % 26))
        num -= 1
        num //= 26
    return s


_FLIPPABLE_OPS = [">", "<", ">=", "<=", "~=", "=="]
_FLIPPED_OPS = ["<", ">", "<=", ">=", "~=", "=="]
_REORDERABLE_OPS = ["+", "-", "*", "/", "&", "|", "~"]
_REORDERABLE_RIGHT = [["+", "-"], ["+", "-"], ["*", "/"], ["*", "/"], ["&"], ["|"], ["~"]]
_REORDERABLE_LEFT = [True, False, True, False, True, True, True]
_EVALUABLE_OPS = {
    "+": lambda l, r: l + r,
    "-": lambda l, r: l - r,
    "*": lambda l, r: l * r,
    "/": lambda l, r: l / r,
    "//": lambda l, r: l // r,
    "%": lambda l, r: l % r,
    "^": lambda l, r: l ** r,
    "&": lambda l, r: int(l) & int(r) if int(l) == l and int(r) == r else None,
    "|": lambda l, r: int(l) | int(r) if int(l) == l and int(r) == r else None,
    "~": lambda l, r: int(l) ^ int(r) if int(l) == l and int(r) == r else None,
}

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


def minify(root: ast.Node) -> ast.Node:
    """
    Perform initial minification of the variable names
        Parameters:
            root (ast.Node): Root of the abstract syntax tree
        Returns:
            new_root (ast.Node): Root of the new, mutated abstract syntax tree
    """
    new_root = pickle.loads(pickle.dumps(root))  # pickling/unpickling is faster than deepcopy
    changed_names = dict()
    changed_labels = dict()
    name_iter = iter((name for i in itertools.count(start=1, step=1) if (name := _toBase26(i)) not in _RESERVED and name not in parser.keywords))
    label_iter = iter((name for i in itertools.count(start=1, step=1) if (name := _toBase26(i)) not in _RESERVED and name not in parser.keywords))

    def _tryget(d: dict, key: str, it):
        if key in _RESERVED:
            return key
        new = d.get(key, None)
        if new is None:
            new = next(it)
        d[key] = new
        return new

    def _minify(node: ast.Node, parent: ast.Node, attr: str):
        if type(node) == ast.Name:
            node.id = _tryget(changed_names, node.id, name_iter)
        elif type(node) == ast.Label:
            node.name = _tryget(changed_labels, node.name, label_iter)
        elif type(node) == ast.Goto:
            node.target = _tryget(changed_labels, node.target, label_iter)

    visit(new_root, _minify)
    return new_root


def mutate(root_order: tuple[ast.Node, list], rand: random.Random):
    """
    Mutates an abstract syntax tree by making small modification to it, e.g.
    flipping binary operators or changing variable names
        Parameters:
            root_order (tuple[ast.Node,list]): First item is the root of the
                abstract syntax tree, second item the chunk order in cart (can be
                nil if chunk shuffling not wanted). These will get modified, so deep
                copy them before calling this function if needed.
            (random.Random): Random number generator to use
    """
    root, order = root_order
    mutations = []
    used_names = set()
    used_labels = set()

    def _check_mutations(node: ast.Node, parent: ast.Node, attr: str):
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
                    node.right = pickle.loads(pickle.dumps(node.left))
                mutations.append(_mutation)
            if node.op in _EVALUABLE_OPS and type(node.left) == ast.Numeral and type(node.right) == ast.Numeral:
                value = _EVALUABLE_OPS[node.op](node.left.value, node.right.value)
                if value != None and int(value) == value:
                    def _mutation():
                        replace_node(parent, attr, ast.Numeral(int(value)), node)
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

        if node.original != None and parent != None:
            def _mutation():
                replace_node(parent, attr, node.original, None)

    visit(root, _check_mutations)
    used_names = sorted(used_names.difference(_RESERVED))

    def var_repl(id_a, id_b):
        def _mut():
            def _repl(node, parent, attr):
                if type(node) == ast.Name:
                    if node.id == id_a:
                        node.id = id_b
                    elif node.id == id_b:
                        node.id = id_a
            visit(root, _repl)
        return _mut
    # if both a and b are in used_names, we have both copies of a,b and b,a in the list
    # but that's probably ok: swapping variables head to head is usually better idea
    # that swapping variables with new ones
    mutations.extend((var_repl(a, b) for a in used_names for b in _LOWERS if a != b))

    def label_repl(name_a, name_b):
        def _mut():
            def _repl(node, parent, attr):
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
            visit(root, _repl)
        return _mut
    used_labels = sorted(used_labels)
    mutations.extend((label_repl(a, b)
                     for a in used_labels for b in _LOWERS if a != b))

    if order is not None and len(order) > 0:
        def chunk_swap(i, j: int):
            def _mut():
                order[i], order[j] = order[j], order[i]
            return _mut
        mutations.extend(chunk_swap(i, j) for i, _ in enumerate(
            order) for j, _ in enumerate(order) if j > i)

    if len(mutations) > 0:
        mutation = rand.choice(mutations)
        mutation()


def replace_node(parent: ast.Node, attr: str, node: ast.Node, old: ast.Node):
    """
    Replaces one node in the abstract syntax tree with another.
    Adds a reference to the old node from the new node's 'original' attribute.
        Parameters:
            parent (ast.Node): Root of the abstract syntax tree
            attr (str): parent attribute which references the node being replaced. Can be "attr.#" to replace an element of a list.
            node (ast.Node): new node
            old (ast.Node): old node that is being replaced
    """
    node.original = old
    if "." in attr:
        a, i = attr.split(".")
        getattr(parent, a)[int(i)] = node
    else:
        setattr(parent, attr, node)


class Solutions:
    processes: int
    queue: deque
    mutate_func: Callable[[Any], Any]
    cost_func: Callable[[Any, int], int]
    init_state: Any
    queue_length: int

    def __init__(self, state, seed: int, queue_length: int, processes: int, cost_func: Callable[[Any, int], int],  best_func, init=None, initargs=()):
        self.processes = processes
        if processes != 1:
            _initialize_ctrl_c_handler()
            self.pool = Pool(processes=processes, initializer=_PoolInitializer(init), initargs=(initargs,))
        else:
            self.pool = None
        self.queue = deque()
        self.cost_func = cost_func
        self.cost_func_pickled = pickle.dumps(self.cost_func)
        self.queue_length = queue_length
        self.init_state = pickle.dumps(state)
        self.seed = seed
        self.best_func = best_func

    def __enter__(self):
        if self.pool is not None:
            self.pool.__enter__()

        rng = random.Random(self.seed)
        for i in range(self.queue_length):
            if self.pool is not None:
                self.put(self.init_state, pickle.dumps(rng), first=i == 0)
            else:
                self.put(self.init_state, pickle.loads(pickle.dumps(rng)), first=i == 0)
            rng = random.Random(rng.getrandbits(32))  # shuffle the rng so that the different rngs are used
        return self

    def __exit__(self, *args):
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
            self.pool.__exit__(*args)

    def get(self):
        if self.pool is not None:
            value = self.queue.popleft().get(timeout=9999)
            if value is None:
                raise KeyboardInterrupt
            return value
        else:
            state, rng, first = self.queue.popleft()
            return _mutate_cost(state, rng, self.cost_func, first)

    def put(self, state, rng, first=False):
        if self.pool is not None:
            self.queue.append(self.pool.apply_async(_mutate_cost_pickled, (state, rng, self.cost_func_pickled, first)))
        else:
            self.queue.append((state, rng, first))

    def best(self, state, finisher):
        self.best_func(state, finisher)


def anneal(solutions: Solutions, steps: int, start_temp: float, end_temp: float, seed: int = 0) -> Any:
    """
    Perform simulated annealing optimization, using exponential temperature schedule.
    See https://en.wikipedia.org/wiki/Simulated_annealing
        Parameters:
            solutions (Solutions): the Solutions object with a pool of solutions, cost function and best function
            steps (int): how many steps the optimization algorithms takes
            start_temp (float): starting temperature for the optimization
            end_temp (float): end temperature for the optimization
            seed (int): seed for the random number generator
        Returns:
            best (Any): The best solution found
    """
    state, current_cost, rng, finalize = solutions.get()
    solutions.best(state, finalize)
    best_cost = current_cost
    best = state
    r = random.Random(seed)  # deterministic seed, to have deterministic results
    bar = tqdm.tqdm(_stepsGenerator(steps), position=1, leave=False)
    for i in bar:
        solutions.put(state, rng)
        alpha = i / (steps - 1)
        temp = math.exp((1 - alpha) * math.log(start_temp) + alpha * math.log(end_temp))
        candidate, cand_cost, rng, finalize = solutions.get()
        if cand_cost < current_cost or math.exp(-(cand_cost - current_cost) / temp) >= r.random():
            current_cost = cand_cost
            state = candidate
        if cand_cost < best_cost:
            best_cost = cand_cost
            best = candidate
            solutions.best(best, finalize)
        bar.set_description(f"B:{best_cost} C:{current_cost} A:{cand_cost} T: {temp:.1f}")
        if best_cost <= 0:
            break
    return best


def lahc(solutions: Solutions, steps: int, list_length: int, init_margin: int) -> Any:
    """
    Optimize a function using Late Acceptance Hill Climbing
    See https://arxiv.org/pdf/1806.09328.pdf
        Parameters:
            solutions (Solutions): the Solutions object with a pool of solutions, cost function and best function
            steps (int): how many steps the optimization algorithms takes
            list_length (int): length of the history in the algorithm
            init_margin (int): how much margin, in bytes, to add to the initial best cost
        Returns:
            best (Any): The best solution found
    """
    state, current_cost, rng, finalize = solutions.get()
    solutions.best(state, finalize)
    best_cost = current_cost
    history = [best_cost + init_margin] * list_length
    best = state
    bar = tqdm.tqdm(_stepsGenerator(steps), position=1, leave=False)
    for i in bar:
        solutions.put(state, rng)
        candidate, cand_cost, rng, finalize = solutions.get()
        v = i % list_length
        if cand_cost < history[v] or cand_cost <= current_cost:
            current_cost = cand_cost
            state = candidate
        if current_cost < history[v]:
            history[v] = current_cost
        if cand_cost < best_cost:
            best_cost = cand_cost
            best = candidate
            solutions.best(best, finalize)
        bar.set_description(f"B:{best_cost} C:{current_cost} A:{cand_cost}")
        if best_cost <= 0:
            break
    return best


def dlas(solutions: Solutions, steps: int, list_length: int, init_margin: int) -> Any:
    """
    Optimize a function using Diversified Late Acceptance Search
    See https://arxiv.org/pdf/1806.09328.pdf
        Parameters:
            solutions (Solutions): the Solutions object with a pool of solutions, cost function and best function
            steps (int): how many steps the optimization algorithms takes
            list_length (int): length of the history in the algorithm
            init_margin (int): how much margin, in bytes, to add to the initial best cost
        Returns:
            best (Any): The best solution found
    """
    state, current_cost, rng, finalize = solutions.get()
    solutions.best(state, finalize)
    best_cost = current_cost
    cost_max = best_cost + init_margin
    history = [cost_max] * list_length
    N = list_length
    best = state
    bar = tqdm.tqdm(_stepsGenerator(steps), position=1, leave=False)
    for i in bar:
        solutions.put(state, rng)
        prev_cost = current_cost
        candidate, cand_cost, rng, finalize = solutions.get()
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
            solutions.best(best, finalize)
        bar.set_description(f"B:{best_cost} C:{current_cost} M:{cost_max} A:{cand_cost}")
        if best_cost <= 0:
            break
    return best


def _ctrl_c_handler(*args, **kwargs):
    global ctrl_c_entered
    ctrl_c_entered = True


def _initialize_ctrl_c_handler():
    # set global variable for each process in the pool:
    global ctrl_c_entered
    ctrl_c_entered = False
    signal.signal(signal.SIGINT, _ctrl_c_handler)


@dataclass
class _PoolInitializer:
    """
    This class was just a simple lambda function, but it is not possible to pickle lambda functions with default pickling
    """
    init: Callable[[Any], None]

    def __call__(self, a):
        _initialize_ctrl_c_handler()
        if self.init is not None:
            self.init(a)


def _mutate_cost(state, rng, cost_func, first):
    state = pickle.loads(state)
    if not first:
        mutate(state, rng)
    new_cost, finish_write = cost_func(state)
    return pickle.dumps(state), new_cost, rng, finish_write


def _mutate_cost_pickled(state, rng, cost_func, first):
    global ctrl_c_entered
    if ctrl_c_entered:
        return None
    rng = pickle.loads(rng)
    state = pickle.loads(state)
    if not first:
        mutate(state, rng)
    new_cost, finish_write = pickle.loads(cost_func)(state)
    return pickle.dumps(state), new_cost, pickle.dumps(rng), finish_write


def _stepsGenerator(steps: int):
    """
    Generator for the steps of the optimization algorithms, taking into account that 0 means infinite steps
    """
    if steps == 0:
        return itertools.count()
    else:
        return range(steps)


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
            if origin is Optional:
                if attr is None:
                    continue
                origin = args
            if origin is list and len(args) > 0 and issubclass(args[0], ast.Node):
                replaces[name] = [apply_trans(e, trans) for e in attr]
            elif inspect.isclass(typehint) and issubclass(typehint, ast.Node):
                replaces[name] = apply_trans(attr, trans)
    except TypeError:
        pass
    return trans(replace(node, **replaces))


@singledispatch
def visit(node: ast.Node, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    """
    Visit each node of an abstract syntax tree recursively
        Parameters:
            node (ast.Node): A (root) node of the syntax tree to visit
            visitor (Callable[[ast.Node, ast.Node, str], None]): Callback function called for each node
    """
    if node != None:
        visitor(node, parent, attr)


@ visit.register
def _(node: ast.Block, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for s in node.stats:
        visit(s, visitor)


@ visit.register
def _(node: ast.Return, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, e in enumerate(node.exps):
        visit(e, visitor, node, f"exps.{i}")


@ visit.register
def _(node: ast.Do, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.block, visitor, node, "block")


@ visit.register
def _(node: ast.Assign, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, t in enumerate(node.targets):
        visit(t, visitor, node, f"targets.{i}")
    for i, v in enumerate(node.values):
        visit(v, visitor, node, f"values.{i}")


@ visit.register
def _(node: ast.While, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.condition, visitor, node, "condition")
    visit(node.block, visitor, node, "block")


@ visit.register
def _(node: ast.Repeat, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.block, visitor, node, "block")
    visit(node.condition, visitor, node, "condition")


@ visit.register
def _(node: ast.ForRange, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.var, visitor, node, "var")
    visit(node.lb, visitor, node, "lb")
    visit(node.ub, visitor, node, "ub")
    visit(node.step, visitor, node, "step")
    visit(node.body, visitor, node, "body")


@ visit.register
def _(node: ast.ForIn, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, n in enumerate(node.names):
        visit(n, visitor, node, f"names.{i}")
    for i, e in enumerate(node.exps):
        visit(e, visitor, node, f"exps.{i}")
    visit(node.body, visitor, node, "body")


@ visit.register
def _(node: ast.Local, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, t in enumerate(node.targets):
        visit(t, visitor, node, f"targets.{i}")
    if node.values is not None:
        for i, v in enumerate(node.values):
            visit(v, visitor, node, f"values.{i}")


@ visit.register
def _(node: ast.Func, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, a in enumerate(node.args):
        visit(a, visitor, node, f"args.{i}")
    visit(node.body, visitor, node, "body")


@ visit.register
def _(node: ast.Index, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.obj, visitor, node, "obj")
    visit(node.item, visitor, node, "item")


@ visit.register
def _(node: ast.Table, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, f in enumerate(node.fields):
        visit(f, visitor, node, f"fields.{i}")


@ visit.register
def _(node: ast.Field, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.key, visitor, node, "key")
    visit(node.value, visitor, node, "value")


@ visit.register(ast.MethodCall)
def _(node: ast.MethodCall, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.value, visitor, node, "value")
    for i, a in enumerate(node.args):
        visit(a, visitor, node, f"args.{i}")


@ visit.register(ast.Call)
def _(node: ast.Call, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.func, visitor, node, "func")
    for i, a in enumerate(node.args):
        visit(a, visitor, node, f"args.{i}")


@ visit.register
def _(node: ast.If, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.test, visitor, node, "test")
    visit(node.body, visitor, node, "body")
    visit(node.orelse, visitor, node, "orelse")


@ visit.register
def _(node: ast.BinOp, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.left, visitor, node, "left")
    visit(node.right, visitor, node, "right")


@ visit.register
def _(node: ast.UnaryOp, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.operand, visitor, node, "operand")


@ visit.register
def _(node: ast.Alt, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, a in enumerate(node.alts):
        visit(a, visitor, node, f"alts.{i}")


@ visit.register
def _(node: ast.Perm, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    for i, s in enumerate(node.stats):
        visit(s, visitor, node, f"stats.{i}")


@ visit.register
def _(node: ast.Hint, visitor: Callable[[ast.Node, ast.Node, str], None], parent: ast.Node = None, attr: str = None):
    visitor(node, parent, attr)
    visit(node.block, visitor, node, "block")
