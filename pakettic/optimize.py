from functools import singledispatch
from typing import Callable


from pakettic import ast, parser, printer


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
            code = printer.Formatter(doubleQuotes=True).format(node.body)
            return ast.Call(func=ast.Name("load"), args=[ast.LiteralString(code)])
        else:
            return node
    return apply_trans(node, _trans)


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
    return trans(ast.Assign(targets=node.targets, values=[apply_trans(v, trans) for v in node.values]))


@ apply_trans.register
def _(node: ast.While, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.While(apply_trans(node.condition, trans), apply_trans(node.block, trans)))


@ apply_trans.register
def _(node: ast.Repeat, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Repeat(apply_trans(node.condition, trans), apply_trans(node.block, trans)))


@ apply_trans.register
def _(node: ast.ForRange, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.ForRange(node.var, apply_trans(node.lb, trans), apply_trans(node.ub, trans), apply_trans(node.step, trans), apply_trans(node.body, trans)))


@ apply_trans.register
def _(node: ast.ForIn, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.ForIn(node.names, [apply_trans(i, trans) for i in node.exps], body=apply_trans(node.body, trans)))


@ apply_trans.register
def _(node: ast.Local, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.Local(node.targets, value=[apply_trans(v, trans) for v in node.values]))


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
def _(node: ast.UnaryOp, trans: Callable[[ast.Node], ast.Node]) -> ast.Node:
    return trans(ast.UnaryOp(op=node.op, operand=apply_trans(node.operand, trans)))
