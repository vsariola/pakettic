from dataclasses import dataclass
from typing import Union, Optional

Expression = Union['Nil', 'Boolean']


class Node:
    @property
    def precedence(self):
        return 0


@dataclass
class Block(Node):
    stats: list


@dataclass
class DoBlock(Node):
    stats: list


@dataclass
class Assign(Node):
    targets: list
    values: list


@dataclass
class Label(Node):
    name: str


@dataclass
class Break(Node):
    pass


@dataclass
class LiteralString(Node):
    value: str


@dataclass
class Goto(Node):
    target: str


@dataclass
class Boolean(Node):
    value: bool


@dataclass
class Ellipsis(Node):
    pass


@dataclass
class Nil(Node):
    pass


@dataclass
class While(Node):
    condition: Expression
    block: Block


@dataclass
class Repeat(Node):
    condition: Expression
    block: Block


@dataclass
class ForRange(Node):
    var: str
    lb: Expression
    ub: Expression
    step: Optional[Expression]  # can be empty
    body: Block


@dataclass
class ForIn(Node):
    names: list
    exps: list
    body: list


@dataclass
class Local(Node):
    targets: list
    values: list


@dataclass
class Func(Node):
    args: list
    body: list


@dataclass
class Index(Node):
    obj: Expression
    item: Expression


@dataclass
class Table(Node):
    fields: list[Expression]


@dataclass
class Field(Node):
    value: Expression
    key: Expression = None


@dataclass
class Call(Node):
    func: Expression
    args: list[Expression]


@dataclass
class MethodCall(Node):
    value: Expression
    method: str
    args: list[Expression]


@dataclass
class If(Node):
    test: Expression
    body: list
    orelse: list


@dataclass
class Name(Node):
    id: str


@dataclass
class BinOp(Node):
    left: Expression
    op: str
    right: Expression

    @property
    def precedence(self):
        return _precedence[self.op]


_precedence = \
    dict.fromkeys(['^'], 2) | \
    dict.fromkeys(['*', '/', '//', '%'], 3) | \
    dict.fromkeys(['+', '-'], 4) | \
    dict.fromkeys(['..'], 5) | \
    dict.fromkeys(['<<', '>>'], 6) | \
    dict.fromkeys(['&'], 7) | \
    dict.fromkeys(['~'], 8) | \
    dict.fromkeys(['|'], 9) | \
    dict.fromkeys(['<', '>', '<=', '>=', '~=', '=='], 10) | \
    dict.fromkeys(['and'], 11) | \
    dict.fromkeys(['or'], 12)


@dataclass
class UnaryOp(Node):
    op: str
    operand: Expression

    @property
    def precedence(self):
        return 1


@dataclass(init=False)
class Numeral(Node):
    whole: int
    fractional: int
    exponent: int
    hex: bool

    def __init__(self, whole=0, fractional=0, exponent=0, hex=False):
        self.whole = whole
        self.fractional = fractional
        self.exponent = exponent
        self.hex = hex

    def __repr__(self):
        if self.whole == 0 and self.fractional > 0:
            return f"{'.' + '%x' % self.fractional if self.fractional != 0 else ''}{'p' + self.exponent if self.exponent != 0 else ''}" if self.hex \
                else f"{'.' + str(self.fractional)[::-1] if self.fractional != 0 else ''}{'e' + str(self.exponent) if self.exponent != 0 else ''}"
        else:
            return f"{'%x' % self.whole}{'.' + '%x' % self.fractional if self.fractional != 0 else ''}{'p' + self.exponent if self.exponent != 0 else ''}" if self.hex \
                else f"{self.whole}{'.' + str(self.fractional)[::-1] if self.fractional != 0 else ''}{'e' + str(self.exponent) if self.exponent != 0 else ''}"
