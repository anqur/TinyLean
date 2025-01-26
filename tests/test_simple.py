import unittest

from TinyLean.simple import add_one


class TestSimple(unittest.TestCase):

    def test_add_one(self):
        self.assertEqual(add_one(5), 6)


if __name__ == "__main__":
    unittest.main()
