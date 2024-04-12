import io
import unittest

import zopfli
from pakettic import ticfile


class TestCarts(unittest.TestCase):
    def test_tic_carts(self):
        def compress(bytes=None):
            c = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB)
            return (c.compress(bytes) + c.flush())
        cases = [
            ("tests/data/cracklebass.tic", False, False),
            ("tests/data/cracklebass.tic", True, False),
            ("tests/data/cracklebass.tic", False, True),
            ("tests/data/cracklebass.tic", True, True),
            ("tests/data/timeline2.tic", False, False),
            ("tests/data/timeline2.tic", False, True),
        ]
        for path, c, pedantic in cases:
            with self.subTest(path=path, compress=c, pedantic=pedantic):
                with io.open(path, "rb") as file:
                    # Read original cart
                    orig_cart = ticfile.read_tic(file)
                    # Write the original cart into memory file
                    output = io.BytesIO()
                    size, finish = ticfile.write_tic(
                        orig_cart.data, pedantic, compress if c else None)(orig_cart.code)
                    self.assertEqual(size, finish(output))
                    # Read the written cart
                    output.seek(0)
                    new_cart = ticfile.read_tic(output)
                    # Compare the original and the new cart
                    self.assertEqual(orig_cart, new_cart)

    def test_lua_carts(self):
        cases = [
            "tests/data/cracklebass.lua",
            "tests/data/timeline2.lua",
        ]
        for path in cases:
            with self.subTest(path=path):
                with io.open(path, "r", encoding="latin-1") as file:
                    # Read original cart
                    orig_cart = ticfile.read_lua(file)
                    # Write the original cart into memory file
                    output = io.BytesIO()
                    size, finish = ticfile.write_lua(
                        orig_cart.data)(orig_cart.code)
                    self.assertEqual(size, finish(output))
                    # Read the written cart
                    output.seek(0)
                    wrapper = io.TextIOWrapper(output, encoding='latin-1')
                    new_cart = ticfile.read_lua(wrapper)
                    # Compare the original and the new cart
                    self.assertEqual(orig_cart, new_cart)

    def test_png_carts(self):
        def compress(bytes=None):
            c = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB)
            return (c.compress(bytes) + c.flush())
        cases = [
            ("tests/data/timeline2.png", False),
            ("tests/data/timeline2.png", True),
        ]
        for path, pedantic in cases:
            with self.subTest(path=path, pedantic=pedantic):
                with io.open(path, "rb") as file:
                    # Read original cart
                    orig_cart = ticfile.read_png(file)
                    # Write the original cart into memory file
                    output = io.BytesIO()
                    size, finish = ticfile.write_png(
                        orig_cart.data, pedantic, compress)(orig_cart.code)
                    self.assertEqual(size, finish(output))
                    # Read the written cart
                    output.seek(0)
                    new_cart = ticfile.read_png(output)
                    # Compare the original and the new cart
                    self.assertEqual(orig_cart, new_cart)
