from unittest import TestCase

from TinyLean import Ident


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Ident.fresh("i").id, Ident.fresh("j").id)


class TestAST(TestCase):
    def test_parse_program(self):
        # TODO
        pass
