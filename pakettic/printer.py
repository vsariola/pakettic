

from dataclasses import dataclass
from functools import singledispatch
import typing
import re
from pakettic import ast


def format(node: ast.Node, pretty: bool = False, no_load: bool = False) -> str:
    return Formatter(pretty=pretty, no_load=no_load).format(node)


_hexy = re.compile(r'[0-9a-fxA-FXpP\.]').search
_alphaunder = re.compile('[_a-zA-Z]').search
_alphanumunder = re.compile('[_a-zA-Z0-9]').search
_single_quote_translation = str.maketrans({"\n": r"\n",
                                           "\t": r"\t",
                                           "\f": r"\f",
                                           "\r": r"\r",
                                           "\\": r"\\",
                                           "'": r"\'"})
_double_quote_translation = str.maketrans({"\n": r"\n",
                                           "\t": r"\t",
                                           "\f": r"\f",
                                           "\r": r"\r",
                                           "\\": r"\\",
                                           "\"": r'\"'})


@dataclass
class Formatter:
    indent: int = 0
    double_quotes: bool = False
    pretty: bool = False
    no_hex: bool = False
    no_load: bool = False

    def format(self, node: ast.Node) -> str:
        tokens = _traverse(node, self)
        return ''.join(self.__addspaces(tokens))

    @property
    def __quote(self):
        return '"' if self.double_quotes else "'"

    def escape(self, s: str):
        return f"{self.__quote}{s.translate(_double_quote_translation if self.double_quotes else _single_quote_translation)}{self.__quote}"

    def __addspaces(self, tokens: typing.Iterable[str]):
        prevtoken = ' '
        for token in tokens:
            if type(token) is str:
                if len(token) == 0:
                    continue
                if type(prevtoken) is str and bool(_alphaunder(prevtoken[0])) and bool(_alphanumunder(token[0])):
                    # the previous token was word, and the next continues with a character that might be confused with it
                    yield ' '
                elif type(prevtoken) is ast.Numeral and bool(_hexy(token[0])):
                    yield ' '  # the previous token was numeral and the next starts with something that be confused with a hex or a decimal point
                yield token
            elif type(token) is ast.Numeral:
                strnumeral = str(token)
                if strnumeral[0] != '.' and type(prevtoken) is str and bool(_alphaunder(prevtoken[0])):
                    # the previous token was word, and the next continues with a character that might be confused with it
                    yield ' '
                yield strnumeral
            prevtoken = token


# This used to be a singledispatchmethod of Formatter, but for some reason, @singledispatchmethod are far slower than
# @singledispatch
@ singledispatch
def _traverse(node: ast.Node, fmt: Formatter):
    # raise TypeError("_print encounted unknown ast.node")
    yield str(node)


@ _traverse.register
def _(node: ast.Block, fmt: Formatter):
    for n in node.stats:
        if fmt.pretty:
            yield '  ' * fmt.indent
        yield from _traverse(n, fmt)
        if fmt.pretty:
            yield '\n'


@ _traverse.register
def _(node: ast.Return, fmt: Formatter):
    yield 'return'
    for i, v in enumerate(node.exps):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)


@ _traverse.register
def _(node: ast.Perm, fmt: Formatter):
    if fmt.pretty:
        if node.allow_reorder:
            yield '--{'
        else:
            yield '--{!'
        yield '\n'
        yield '  ' * fmt.indent
    for i, n in enumerate(node.stats):
        if fmt.pretty and i > 0:
            yield '  ' * fmt.indent
        yield from _traverse(n, fmt)
        if fmt.pretty and i < len(node.stats) - 1:
            yield '\n'
    if fmt.pretty:
        yield '\n'
        yield '  ' * fmt.indent
        yield '--}'


@ _traverse.register
def _(node: ast.Do, fmt: Formatter):
    yield 'do'
    if fmt.pretty:
        yield '\n'
    fmt.indent += 1
    yield from _traverse(node.block, fmt)
    fmt.indent -= 1
    if fmt.pretty:
        yield '  ' * fmt.indent
    yield 'end'


@ _traverse.register
def _(node: ast.Assign, fmt: Formatter):
    for i, v in enumerate(node.targets):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)
    yield '='
    for i, v in enumerate(node.values):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)


@ _traverse.register
def _(node: ast.Label, fmt: Formatter):
    yield '::'
    yield node.name
    yield '::'


@ _traverse.register
def _(node: ast.Break, fmt: Formatter):
    yield 'break'


@ _traverse.register
def _(node: ast.LiteralString, fmt: Formatter):
    yield fmt.escape(node.value)


@ _traverse.register
def _(node: ast.Goto, fmt: Formatter):
    yield 'goto'
    yield node.target


@ _traverse.register
def _(node: ast.Boolean, fmt: Formatter):
    yield 'true' if node.value else 'false'


@ _traverse.register
def _(node: ast.Ellipsis, fmt: Formatter):
    yield '...'


@ _traverse.register
def _(node: ast.Nil, fmt: Formatter):
    yield 'nil'


@ _traverse.register
def _(node: ast.While, fmt: Formatter):
    yield 'while'
    yield from _traverse(node.condition, fmt)
    yield 'do'
    if fmt.pretty:
        yield '\n'
    fmt.indent += 1
    yield from _traverse(node.block, fmt)
    fmt.indent -= 1
    if fmt.pretty:
        yield '  ' * fmt.indent
    yield 'end'


@ _traverse.register
def _(node: ast.Repeat, fmt: Formatter):
    yield 'repeat'
    if fmt.pretty:
        yield '\n'
    fmt.indent += 1
    yield from _traverse(node.block, fmt)
    fmt.indent -= 1
    yield 'until'
    yield from _traverse(node.condition, fmt)


@ _traverse.register
def _(node: ast.ForRange, fmt: Formatter):
    yield 'for'
    yield from _traverse(node.var, fmt)
    yield '='
    yield from _traverse(node.lb, fmt)
    yield ','
    yield from _traverse(node.ub, fmt)
    if node.step is not None:
        yield ','
        yield from _traverse(node.step, fmt)
    yield 'do'
    if fmt.pretty:
        yield '\n'
    fmt.indent += 1
    yield from _traverse(node.body, fmt)
    fmt.indent -= 1
    if fmt.pretty:
        yield '  ' * fmt.indent
    yield 'end'


@ _traverse.register
def _(node: ast.ForIn, fmt: Formatter):
    yield 'for'
    for i, v in enumerate(node.names):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)
    yield 'in'
    for i, v in enumerate(node.exps):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)
    yield 'do'
    if fmt.pretty:
        yield '\n'
    fmt.indent += 1
    yield from _traverse(node.body, fmt)
    fmt.indent -= 1
    if fmt.pretty:
        yield '  ' * fmt.indent
    yield 'end'


@ _traverse.register
def _(node: ast.Local, fmt: Formatter):
    yield 'local'
    for i, v in enumerate(node.targets):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)
    if node.values is not None:
        yield '='
        for i, v in enumerate(node.values):
            if i > 0:
                yield ','
            yield from _traverse(v, fmt)


@ _traverse.register
def _(node: ast.Func, fmt: Formatter):
    if (len(node.args) == 0 or (len(node.args) == 1 and type(node.args[0]) == ast.Ellipsis)) and not fmt.pretty and not fmt.no_load and node.oneline:
        fmt.indent += 1
        fmt2 = Formatter(fmt.indent + 1, double_quotes=not fmt.double_quotes, pretty=False, no_load=fmt.no_load)
        s = fmt2.format(node.body)
        yield 'load'
        yield fmt.escape(s)
        fmt.indent -= 1
    else:
        yield 'function'
        yield '('
        for i, v in enumerate(node.args):
            if i > 0:
                yield ','
            yield from _traverse(v, fmt)
        yield ')'
        if fmt.pretty:
            yield '\n'
        fmt.indent += 1
        yield from _traverse(node.body, fmt)
        fmt.indent -= 1
        if fmt.pretty:
            yield '  ' * fmt.indent
        yield 'end'


@ _traverse.register
def _(node: ast.Index, fmt: Formatter):
    require_parentheses = type(node.obj) is not ast.Name and \
        type(node.obj) is not ast.Index and \
        type(node.obj) is not ast.MethodCall and \
        type(node.obj) is not ast.Call
    if require_parentheses:
        yield '('
    yield from _traverse(node.obj, fmt)
    if require_parentheses:
        yield ')'
    if type(node.item) is ast.LiteralString:
        yield '.'
        yield node.item.value
    else:
        yield '['
        yield from _traverse(node.item, fmt)
        yield ']'


@ _traverse.register
def _(node: ast.Table, fmt: Formatter):
    yield '{'
    for i, f in enumerate(node.fields):
        if i > 0:
            yield ','
        yield from _traverse(f, fmt)
    yield '}'


@ _traverse.register
def _(node: ast.NamedField, fmt: Formatter):
    yield node.key
    yield '='
    yield from _traverse(node.value, fmt)


@ _traverse.register
def _(node: ast.ExpressionField, fmt: Formatter):
    yield '['
    yield from _traverse(node.key, fmt)
    yield ']='
    yield from _traverse(node.value, fmt)


@ _traverse.register
def _(node: ast.Field, fmt: Formatter):
    yield from _traverse(node.value, fmt)


@ _traverse.register
def _(node: ast.Call, fmt: Formatter):
    yield from _traverse(node.func, fmt)
    if len(node.args) == 1 and (type(node.args[0]) is ast.Table or type(node.args[0]) is ast.LiteralString):
        yield from _traverse(node.args[0], fmt)
    else:
        yield '('
        for i, v in enumerate(node.args):
            if i > 0:
                yield ','
            yield from _traverse(v, fmt)
        yield ')'


@ _traverse.register
def _(node: ast.MethodCall, fmt: Formatter):
    require_parentheses = type(node.value) is not ast.Name and \
        type(node.value) is not ast.Index and \
        type(node.value) is not ast.MethodCall and \
        type(node.value) is not ast.Call
    if require_parentheses:
        yield '('
    yield from _traverse(node.value, fmt)
    if require_parentheses:
        yield ')'
    yield ':'
    yield from _traverse(node.method, fmt)
    yield '('
    for i, v in enumerate(node.args):
        if i > 0:
            yield ','
        yield from _traverse(v, fmt)
    yield ')'


@ _traverse.register
def _(node: ast.If, fmt: Formatter):
    yield 'if'
    yield from _traverse(node.test, fmt)
    yield 'then'
    fmt.indent += 1
    if fmt.pretty:
        yield '\n'
    yield from _traverse(node.body, fmt)
    fmt.indent -= 1
    while node.orelse is not None and len(node.orelse.stats) == 1 and type(node.orelse.stats[0]) == ast.If:
        node = node.orelse.stats[0]
        if fmt.pretty:
            yield '  ' * fmt.indent
        yield 'elseif'
        yield from _traverse(node.test, fmt)
        yield 'then'
        fmt.indent += 1
        if fmt.pretty:
            yield '\n'
        yield from _traverse(node.body, fmt)
        fmt.indent -= 1
    if node.orelse is not None:
        if fmt.pretty:
            yield '  ' * fmt.indent
        yield 'else'
        if fmt.pretty:
            yield '\n'
        fmt.indent += 1
        yield from _traverse(node.orelse, fmt)
        fmt.indent -= 1
    if fmt.pretty:
        yield '  ' * fmt.indent
    yield 'end'


@ _traverse.register
def _(node: ast.Name, fmt: Formatter):
    yield node.id


@ _traverse.register
def _(node: ast.BinOp, fmt: Formatter):
    if node.op == '^':
        if node.left.precedence >= node.precedence:
            yield '('
        yield from _traverse(node.left, fmt)
        if node.left.precedence >= node.precedence:
            yield ')'
        yield node.op
        if node.right.precedence > node.precedence:
            yield '('
        yield from _traverse(node.right, fmt)
        if node.right.precedence > node.precedence:
            yield ')'
    else:
        if node.left.precedence > node.precedence:
            yield '('
        yield from _traverse(node.left, fmt)
        if node.left.precedence > node.precedence:
            yield ')'
        yield node.op
        if node.right.precedence >= node.precedence:
            yield '('
        yield from _traverse(node.right, fmt)
        if node.right.precedence >= node.precedence:
            yield ')'


@ _traverse.register
def _(node: ast.UnaryOp, fmt: Formatter):
    yield node.op
    if node.operand.precedence > node.precedence:
        yield '('
    yield from _traverse(node.operand, fmt)
    if node.operand.precedence > node.precedence:
        yield ')'


@ _traverse.register
def _(node: ast.Alt, fmt: Formatter):
    yield from _traverse(node.alts[0], fmt)
    if fmt.pretty and len(node.alts) > 0:
        for i, v in enumerate(node.alts[1:]):
            yield '--|'
            yield from _traverse(v, fmt)
            if i == len(node.alts) - 2:
                yield '\n'
                yield '  ' * fmt.indent


@ _traverse.register
def _(node: ast.Numeral, fmt: Formatter):
    # We treat numerals a bit differently, to see if they need spaces before, so
    # we yield them as Numerals, not strs
    if fmt.no_hex and node.hex and node.fractional == 0 and node.exponent == 0:
        yield ast.Numeral(node.whole)
    else:
        yield node


@ _traverse.register
def _(node: ast.Hint, fmt: Formatter):
    prev_double_quotes = fmt.double_quotes
    prev_no_hex = fmt.no_hex
    fmt.double_quotes = node.double_quotes
    fmt.no_hex = node.no_hex
    yield from _traverse(node.block, fmt)
    fmt.double_quotes = prev_double_quotes
    fmt.no_hex = prev_no_hex
