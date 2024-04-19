import unittest
from pakettic import parser
from pakettic import printer
from pakettic import optimize


class TestOptimization(unittest.TestCase):
    def test_single_processing_no_crashes(self):
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
        queue_lengths_cases = [1, 10]
        for code in cases:
            for alg in algorithms:
                for queue_length in queue_lengths_cases:
                    with self.subTest(code=code, alg=alg, queue_length=queue_length):
                        try:
                            root = parser.parse_string(code)
                            with optimize.Solutions((root, None), 0, queue_length, 1, _cost_func, lambda x: None) as solutions:
                                if alg == 'lahc':
                                    opt_root = optimize.lahc(solutions, steps=100, list_length=50, init_margin=0)
                                elif alg == 'dlas':
                                    opt_root = optimize.dlas(solutions, steps=100, list_length=5, init_margin=0)
                                else:
                                    opt_root = optimize.anneal(solutions, steps=100, start_temp=1, end_temp=0.1, seed=0)
                            printed = printer.format(opt_root)
                            self.assertGreater(len(printed), 0)
                        except Exception as err:
                            self.fail(err)

    def test_multi_processing_no_crashes(self):
        cases = [
            'if true then else break end',
            'f=function(x) end',
        ]
        algorithms = [
            'anneal',
            'lahc',
            'dlas',
        ]
        queue_lengths_cases = [1, 10]
        for code in cases:
            for alg in algorithms:
                for queue_length in queue_lengths_cases:
                    with self.subTest(code=code, alg=alg, queue_length=queue_length):
                        try:
                            root = parser.parse_string(code)
                            with optimize.Solutions((root, None), 0, queue_length, 4, _cost_func, lambda x: None) as solutions:
                                if alg == 'lahc':
                                    opt_root = optimize.lahc(solutions, steps=100, list_length=50, init_margin=0)
                                elif alg == 'dlas':
                                    opt_root = optimize.dlas(solutions, steps=100, list_length=5, init_margin=0)
                                else:
                                    opt_root = optimize.anneal(solutions, steps=100, start_temp=1, end_temp=0.1, seed=0)
                            printed = printer.format(opt_root)
                            self.assertGreater(len(printed), 0)
                        except Exception as err:
                            self.fail(err)


def _cost_func(root_data):
    root, _ = root_data
    # slightly more interesting cost function than just string length, so
    # that we see some optimization happening even with these small carts
    printed = printer.format(root)
    return sum(bytes(printed, 'ascii')), None
