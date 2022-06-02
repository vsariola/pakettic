

from dataclasses import dataclass
from functools import singledispatch, singledispatchmethod
import typing
import re
from pakettic import ast


def format(node: ast.Node, pretty: bool = False) -> str:
    return Formatter(pretty=pretty).format(node)


_hexy = re.compile('[0-9a-fA-F]').search
_single_quote_translation = str.maketrans({"\n": r"\n",
                                           "\t": r"\t",
                                           "\\": r"\\",
                                           "'": r"\'"})
_double_quote_translation = str.maketrans({"\n": r"\n",
                                           "\t": r"\t",
                                           "\\": r"\\",
                                           "\"": r'\"'})


@dataclass
class Formatter:
    indent: int = 0
    double_quotes: bool = False
    pretty: bool = False
    no_hex: bool = False

    def format(self, node: ast.Node) -> str:
        tokens = self.__traverse(node)
        return ''.join(self.__addspaces(tokens))

    @property
    def __quote(self):
        return '"' if self.double_quotes else "'"

    def __escape(self, s: str):
        return f"{self.__quote}{s.translate(_double_quote_translation if self.double_quotes else _single_quote_translation)}{self.__quote}"

    @ singledispatchmethod
    def __traverse(self, node: ast.Node):
        # raise TypeError("_print encounted unknown ast.node")
        yield str(node)

    def __addspaces(self, tokens: typing.Iterable[str]):
        prevtoken = ' '
        for token in tokens:
            if len(token) == 0:
                continue
            if prevtoken[-1].isalpha() and (token[0].isalpha() or token[0].isdigit()) or (prevtoken[-1].isdigit() and bool(_hexy(token[0]))):
                yield ' '
            yield token
            prevtoken = token

    @ __traverse.register
    def _(self, node: ast.Block):
        for n in node.stats:
            if self.pretty:
                yield '  ' * self.indent
            yield from self.__traverse(n)
            if self.pretty:
                yield '\n'

    @ __traverse.register
    def _(self, node: ast.Perm):
        if self.pretty:
            if node.allow_reorder:
                yield '--{'
            else:
                yield '--{!'
            yield '\n'
            yield '  ' * self.indent
        for i, n in enumerate(node.stats):
            if self.pretty and i > 0:
                yield '  ' * self.indent
            yield from self.__traverse(n)
            if self.pretty and i < len(node.stats) - 1:
                yield '\n'
        if self.pretty:
            yield '\n'
            yield '  ' * self.indent
            yield '--}'

    @ __traverse.register
    def _(self, node: ast.Do):
        yield 'do'
        if self.pretty:
            yield '\n'
        self.indent += 1
        yield from self.__traverse(node.body)
        self.indent -= 1
        if self.pretty:
            yield '  ' * self.indent
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.Assign):
        for i, v in enumerate(node.targets):
            if i > 0:
                yield ','
            yield from self.__traverse(v)
        yield '='
        for i, v in enumerate(node.values):
            if i > 0:
                yield ','
            yield from self.__traverse(v)

    @ __traverse.register
    def _(self, node: ast.Label):
        yield '::'
        yield node.name
        yield '::'

    @ __traverse.register
    def _(self, node: ast.Break):
        yield 'break'

    @ __traverse.register
    def _(self, node: ast.LiteralString):
        yield self.__escape(node.value)

    @ __traverse.register
    def _(self, node: ast.Goto):
        yield 'goto'
        yield node.target

    @ __traverse.register
    def _(self, node: ast.Boolean):
        yield 'true' if node.value else 'false'

    @ __traverse.register
    def _(self, node: ast.Ellipsis):
        yield '...'

    @ __traverse.register
    def _(self, node: ast.Nil):
        yield 'nil'

    @ __traverse.register
    def _(self, node: ast.While):
        yield 'while'
        yield from self.__traverse(node.condition)
        yield 'do'
        if self.pretty:
            yield '\n'
        self.indent += 1
        yield from self.__traverse(node.block)
        self.indent -= 1
        if self.pretty:
            yield '  ' * self.indent
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.Repeat):
        yield 'repeat'
        if self.pretty:
            yield '\n'
        self.indent += 1
        yield from self.__traverse(node.block)
        self.indent -= 1
        yield 'until'
        yield from self.__traverse(node.condition)

    @ __traverse.register
    def _(self, node: ast.ForRange):
        yield 'for'
        yield from self.__traverse(node.var)
        yield '='
        yield from self.__traverse(node.lb)
        yield ','
        yield from self.__traverse(node.ub)
        if node.step is not None:
            yield ','
            yield from self.__traverse(node.step)
        yield 'do'
        if self.pretty:
            yield '\n'
        self.indent += 1
        yield from self.__traverse(node.body)
        self.indent -= 1
        if self.pretty:
            yield '  ' * self.indent
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.ForIn):
        yield 'for'
        for i, v in enumerate(node.names):
            if i > 0:
                yield ','
            yield from self.__traverse(v)
        yield 'in'
        for i, v in enumerate(node.exps):
            if i > 0:
                yield ','
            yield from self.__traverse(v)
        yield 'do'
        if self.pretty:
            yield '\n'
        self.indent += 1
        yield from self.__traverse(node.body)
        self.indent -= 1
        if self.pretty:
            yield '  ' * self.indent
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.Local):
        pass

    @ __traverse.register
    def _(self, node: ast.Func):
        if len(node.args) == 0 and not self.pretty and node.oneline:
            self.indent += 1
            fmt = Formatter(self.indent + 1, double_quotes=not self.double_quotes, pretty=False)
            s = fmt.format(node.body)
            yield 'load'
            yield self.__escape(s)
            self.indent -= 1
        else:
            yield 'function'
            yield '('
            for i, v in enumerate(node.args):
                if i > 0:
                    yield ','
                yield from self.__traverse(v)
            yield ')'
            if self.pretty:
                yield '\n'
            self.indent += 1
            yield from self.__traverse(node.body)
            self.indent -= 1
            if self.pretty:
                yield '  ' * self.indent
            yield 'end'

    @ __traverse.register
    def _(self, node: ast.Index):
        if type(node.obj) is not ast.Name:
            yield '('
        yield from self.__traverse(node.obj)
        if type(node.obj) is not ast.Name:
            yield ')'
        if type(node.item) is ast.LiteralString:
            yield '.'
            yield node.item.value
        else:
            yield '['
            yield from self.__traverse(node.item)
            yield ']'

    @ __traverse.register
    def _(self, node: ast.Table):
        yield '{'
        for i, f in enumerate(node.fields):
            if i > 0:
                yield ','
            yield from self.__traverse(f)
        yield '}'

    @ __traverse.register
    def _(self, node: ast.Field):
        if node.key is not None:
            if type(node.key) is ast.LiteralString:
                yield node.key.value
                yield '='
            else:
                yield '['
                yield from self.__traverse(node.key)
                yield ']'
                yield '='
        yield from self.__traverse(node.value)

    @ __traverse.register
    def _(self, node: ast.Call):
        yield from self.__traverse(node.func)
        if len(node.args) == 1 and (type(node.args[0]) is ast.Table or type(node.args[0]) is ast.LiteralString):
            yield from self.__traverse(node.args[0])
        else:
            yield '('
            for i, v in enumerate(node.args):
                if i > 0:
                    yield ','
                yield from self.__traverse(v)
            yield ')'

    @ __traverse.register
    def _(self, node: ast.MethodCall):
        pass  # TODO

    @ __traverse.register
    def _(self, node: ast.If):
        yield 'if'
        yield from self.__traverse(node.test)
        yield 'then'
        self.indent += 1
        if self.pretty:
            yield '\n'
        yield from self.__traverse(node.body)
        self.indent -= 1
        while node.orelse is not None and len(node.orelse.stats) == 1 and type(node.orelse.stats[0]) == ast.If:
            node = node.orelse.stats[0]
            if self.pretty:
                yield '  ' * self.indent
            yield 'elseif'
            yield from self.__traverse(node.test)
            yield 'then'
            self.indent += 1
            if self.pretty:
                yield '\n'
            yield from self.__traverse(node.body)
            self.indent -= 1
        if node.orelse is not None:
            if self.pretty:
                yield '  ' * self.indent
            yield 'else'
            if self.pretty:
                yield '\n'
            self.indent += 1
            yield from self.__traverse(node.orelse)
            self.indent -= 1
        if self.pretty:
            yield '  ' * self.indent
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.Name):
        yield node.id

    @ __traverse.register
    def _(self, node: ast.BinOp):
        if node.op == '^':
            if node.left.precedence >= node.precedence:
                yield '('
            yield from self.__traverse(node.left)
            if node.left.precedence >= node.precedence:
                yield ')'
            yield node.op
            if node.right.precedence > node.precedence:
                yield '('
            yield from self.__traverse(node.right)
            if node.right.precedence > node.precedence:
                yield ')'
        else:
            if node.left.precedence > node.precedence:
                yield '('
            yield from self.__traverse(node.left)
            if node.left.precedence > node.precedence:
                yield ')'
            yield node.op
            if node.right.precedence >= node.precedence:
                yield '('
            yield from self.__traverse(node.right)
            if node.right.precedence >= node.precedence:
                yield ')'

    @ __traverse.register
    def _(self, node: ast.UnaryOp):
        yield node.op
        if node.operand.precedence > node.precedence:
            yield '('
        yield from self.__traverse(node.operand)
        if node.operand.precedence > node.precedence:
            yield ')'

    @ __traverse.register
    def _(self, node: ast.Alt):
        yield from self.__traverse(node.alts[0])
        if self.pretty and len(node.alts) > 0:
            for i, v in enumerate(node.alts[1:]):
                yield '--|'
                yield from self.__traverse(v)
                if i == len(node.alts) - 2:
                    yield '\n'
                    yield '  ' * self.indent

    @ __traverse.register
    def _(self, node: ast.Numeral):
        if self.no_hex and node.hex and node.fractional == 0 and node.exponent == 0:
            yield str(node.whole)
        else:
            yield str(node)

    @ __traverse.register
    def _(self, node: ast.Hint):
        prev_double_quotes = self.double_quotes
        prev_no_hex = self.no_hex
        self.double_quotes = node.double_quotes
        self.no_hex = node.no_hex
        yield from self.__traverse(node.block)
        self.double_quotes = prev_double_quotes
        self.no_hex = prev_no_hex
