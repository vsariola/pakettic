import unittest
from pakettic import parser
from pakettic import printer
from pakettic import optimize


class TestOptimization(unittest.TestCase):
    def test_no_crashes(self):
        cases = [
            'q={42,x,0}',
            'q={42;x;0}',
            'q={[1]=5,[42]=0}',
            'q={x=2,y=4}',
            'q={42,x=4,[4]=1}',
            'obj:f(42)',
            'function q(x) end',
            'function q.foo(x) end',
            'function q:bar(x) end',
            'function q.foo:bar(x) end',
            'x=5',
            'p.x=5',
            'p[5]=5',
            'p[5].x=5',
            'x,y=1,2',
            'local y=42',
            'do break end',
            'for i=1,10 do end',
            'for k,v in a do end',
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
            with self.subTest(parsed=a):
                try:
                    root = parser.parse_string(a)

                    def cost_func(root, _):
                        # slightly more interesting cost function than just string length, so
                        # that we see some optimization happening even with these small carts
                        printed = printer.format(root)
                        return sum(bytes(printed, 'ascii'))
                    opt_root = optimize.dlas(root, steps=100, list_length=5, init_margin=0, seed=0, cost_func=cost_func)
                    printed = printer.format(opt_root)
                    self.assertGreater(len(printed), 0)
                except Exception as err:
                    self.fail(err)

    def test_minify(self):
        cases = {
                'poke(0x3fc0,0)': 'poke(16320,0)',
                'print(1000000000001)': 'print(0xe8d4a51001)',
        }
        for a, expected in cases.items():
            with self.subTest(parsed=a):
                root = parser.parse_string(a)
                opt_root = optimize.dlas(root, steps=100, list_length=5, init_margin=0, seed=0, cost_func=lambda root,_: len(printer.format(root)))
                printed = printer.format(opt_root)
                self.assertEqual(printed, expected)
