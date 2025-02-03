from unittest import TestCase

from TinyLean import ast, Ident, grammar


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Ident.fresh("i").id, Ident.fresh("j").id)


class TestParser(TestCase):
    def test_parse_name(self):
        i = grammar.NAME.parse_string("hello", parse_all=True)[0]
        self.assertEqual(type(i), Ident)
        self.assertEqual(i.text, "hello")
