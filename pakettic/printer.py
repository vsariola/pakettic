

from dataclasses import dataclass
from functools import singledispatch, singledispatchmethod
import typing
import re
from pakettic import ast


def format(node: ast.Node) -> str:
    return Formatter().format(node)


    # to check whether any in ranges (->MatchObject) / all outside ranges (->None)
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
    indent: int = 0  # TODO: get rid of this?
    double_quotes: bool = False

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
            if token != 'if' or prevtoken != 'else':
                if prevtoken[-1].isalpha() and (token[0].isalpha() or token[0].isdigit()) or (prevtoken[-1].isdigit() and bool(_hexy(token[0]))):
                    yield ' '
            yield token
            prevtoken = token

    @ __traverse.register
    def _(self, node: ast.Block):
        for n in node.stats:
            # yield ' ' * self.indent
            yield from self.__traverse(n)
            # yield '\n'

    @ __traverse.register
    def _(self, node: ast.Do):
        yield 'do'
        self.indent += 1
        yield from self.__traverse(node.body)
        self.indent -= 1
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
        self.indent += 1
        yield from self.__traverse(node.block)
        self.indent -= 1
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.Repeat):
        yield 'repeat'
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
        self.indent += 1
        yield from self.__traverse(node.body)
        self.indent -= 1
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
        self.indent += 1
        yield from self.__traverse(node.body)
        self.indent -= 1
        yield 'end'

    @ __traverse.register
    def _(self, node: ast.Local):
        pass

    @ __traverse.register
    def _(self, node: ast.Func):
        if len(node.args) == 0:
            self.indent += 1
            fmt = Formatter(self.indent + 1, double_quotes=not self.double_quotes)
            str = fmt.format(node.body)
            yield 'load'
            yield self.__escape(str)
            self.indent -= 1
        else:
            yield 'function'
            yield '('
            for i, v in enumerate(node.args):
                if i > 0:
                    yield ','
                yield from str(v)
            yield ')'
            self.indent += 1
            yield from self.__traverse(node.body)
            self.indent -= 1
            yield 'end'

    @ __traverse.register
    def _(self, node: ast.Index):
        yield from self.__traverse(node.obj)
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
        yield from self.__traverse(node.body)
        if node.orelse is not None:
            yield 'else'
            yield from self.__traverse(node.orelse)
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

    @ __traverse.register
    def _(self, node: ast.Numeral):
        yield str(node)
