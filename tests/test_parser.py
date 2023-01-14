import unittest
from pakettic import parser
from pakettic import ast
from pakettic.ast import *


class TestStringLiterals(unittest.TestCase):
    def test_short_string_literals(self):
        short_string_literals = [
            ('"test123"', "test123"),
            ("'test123'", "test123"),
            ("'test123\\n'", "test123\n"),
            ("'test123\\t'", "test123\t"),
            ("'test123\\''", "test123'"),
        ]
        for a, b in short_string_literals:
            with self.subTest(parsed=a, expected=b):
                got = parser.LiteralString.parse_string(a, parse_all=True)[0].value
                self.assertEqual(got, b)

    def test_long_string_literals(self):
        long_string_literals = [
            ('[[test123]]', "test123"),
            ('[===[test123]===]', "test123"),
            ('[==[\ntest123]==]', "test123"),
            ('[==[\n[[test123]]]==]', "[[test123]]"),
            ('[[\ntest\n123]]', "test\n123"),
        ]
        for a, b in long_string_literals:
            with self.subTest(parsed=a, expected=b):
                got = parser.LiteralString.parse_string(a, parse_all=True)[0].value
                self.assertEqual(got, b)

    def test_bad_string_literals(self):
        bad_string_literals = [
            '[=[\ntest123]=====]',
            '"test123',
            '"test123\'',
        ]
        for a in bad_string_literals:
            with self.subTest(parsed=a):
                with self.assertRaises(Exception):
                    parser.LiteralString.parse_string(a, parse_all=True)


class TestNumerals(unittest.TestCase):
    def test_ints(self):
        ints = [
            ('123', Numeral(123, 0, 0)),
            ('50000000', Numeral(50000000, 0, 0)),
            ('50', Numeral(50, 0, 0)),
        ]
        for a, b in ints:
            with self.subTest(parsed=a, expected=b):
                got = parser.Numeral.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, b)

    def test_fractionals(self):
        fractionals = [
            ('0.123', Numeral(0, 321, 0)),
            ('.6192', Numeral(0, 2916, 0)),
        ]
        for a, b in fractionals:
            with self.subTest(parsed=a, expected=b):
                got = parser.Numeral.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, b)

    def test_bad_numerals(self):
        bad_numerals = [
            '. 123',
            '1 .0',
        ]
        for a in bad_numerals:
            with self.subTest(parsed=a):
                with self.assertRaises(Exception):
                    parser.Numeral.parse_string(a, parse_all=True)

    def test_exponents(self):
        exponents = [
            ('1e5', Numeral(1, 0, 5)),
            ('1.5e10', Numeral(1, 5, 10)),
        ]
        for a, b in exponents:
            with self.subTest(parsed=a, expected=b):
                got = parser.Numeral.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, b)

    def test_hex_numerals(self):
        hex_numerals = [
            ('0xff', Numeral(255, hex=True)),
            ('0Xff', Numeral(255, hex=True)),
            ('0XFF', Numeral(255, hex=True)),
            ('0xFF.A', Numeral(255, 10, hex=True)),
            ('0xFF.Ap5', Numeral(255, 10, 5, hex=True)),
        ]
        for a, b in hex_numerals:
            with self.subTest(parsed=a, expected=b):
                got = parser.Numeral.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, b)


class TestNames(unittest.TestCase):
    def test_valid_names(self):
        valid_names = [
            'foo', 'Foo', 'Foo_', '_Foo', 'iff', 'repeatuntil'
        ]
        for a in valid_names:
            with self.subTest(parsed=a):
                try:
                    parser.Name.parse_string(a, parse_all=True)
                except:
                    self.fail(f"{a} should have been a valid name")

    def test_invalid_names(self):
        invalid_names = [
            '1foo', '#Foo', '@foo',
            'and', 'break', 'do', 'break', 'else', 'elseif',
            'end', 'false', 'for', 'function', 'if',
            'in', 'local', 'nil', 'not', 'or',
            'repeat', 'return', 'then', 'true', 'until', 'while'
        ]
        for a in invalid_names:
            with self.subTest(parsed=a):
                with self.assertRaises(Exception):
                    parser.Name.parse_string(a, parse_all=True)


class TestAssignments(unittest.TestCase):
    def test_valid_assignments(self):
        valid_assignments = [
            ('x=5', ([Name('x')], [Numeral(5)])),
            ('x,y=1,2', ([Name('x'), Name('y')], [Numeral(1), Numeral(2)])),
            # LUA does not enforce left and right having same number of items
            # y becomes nil here:
            ('x,y=1', ([Name('x'), Name('y')], [Numeral(1)])),
            ('x,y=1,2,3', ([Name('x'), Name('y')], [Numeral(1), Numeral(2), Numeral(3)])),
            ('x=nil', ([Name('x')], [Nil()])),
            ('x=true', ([Name('x')], [Boolean(True)])),
            ('x=false', ([Name('x')], [Boolean(False)])),
        ]
        for a, b in valid_assignments:
            with self.subTest(parsed=a, expected=b):
                got = parser.chunk.parse_string(a, parse_all=True)[0]
                expected = Block([Assign(b[0], b[1])])
                self.assertEqual(got, expected)

    def test_invalid_assignments(self):
        invalid_assignments = [
            '1=x',
            'x=if',
            'y=',
        ]
        for a in invalid_assignments:
            with self.subTest(parsed=a):
                with self.assertRaises(Exception):
                    parser.chunk.parse_string(a, parse_all=True)


class TestFlowControl(unittest.TestCase):
    def test_valid_labels(self):
        valid_labels = [
            ('::foo::', 'foo'),
            ('::Foo::', 'Foo'),
            ('::Foo_::', 'Foo_'),
            ('::_Foo::', '_Foo'),
            ('::iff::', 'iff'),
            ('::repeatuntil::', 'repeatuntil'),
        ]
        for a, b in valid_labels:
            with self.subTest(parsed=a, expected=b):
                got = parser.chunk.parse_string(a, parse_all=True)[0]
                expected = Block([Label(b)])
                self.assertEqual(got, expected)

    def test_invalid_labels(self):
        invalid_labels = [
            '::foo:',
            '::if::',
            '::1::',
        ]
        for a in invalid_labels:
            with self.subTest(parsed=a):
                with self.assertRaises(Exception):
                    parser.chunk.parse_string(a, parse_all=True)

    def test_break(self):
        got = parser.parse_string('break')
        expected = Block([Break()])
        self.assertEqual(got, expected)

    def test_return_no_value(self):
        got = parser.parse_string('return')
        expected = Block([Return(exps=[])])
        self.assertEqual(got, expected)

    def test_return_value(self):
        got = parser.parse_string('return 42')
        expected = Block([Return(exps=[Numeral(42)])])
        self.assertEqual(got, expected)

    def test_return_multiple_values(self):
        got = parser.parse_string('return 1,2,3')
        expected = Block([Return(exps=[Numeral(1), Numeral(2), Numeral(3)])])
        self.assertEqual(got, expected)

    def test_return_always_last(self):
        with self.assertRaises(Exception):
            parser.parse_string('return\n::foo::')

    def test_single_goto(self):
        got = parser.parse_string('goto test_label')
        expected = Block([Goto('test_label')])
        self.assertEqual(got, expected)

    def test_multiple_gotos(self):
        got = parser.parse_string('goto foo;goto bar')
        expected = Block([Goto('foo'), Goto('bar')])
        self.assertEqual(got, expected)

    def test_do_block(self):
        got = parser.parse_string('do break end')
        expected = Block([Do(Block([Break()]))])
        self.assertEqual(got, expected)

    def test_while(self):
        got = parser.parse_string('while true do break end')
        expected = Block([While(Boolean(True), Block([Break()]))])
        self.assertEqual(got, expected)

    def test_repeat(self):
        got = parser.parse_string('repeat break until true')
        expected = Block([Repeat(Boolean(True), Block([Break()]))])
        self.assertEqual(got, expected)

    def test_ranged_for_loop(self):
        got = parser.parse_string('for i = 0,5 do break end')
        expected = Block([
            ForRange(
                var=Name('i'),
                lb=Numeral(0),
                ub=Numeral(5),
                step=None,
                body=Block([Break()])
            ),
        ])
        self.assertEqual(got, expected)

    def test_for_in_loop(self):
        cases = [
            ('for k in a do end', ([Name('k')], [Name('a')], [])),
            ('for k,v in a,v do end', ([Name('k'), Name('v')], [Name('a'), Name('v')], [])),
            ('for k,v in a do end', ([Name('k'), Name('v')], [Name('a')], [])),
        ]
        for a, b in cases:
            with self.subTest(parsed=a, expected=b):
                got = parser.parse_string(a)
                expected = Block([
                    ForIn(
                        names=b[0],
                        exps=b[1],
                        body=Block(b[2])
                    ),
                ])
                self.assertEqual(got, expected)


class TestBranching(unittest.TestCase):
    def test_if(self):
        got = parser.parse_string('if true then end')
        expected = Block([If(test=Boolean(True), body=Block([]), orelse=None)])
        self.assertEqual(got, expected)

    def test_else(self):
        got = parser.parse_string('if true then else break end')
        expected = Block([If(test=Boolean(True), body=Block([]), orelse=Block([Break()]))])
        self.assertEqual(got, expected)

    def test_elseif(self):
        got = parser.parse_string('if true then elseif true then else break end')
        expected = Block([
            If(
                test=Boolean(True),
                body=Block([]),
                orelse=Block([
                    If(test=Boolean(True), body=Block([]), orelse=Block([Break()]))
                ])
            )
        ])
        self.assertEqual(got, expected)


class TestMagicComments(unittest.TestCase):
    def test_reorderings(self):
        got = parser.parse_string('--{\n::foo::\n::bar::\n--}')
        expected = Block([Perm([Label("foo"), Label("bar")], allow_reorder=True)])
        self.assertEqual(got, expected)

    def test_disabled_reordering(self):
        got = parser.parse_string('--{!\n::foo::\n::bar::\n--}')
        expected = Block([Perm([Label("foo"), Label("bar")], allow_reorder=False)])
        self.assertEqual(got, expected)

    def test_alternative_expressions(self):
        got = parser.parse_string('x = 1 --| 2')
        expected = Block([Assign([Name('x')], [Alt([Numeral(1), Numeral(2)])])])
        self.assertEqual(got, expected)


class TestComments(unittest.TestCase):
    def test_single_line_comments(self):
        cases = [
            ('goto --comment\ntest_label', [Goto('test_label')]),
            ('goto foo--comment\n--comment\ngoto bar', [Goto('foo'), Goto('bar')]),
        ]
        for a, b in cases:
            expected = Block(b)
            with self.subTest(parsed=a, expected=expected):
                got = parser.parse_string(a)
                self.assertEqual(got, expected)

    def test_multiline_comments(self):
        cases = [
            ('--', []),
            ('goto --[[goto foo\ngoto bar\n--]]\ntest_label', [Goto('test_label')]),
            ('goto --[=====[goto foo\ngoto bar\n--]=====]\ntest_label', [Goto('test_label')]),
            ('goto --[=====[\n\ngoto foo\ngoto bar\n--]=====]\ntest_label', [Goto('test_label')]),
        ]
        for a, b in cases:
            expected = Block(b)
            with self.subTest(parsed=a, expected=expected):
                got = parser.parse_string(a)
                self.assertEqual(got, expected)

    def test_invalid_comments(self):
        invalid_comments = [
            'goto --[==[goto foo\ngoto bar\n--]=======]\ntest_label',
            '-',
            '//'
        ]
        for a in invalid_comments:
            with self.subTest(parsed=a):
                with self.assertRaises(Exception):
                    parser.chunk.parse_string(a, parse_all=True)


class TestFunction(unittest.TestCase):
    def test_function(self):
        got = parser.parse_string('f=function(x) end')
        expected = Block([
            Assign([Name('f')], [Func(args=[Name('x')], body=Block([]))])
        ])
        self.assertEqual(got, expected)

    def test_return(self):
        got = parser.parse_string('return 0')
        expected = Block([Return([Numeral(0)])])
        self.assertEqual(got, expected)


class TestCall(unittest.TestCase):
    def test_call(self):
        got = parser.parse_string('debug()')
        expected = Block([Call(func=Name("debug"), args=[])])
        self.assertEqual(got, expected)


class TestBinaryOperators(unittest.TestCase):
    def test_add(self):
        got = parser.parse_string('x = 1 + 2')
        expected = Block([
            Assign(
                [Name('x')],
                [BinOp(left=Numeral(1), op="+", right=Numeral(2))]
            )
        ])
        self.assertEqual(got, expected)

    def test_multiadd(self):
        got = parser.parse_string('x = 1 + 2 + 3')
        expected = Block([
            Assign(
                [Name('x')],
                [BinOp(left=BinOp(left=Numeral(1), op="+", right=Numeral(2)), op='+', right=Numeral(3))]
            )
        ])
        self.assertEqual(got, expected)

    def test_precedence(self):
        got = parser.parse_string('x = 6+1*2')
        expected = Block([
            Assign(
                [Name('x')],
                [BinOp(left=Numeral(6), op="+", right=BinOp(left=Numeral(1), op="*", right=Numeral(2)))]
            )
        ])
        self.assertEqual(got, expected)


class TestUnaryOperators(unittest.TestCase):
    def test_minus(self):
        got = parser.parse_string('x = -1')
        expected = Block([
            Assign([Name('x')], [UnaryOp(op="-", operand=Numeral(1))])
        ])
        self.assertEqual(got, expected)

    def test_association(self):
        cases = [
            ('-#a', UnaryOp(op='-', operand=UnaryOp(op="#", operand=Name("a")))),
            ('-1^2', UnaryOp(op='-', operand=BinOp(left=Numeral(1), op="^", right=Numeral(2)))),
            ('(-1)^2', BinOp(left=UnaryOp(op='-', operand=Numeral(1)), op="^", right=Numeral(2))),
        ]
        for a, expected in cases:
            with self.subTest(parsed=a, expected=expected):
                got = parser.exp.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, expected)

    def test_multiadd(self):
        got = parser.parse_string('x = 1 + 2 + 3')
        expected = Block([Assign([Name('x')], [BinOp(BinOp(Numeral(1), "+", Numeral(2)), '+', Numeral(3))])])
        self.assertEqual(got, expected)


class TestLocals(unittest.TestCase):
    def test_local_vars(self):
        got = parser.parse_string('local x = 5')
        expected = Block([Local(targets=[Name('x')], values=[Numeral(5)])])
        self.assertEqual(got, expected)

    def test_local_function(self):
        got = parser.parse_string('local function f(x) end')
        expected = Block([
            Local([Name('f')], [Func(args=[Name('x')], body=Block([]))])
        ])
        self.assertEqual(got, expected)


class TestVarPostfix(unittest.TestCase):
    def test_arrays(self):
        cases = [
            ('a[5]', Index(Name('a'), Numeral(5))),
            ('a[5][i]', Index(Index(Name('a'), Numeral(5)), Name('i'))),
            ('a[5].x', Index(Index(Name('a'), Numeral(5)), LiteralString('x'))),
            ('p.x[2]', Index(Index(Name('p'), LiteralString('x')), Numeral(2))),
        ]
        for a, expected in cases:
            with self.subTest(parsed=a, expected=expected):
                got = parser.var.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, expected)


class TestTableConstructors(unittest.TestCase):
    def test_table_constructors(self):
        cases = [
            ('{42,x,0}', [Field(Numeral(42)), Field(Name('x')), Field(Numeral(0))]),
            ('{42;x;0}', [Field(Numeral(42)), Field(Name('x')), Field(Numeral(0))]),
            ('{[1]=5,[42]=0}', [Field(Numeral(5), Numeral(1)), Field(Numeral(0), Numeral(42))]),
            ('{x=2,y=4}', [Field(Numeral(2), LiteralString('x')), Field(Numeral(4), LiteralString('y'))]),
            ('{42,x=4,[4]=1}', [Field(Numeral(42)), Field(Numeral(4), LiteralString('x')), Field(Numeral(1), Numeral(4))]),
        ]
        for a, b in cases:
            expected = Table(b)
            with self.subTest(parsed=a, expected=expected):
                got = parser.tableconstructor.parse_string(a, parse_all=True)[0]
                self.assertEqual(got, expected)
