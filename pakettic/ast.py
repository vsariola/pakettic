from dataclasses import dataclass
from typing import Union, Optional

Expression = Union['Nil', 'Boolean']


class Node:
    """Represents a node in the abstract syntax tree"""
    @property
    def precedence(self):
        return 0


@dataclass
class Name(Node):
    """Represents an variable identifier in the abstract syntax tree"""
    id: str


@dataclass
class Block(Node):
    """Represents list of statements in the abstract syntax tree"""
    stats: list


@dataclass
class Do(Node):
    """Represents a 'do...end' in the abstract syntax tree"""
    block: Block


@dataclass
class Assign(Node):
    """Represents an assignment in the abstract syntax tree"""
    targets: list[Name]
    values: list


@dataclass
class Label(Node):
    """Represents a '::label::' in the abstract syntax tree"""
    name: str


@dataclass
class Break(Node):
    """Represents a 'break' in the abstract syntax tree"""
    pass


@dataclass
class LiteralString(Node):
    """Represents a string literal in the abstract syntax tree"""
    value: str


@dataclass
class Goto(Node):
    """Represents a 'goto target' in the abstract syntax tree"""
    target: str


@dataclass
class Boolean(Node):
    """Represents a boolean literal in the abstract syntax tree"""
    value: bool


@dataclass
class Ellipsis(Node):
    """Represents an ellipsis (...) in the abstract syntax tree"""
    pass


@dataclass
class Nil(Node):
    """Represents a nil literal the abstract syntax tree"""
    pass


@dataclass
class While(Node):
    """Represents a while loop in the abstract syntax tree"""
    condition: Expression
    block: Block


@dataclass
class Repeat(Node):
    """Represents a repeat-until loop in the abstract syntax tree"""
    condition: Expression
    block: Block


@dataclass
class ForRange(Node):
    """Represents a ranged for loop in the abstract syntax tree"""
    var: str
    lb: Expression
    ub: Expression
    step: Optional[Expression]  # can be empty
    body: Block


@dataclass
class ForIn(Node):
    """Represents a for-in loop in the abstract syntax tree"""
    names: list[Name]
    exps: list
    body: Block


@dataclass
class Local(Node):
    """Represents a local assignment in the abstract syntax tree"""
    targets: list[Name]
    values: list


@dataclass
class Func(Node):
    """Represents a function definition the abstract syntax tree"""
    args: list
    body: Block


@dataclass
class Index(Node):
    """Represents an indexing (obj[item]) the abstract syntax tree"""
    obj: Expression
    item: Expression


@dataclass
class Table(Node):
    """Represents a table definition the abstract syntax tree"""
    fields: list[Expression]


@dataclass
class Field(Node):
    """Represents a field in the inside a table definition"""
    value: Expression
    key: Expression = None


@dataclass
class Call(Node):
    """Represents a call in the abstract syntax tree"""
    func: Expression
    args: list[Expression]


@dataclass
class MethodCall(Node):
    """Represents a method call ('obj:method(args)') in the abstract syntax tree"""
    value: Expression
    method: str
    args: list[Expression]


@dataclass
class If(Node):
    """Represents an if statement in the abstract syntax tree"""
    test: Expression
    body: Block
    orelse: Block


@dataclass
class BinOp(Node):
    """Represents a binary operator in the abstract syntax tree"""
    left: Expression
    op: str
    right: Expression

    @property
    def precedence(self):
        return _precedence[self.op]


_precedence = \
    dict.fromkeys(['---'], 1) | \
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
    """Represents an unary operator in the abstract syntax tree"""
    op: str
    operand: Expression

    @property
    def precedence(self):
        return 1


@dataclass(init=False)
class Numeral(Node):
    """Represents a numeral literal in the abstract syntax tree"""
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


@dataclass
class Alt(Node):
    """
    Represents a list of alternative expressions in the abstract syntax tree.
    Not part of standard LUA, but created using pakettic magic comments.
    Only the first alternative is the one currently active.
    """
    alts: list

    @property
    def precedence(self):
        return self.alts[0].precedence


@dataclass
class Perm(Node):
    """
    Represents a list of statements that can be freely reordered in the abstract syntax tree.
    Not part of standard LUA, but created using pakettic magic comments.
    """
    stats: list
