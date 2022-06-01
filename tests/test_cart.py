import io
import unittest
from pakettic import ticfile


class TestCarts(unittest.TestCase):
    def test_tic_carts(self):
        with io.open("tests/data/cracklebass.tic", "rb") as file:
            bytes = file.read()
            input = io.BytesIO(bytes)
            c = ticfile.read_tic(input)
            output = io.BytesIO()
            ticfile.write_tic(c, output)
            self.assertEqual(bytes, output.getbuffer())

    def test_lua_carts(self):
        with io.open("tests/data/cracklebass.lua", "r") as file:
            self.maxDiff = None
            str = file.read()
            input = io.StringIO(str)
            c = ticfile.read_lua(input)
            output = io.StringIO()
            ticfile.write_lua(c, output)
            self.assertEqual(str, output.getvalue())
