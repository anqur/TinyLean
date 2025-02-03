from unittest import TestCase

from TinyLean import ast, Ident, grammar

from . import parse


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Ident.fresh("i").id, Ident.fresh("j").id)


class TestParser(TestCase):
    def test_parse_name(self):
        a = parse(grammar.NAME, "  hello")[0]
        self.assertEqual(type(a), Ident)
        self.assertEqual(a.text, "hello")

    def test_parse_name_unbound(self):
        a = parse(grammar.NAME, "_")[0]
        self.assertTrue(a.is_unbound())

    def test_parse_type(self):
        a = parse(grammar.TYPE, "  Type")[0]
        self.assertEqual(type(a), ast.Type)
        self.assertEqual(a.loc, 2)

    def test_parse_reference(self):
        a = parse(grammar.REFERENCE, "  hello")[0]
        self.assertEqual(type(a), ast.Reference)
        self.assertEqual(a.loc, 2)
        self.assertEqual(a.name.text, "hello")

    def test_parse_paren_expr(self):
        a = parse(grammar.paren_expr, "(hello)")[0]
        self.assertEqual(type(a), ast.Reference)
        self.assertEqual(a.loc, 1)
        self.assertEqual(a.name.text, "hello")
