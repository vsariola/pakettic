import io
import unittest
from pakettic import fileformats


class TestCarts(unittest.TestCase):
    def test_tic_carts(self):
        with io.open("data/cracklebass.tic", "rb") as file:
            bytes = file.read()
            input = io.BytesIO(bytes)
            c = fileformats.read_tic(input)
            output = io.BytesIO()
            fileformats.write_tic(c, output)
            self.assertEqual(bytes, output.getbuffer())

    def test_lua_carts(self):
        with io.open("data/cracklebass.lua", "r") as file:
            self.maxDiff = None
            str = file.read()
            input = io.StringIO(str)
            c = fileformats.read_lua(input)
            output = io.StringIO()
            fileformats.write_lua(c, output)
            self.assertEqual(str, output.getvalue())
