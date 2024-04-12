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
        algorithms = [
            'anneal',
            'lahc',
            'dlas',
        ]
        for code in cases:
            for alg in algorithms:
                with self.subTest(code=code, alg=alg):
                    try:
                        root = parser.parse_string(code)

                        def cost_func(root_data, _):
                            root, _ = root_data
                            # slightly more interesting cost function than just string length, so
                            # that we see some optimization happening even with these small carts
                            printed = printer.format(root)
                            return sum(bytes(printed, 'ascii'))
                        if alg == 'lahc':
                            opt_root = optimize.lahc((root, None), steps=100, list_length=50, init_margin=0, seed=0, cost_func=cost_func)
                        elif alg == 'dlas':
                            opt_root = optimize.dlas((root, None), steps=100, list_length=5, init_margin=0, seed=0, cost_func=cost_func)
                        else:
                            opt_root = optimize.anneal((root, None), steps=100, start_temp=1, end_temp=0.1, seed=0, cost_func=cost_func)

                        printed = printer.format(opt_root)
                        self.assertGreater(len(printed), 0)
                    except Exception as err:
                        self.fail(err)
