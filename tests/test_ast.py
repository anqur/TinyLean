from unittest import TestCase

from TinyLean import ast, Ident, grammar

from . import parse


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Ident.fresh("i").id, Ident.fresh("j").id)


class TestParser(TestCase):
    def test_parse_name(self):
        a = parse(grammar.NAME, "  hello")[0]
        self.assertEqual(Ident, type(a))
        self.assertEqual("hello", a.text)

    def test_parse_name_unbound(self):
        a = parse(grammar.NAME, "_")[0]
        self.assertTrue(a.is_unbound())

    def test_parse_type(self):
        a = parse(grammar.TYPE, "  Type")[0]
        self.assertEqual(ast.Type, type(a))
        self.assertEqual(2, a.loc)

    def test_parse_reference(self):
        a = parse(grammar.REFERENCE, "  hello")[0]
        self.assertEqual(ast.Reference, type(a))
        self.assertEqual(2, a.loc)
        self.assertEqual("hello", a.name.text)

    def test_parse_paren_expr(self):
        a = parse(grammar.paren_expr, "(hello)")[0]
        self.assertEqual(ast.Reference, type(a))
        self.assertEqual(1, a.loc)
        self.assertEqual("hello", a.name.text)

    def test_parse_explicit_param(self):
        a = parse(grammar.explicit_param, " (a : Type)")[0]
        self.assertEqual(type(a), ast.Param)
        self.assertEqual("a", a.name.text)
        self.assertEqual(ast.Type, type(a.type))
        self.assertEqual(6, a.type.loc)

    def test_parse_implicit_param(self):
        a = parse(grammar.implicit_param, " {a: b}")[0]
        self.assertEqual(type(a), ast.Param)
        self.assertEqual("a", a.name.text)
        self.assertEqual(ast.Reference, type(a.type))
        self.assertEqual(5, a.type.loc)
