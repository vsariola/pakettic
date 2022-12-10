import unittest
from pakettic import parser
from pakettic import printer
from pakettic.ast import *


class TestPrinter(unittest.TestCase):
    def test_printing_parsed_code(self):
        cases = [
            'x=5',
            'p.x=5',
            'p[5]=5',
            'p[5].x=5',
            'x,y=1,2',
            'local y=42',
            'do break end',
            'for i=1,10 do end',
            'x=0xAC',
            'x=0xAC x=0xFF',
            '::foo::',
            'return 0',
            'goto foo\ngoto bar',
            'while true do end',
            'repeat break until true',
            'if true then end',
            'if true then else break end',
            'if true then elseif true then else break end',
            'f=function(x) end',
            'debug()',
        ]
        for a in cases:
            with self.subTest(code=a):
                expected = parser.parse_string(a)
                printed = printer.format(expected)
                got = parser.parse_string(printed)
                self.assertEqual(got, expected)
