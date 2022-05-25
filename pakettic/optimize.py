from cmath import inf
import copy
from functools import singledispatch
import math
import random
from typing import Callable, Union
import tqdm
import zopfli
from pakettic import ast, parser, printer

_FLIPPABLE_OPS = ["*", "+", "&", "~", "|", ">", "<", ">=", "<=", "~=", "=="]
_FLIPPED_OPS = ["*", "+", "&", "~", "|", "<", ">", "<=", ">=", "~=", "=="]
_PLUSMINUS_OPS = ["+", "-"]
_MULDIV_OPS = ["*", "/"]
_AND_OR_XOR_OPS = ["&", "|", "~"]
_LOWERS = set(chr(i) for i in range(ord('a'), ord('z') + 1))
_RESERVED = {"TIC", "SCN", "BDR", "OVR", "circ", "circb", "elli", "ellib", "clip", "cls", "font", "line", "map", "pix",
             "print", "rect", "rectb", "spr", "tri", "trib", "textri", "btn", "btnp", "key", "keyp", "mouse",
             "music", "sfx", "memcpy", "memset", "pmem", "peek", "peek1", "peek2", "peek4", "poke", "poke1",
             "poke2", "poke4", "sync", "vbank", "fget", "fset", "mget", "mset", "exit", "reset", "time", "tstamp", "trace",
             "debug", "math"}


def loads_to_funcs(node: ast.Node):
    def _trans(node: ast.Node) -> ast.Node:
        if isinstance(node, ast.Call) and node.func == ast.Name("load") and len(node.args) == 1 and isinstance(node.args[0], ast.LiteralString):
            body = parser.parse_string(node.args[0].value)
            return ast.Func(body=body, args=[])
        else:
            return node
    return apply_trans(node, _trans)


def funcs_to_loads(node: ast.Node):
    def _trans(node: ast.Node) -> ast.Node:
        if isinstance(node, ast.Func) and len(node.args) == 0:
            code = printer.Formatter(double_quotes=True).format(node.body)
            return ast.Call(func=ast.Name("load"), args=[ast.LiteralString(code)])
        else:
            return node
    return apply_trans(node, _trans)


def mutate(root: ast.Node, r: random.Random):
    new_root = copy.deepcopy(root)
    mutations = []

    used_names = set()

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
        elif type(node) == ast.Alt:
            for i, _ in enumerate(node.alts[1:]):
                def _mutation(i=i):
                    node.alts[0], node.alts[i + 1] = node.alts[i + 1], node.alts[0]
                mutations.append(_mutation)
        elif type(node) == ast.Perm:
            for i in range(len(node.stats)):
                for j in range(i + 1, len(node.stats)):
                    def _mutation(i=i, j=j):
                        node.stats[i], node.stats[j] = node.stats[j], node.stats[i]
                    mutations.append(_mutation)

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
    mutations.extend((var_repl(a, b) for a in used_names for b in _LOWERS))
    mutation = r.choice(mutations)
    mutation()
    return new_root


def anneal(state, cost_func: Callable, steps: int, start_temp: float, end_temp: float, mutate_func: Callable = mutate):
    current_cost = cost_func(state, inf)
    best_cost = current_cost
    best = state
    r = random.Random(0)  # deterministic seed, to have deterministic results
    bar = tqdm.tqdm(range(steps), position=1)
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


@singledispatch
def apply_trans(node: ast.Node, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(node)


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
    return trans(ast.Func(args=node.args, body=apply_trans(node.body, trans)))


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
    return trans(ast.Perm([apply_trans(s, trans) for s in node.stats]))


@ apply_trans.register
def _(node: ast.UnaryOp, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.UnaryOp(op=node.op, operand=apply_trans(node.operand, trans)))


@singledispatch
def visit(node: ast.Node, visitor: Callable[[ast.Node], None]):
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
