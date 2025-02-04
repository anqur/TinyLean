from unittest import TestCase

from .. import ast, Ident, grammar

from . import parse


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Ident.fresh("i").id, Ident.fresh("j").id)


class TestParser(TestCase):
    def test_parse_name(self):
        x = parse(grammar.NAME, "  hello")[0]
        self.assertEqual(Ident, type(x))
        self.assertEqual("hello", x.text)

    def test_parse_name_unbound(self):
        x = parse(grammar.NAME, "_")[0]
        self.assertTrue(x.is_unbound())

    def test_parse_type(self):
        x = parse(grammar.TYPE, "  Type")[0]
        self.assertEqual(ast.Type, type(x))
        self.assertEqual(2, x.loc)

    def test_parse_reference(self):
        x = parse(grammar.REFERENCE, "  hello")[0]
        self.assertEqual(ast.Reference, type(x))
        self.assertEqual(2, x.loc)
        self.assertEqual("hello", x.name.text)

    def test_parse_paren_expr(self):
        x = parse(grammar.paren_expr, "(hello)")[0]
        self.assertEqual(ast.Reference, type(x))
        self.assertEqual(1, x.loc)
        self.assertEqual("hello", x.name.text)

    def test_parse_explicit_param(self):
        x = parse(grammar.explicit_param, " (a : Type)")[0]
        self.assertEqual(type(x), ast.Param)
        self.assertEqual("a", x.name.text)
        self.assertEqual(ast.Type, type(x.type))
        self.assertEqual(6, x.type.loc)

    def test_parse_implicit_param(self):
        x = parse(grammar.implicit_param, " {a: b}")[0]
        self.assertEqual(type(x), ast.Param)
        self.assertEqual("a", x.name.text)
        self.assertEqual(ast.Reference, type(x.type))
        self.assertEqual(5, x.type.loc)

    def test_parse_call(self):
        x = parse(grammar.call, "a b")[0]
        self.assertEqual(type(x), ast.Call)
        self.assertEqual(type(x.callee), ast.Reference)
        self.assertEqual(x.callee.loc, 0)
        self.assertEqual(x.callee.name.text, "a")
        self.assertEqual(type(x.arg), ast.Reference)
        self.assertEqual(x.arg.loc, 2)
        self.assertEqual(x.arg.name.text, "b")

    def test_parse_call_paren(self):
        x = parse(grammar.call, "(a) b (Type)")[0]
        self.assertEqual(type(x), ast.Call)
        self.assertEqual(type(x.callee), ast.Call)
        self.assertEqual(type(x.callee.callee), ast.Reference)
        self.assertEqual(x.callee.callee.loc, 1)
        self.assertEqual(x.callee.callee.name.text, "a")
        self.assertEqual(type(x.callee.arg), ast.Reference)
        self.assertEqual(x.callee.arg.loc, 4)
        self.assertEqual(x.callee.arg.name.text, "b")
        self.assertEqual(type(x.arg), ast.Type)
        self.assertEqual(x.arg.loc, 7)
