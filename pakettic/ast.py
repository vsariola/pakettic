from dataclasses import dataclass
from typing import Optional


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
    stats: list[Node]


@dataclass
class Return(Node):
    """Represents a return statement in the abstract syntax tree"""
    exps: list[Node]


@dataclass
class Do(Node):
    """Represents a 'do...end' in the abstract syntax tree"""
    block: Block


@dataclass
class Assign(Node):
    """Represents an assignment in the abstract syntax tree"""
    targets: list[Node]
    values: list[Node]


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
    condition: Node
    block: Block


@dataclass
class Repeat(Node):
    """Represents a repeat-until loop in the abstract syntax tree"""
    condition: Node
    block: Block


@dataclass
class ForRange(Node):
    """Represents a ranged for loop in the abstract syntax tree"""
    var: Node
    lb: Node
    ub: Node
    step: Optional[Node]  # can be empty
    body: Block


@dataclass
class ForIn(Node):
    """Represents a for-in loop in the abstract syntax tree"""
    names: list[Name]
    exps: list[Node]
    body: Block


@dataclass
class Local(Node):
    """Represents a local assignment in the abstract syntax tree"""
    targets: list[Name]
    values: list[Node]


@dataclass
class Func(Node):
    """Represents a function definition the abstract syntax tree"""
    args: list[Name]
    body: Block
    oneline: bool = True


@dataclass
class Index(Node):
    """Represents an indexing (obj[item]) the abstract syntax tree"""
    obj: Node
    item: Node


@dataclass
class Table(Node):
    """Represents a table definition the abstract syntax tree"""
    fields: list[Node]


@dataclass
class Field(Node):
    """Represents a field in the inside a table definition"""
    value: Node
    key: Node = None


@dataclass
class Call(Node):
    """Represents a call in the abstract syntax tree"""
    func: Node
    args: list[Node]


@dataclass
class MethodCall(Node):
    """Represents a method call ('obj:method(args)') in the abstract syntax tree"""
    value: Node
    method: str
    args: list[Node]


@dataclass
class If(Node):
    """Represents an if statement in the abstract syntax tree"""
    test: Node
    body: Block
    orelse: Block


@dataclass
class BinOp(Node):
    """Represents a binary operator in the abstract syntax tree"""
    left: Node
    op: str
    right: Node

    @property
    def precedence(self):
        return _precedence[self.op]


@dataclass
class Hint(Node):
    """A node containing hints for printing. Does not reflect actual code."""
    block: Block
    no_hex: bool = True
    double_quotes: bool = False


_precedence = \
    dict.fromkeys(['--|'], 1) | \
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
    operand: Node

    @property
    def precedence(self):
        return 2


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
            return f"{'0x.' + ('%x' % self.fractional)[::-1]}{'p' + str(self.exponent) if self.exponent != 0 else ''}" if self.hex \
                else f"{'.' + str(self.fractional)[::-1]}{'e' + str(self.exponent) if self.exponent != 0 else ''}"
        else:
            return f"0x{'%x' % self.whole}{'.' + ('%x' % self.fractional)[::-1] if self.fractional != 0 else ''}{'p' + str(self.exponent) if self.exponent != 0 else ''}" if self.hex \
                else f"{self.whole}{'.' + str(self.fractional)[::-1] if self.fractional != 0 else ''}{'e' + str(self.exponent) if self.exponent != 0 else ''}"


@dataclass
class Alt(Node):
    """
    Represents a list of alternative expressions in the abstract syntax tree.
    Not part of standard LUA, but created using pakettic magic comments.
    Only the first alternative is the one currently active.
    """
    alts: list[Node]

    @property
    def precedence(self):
        return self.alts[0].precedence


@dataclass
class Perm(Node):
    """
    Represents a list of statements that can be freely reordered in the abstract syntax tree.
    Not part of standard LUA, but created using pakettic magic comments.
    """
    stats: list[Node]
    allow_reorder: bool = True
