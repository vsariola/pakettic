import unittest
from pakettic import parser
from pakettic import ast
from pakettic.ast import *


class TestStringLiterals(unittest.TestCase):
    def test_short_string_literals(self):
        self.assertEqual(parser.LiteralString.parse_string(
            '"test123"')[0].value, "test123")
        self.assertEqual(parser.LiteralString.parse_string(
            "'test123'")[0].value, "test123")
        self.assertEqual(parser.LiteralString.parse_string(
            "'test123\\n'")[0].value, "test123\n")
        self.assertEqual(parser.LiteralString.parse_string(
            "'test123\\t'")[0].value, "test123\t")
        self.assertEqual(parser.LiteralString.parse_string(
            "'test123\\''")[0].value, "test123'")

    def test_long_string_literals(self):
        self.assertEqual(parser.LiteralString.parse_string(
            '[[\ntest123]]')[0].value, "test123")
        self.assertEqual(parser.LiteralString.parse_string(
            '[==[\ntest123]==]')[0].value, "test123")
        self.assertEqual(parser.LiteralString.parse_string(
            '[==[\n[[test123]]]==]')[0].value, "[[test123]]")
        self.assertEqual(parser.LiteralString.parse_string(
            '[[\ntest\n123]]')[0].value, "test\n123")


class TestNumerals(unittest.TestCase):
    def test_ints(self):
        res = parser.Numeral.parse_string('123')[0]
        self.assertEqual(res, ast.Numeral(123, 0, 0))
        self.assertEqual(parser.Numeral.parse_string(
            '50000000')[0], ast.Numeral(50000000, 0, 0))
        self.assertEqual(parser.Numeral.parse_string('50')
                         [0], ast.Numeral(50, 0, 0))

    def test_fractionals(self):
        self.assertEqual(parser.Numeral.parse_string(
            '0.123')[0], ast.Numeral(0, 321, 0))
        self.assertEqual(parser.Numeral.parse_string(
            '.6192')[0], ast.Numeral(0, 2916, 0))
        with self.assertRaises(Exception):
            parser.Numeral.parse_string('. 123')

    def test_exponents(self):
        self.assertEqual(parser.Numeral.parse_string(
            '1e5')[0], ast.Numeral(1, 0, 5))
        self.assertEqual(parser.Numeral.parse_string(
            '1.5e10')[0], ast.Numeral(1, 5, 10))
        with self.assertRaises(Exception):
            parser.Numeral.parse_string('. 123')

    def test_hex(self):
        self.assertEqual(parser.Numeral.parse_string(
            '0xff')[0], ast.Numeral(255, hex=True))
        self.assertEqual(parser.Numeral.parse_string(
            '0Xff')[0], ast.Numeral(255, hex=True))
        self.assertEqual(parser.Numeral.parse_string(
            '0XFF')[0], ast.Numeral(255, hex=True))
        self.assertEqual(parser.Numeral.parse_string(
            '0xFF.A')[0], ast.Numeral(255, 10, hex=True))
        self.assertEqual(parser.Numeral.parse_string(
            '0xFF.Ap5')[0], ast.Numeral(255, 10, 5, hex=True))


class TestNames(unittest.TestCase):
    def test_valid_names(self):
        self.assertEqual(parser.Name.parse_string('foo')[0], 'foo')
        self.assertEqual(parser.Name.parse_string('Foo')[0], 'Foo')
        self.assertEqual(parser.Name.parse_string('Foo_')[0], 'Foo_')

    def test_invalid_names(self):
        with self.assertRaises(Exception):
            parser.Name.parse_string('_foo')
        with self.assertRaises(Exception):
            parser.Name.parse_string('1foo')

    def test_keywords(self):
        self.assertEqual(parser.Name.parse_string('iff')[0], 'iff')
        with self.assertRaises(Exception):
            parser.Name.parse_string('if')
        with self.assertRaises(Exception):
            parser.Name.parse_string('break')


class TestAssignments(unittest.TestCase):
    def test_singles(self):
        self.assertEqual(parser.chunk.parse_string('x=5')[0], ast.Block([ast.Assign([ast.Name('x')], [ast.Numeral(5)])]))

    def test_tuples(self):
        self.assertEqual(parser.chunk.parse_string('x,y=1,2')[0], ast.Block([ast.Assign(
            [ast.Name('x'), ast.Name('y')], [ast.Numeral(1), ast.Numeral(2)])]))


class TestFlowControl(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(parser.chunk.parse_string('::test_label::')[0], ast.Block([ast.Label('test_label')]))

    def test_break(self):
        self.assertEqual(parser.chunk.parse_string('break')[0], ast.Block([ast.Break()]))

    def test_goto(self):
        self.assertEqual(parser.chunk.parse_string('goto test_label')[0], ast.Block([ast.Goto('test_label')]))
        self.assertEqual(parser.chunk.parse_string('goto foo;goto bar')[0], ast.Block([ast.Goto('foo'), ast.Goto('bar')]))

    def test_block(self):
        self.assertEqual(parser.parse_string('do break end'), ast.Block([ast.Do(ast.Block([ast.Break()]))]))

    def test_while(self):
        self.assertEqual(parser.chunk.parse_string('while true do break end')[
                         0], ast.Block([ast.While(ast.Boolean(True), ast.Block([ast.Break()]))]))

    def test_repeat(self):
        self.assertEqual(parser.chunk.parse_string('repeat break until true')[
                         0], ast.Block([ast.Repeat(ast.Boolean(True), ast.Block([ast.Break()]))]))

    def test_ranged_for_loop(self):
        self.assertEqual(
            parser.chunk.parse_string('for i = 0,5 do break end')[0],
            ast.Block([ast.ForRange(var=ast.Name('i'), lb=ast.Numeral(0), ub=ast.Numeral(5), step=None, body=ast.Block([ast.Break()]))]))


class TestBranching(unittest.TestCase):
    def test_if(self):
        self.assertEqual(parser.chunk.parse_string('if true then end')[0], ast.Block(
            [ast.If(test=ast.Boolean(True), body=ast.Block([]), orelse=None)]))

    def test_else(self):
        self.assertEqual(parser.chunk.parse_string('if true then else break end')[
                         0], ast.Block([ast.If(test=ast.Boolean(True), body=ast.Block([]), orelse=ast.Block([ast.Break()]))]))

    def test_elseif(self):
        self.assertEqual(parser.chunk.parse_string('if true then elseif true then else break end')[
                         0], ast.Block([ast.If(test=ast.Boolean(True), body=ast.Block([]), orelse=ast.Block([ast.If(test=ast.Boolean(True), body=ast.Block([]), orelse=ast.Block([ast.Break()]))]))]))


class TestComments(unittest.TestCase):
    def test_single_line_comments(self):
        self.assertEqual(parser.chunk.parse_string('goto --comment\ntest_label')[0], ast.Block([ast.Goto('test_label')]))
        self.assertEqual(
            parser.chunk.parse_string('goto foo--comment\n--comment\ngoto bar')[0],
            ast.Block([ast.Goto('foo'), ast.Goto('bar')]))


class TestFunction(unittest.TestCase):
    def test_function(self):
        self.assertEqual(parser.chunk.parse_string('f=function(x) end')[0], ast.Block([
                         ast.Assign([ast.Name('f')], [ast.Func(args=[ast.Name('x')], body=ast.Block([]))])]))

    def test_return(self):
        self.assertEqual(parser.chunk.parse_string('return 0')[0], ast.Block([ast.Return([ast.Numeral(0)])]))


class TestCall(unittest.TestCase):
    def test_call(self):
        got = parser.parse_string('debug()')
        expected = Block([Call(func=Name("debug"), args=[])])
        self.assertEqual(got, expected)


class TestBinaryOperators(unittest.TestCase):
    def test_add(self):
        got = parser.parse_string('x = 1 + 2')
        expected = Block([Assign([Name('x')], [BinOp(left=Numeral(1), op="+", right=Numeral(2))])])
        self.assertEqual(got, expected)

    def test_multiadd(self):
        self.assertEqual(parser.parse_string('x = 1 + 2 + 3'), ast.Block([ast.Assign([ast.Name('x')], [ast.BinOp(
            left=ast.BinOp(left=ast.Numeral(1), op="+", right=ast.Numeral(2)), op='+', right=ast.Numeral(3))])]))

    def test_precedence(self):
        self.assertEqual(parser.parse_string('x = 6+1*2'), ast.Block([ast.Assign([ast.Name('x')], [ast.BinOp(
            left=ast.Numeral(6), op="+", right=ast.BinOp(left=ast.Numeral(1), op="*", right=ast.Numeral(2)))])]))


class TestUnaryOperators(unittest.TestCase):
    def test_minus(self):
        got = parser.parse_string('x = -1')
        expected = Block([Assign([Name('x')], [UnaryOp(op="-", operand=Numeral(1))])])
        self.assertEqual(got, expected)

    def test_association(self):
        got = parser.parse_string('x = -#a')
        expected = Block([Assign([Name('x')], [UnaryOp(op='-', operand=UnaryOp(op="#", operand=Name("a")))])])
        self.assertEqual(got, expected)

    def test_multiadd(self):
        got = parser.parse_string('x = 1 + 2 + 3')
        expected = Block([Assign([Name('x')], [BinOp(BinOp(Numeral(1), "+", Numeral(2)), '+', Numeral(3))])])
        self.assertEqual(got, expected)


class TestLocals(unittest.TestCase):
    def test_local_vars(self):
        got = parser.chunk.parse_string('local x = 5')[0]
        expected = Block([Local(targets=[ast.Name('x')], values=[Numeral(5)])])
        self.assertEqual(got, expected)
