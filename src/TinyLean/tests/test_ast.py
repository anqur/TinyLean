from unittest import TestCase

from .. import ast, Ident, grammar, Param, Declaration

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

    def test_parse_implicit_param(self):
        x = parse(grammar.implicit_param, " {a: b}")[0]
        self.assertEqual(Param, type(x))
        self.assertTrue(x.implicit)
        self.assertEqual("a", x.name.text)
        self.assertEqual(ast.Reference, type(x.type))
        self.assertEqual(5, x.type.loc)

    def test_parse_explicit_param(self):
        x = parse(grammar.explicit_param, " (a : Type)")[0]
        self.assertEqual(Param, type(x))
        self.assertFalse(x.implicit)
        self.assertEqual("a", x.name.text)
        self.assertEqual(ast.Type, type(x.type))
        self.assertEqual(6, x.type.loc)

    def test_parse_call(self):
        x = parse(grammar.call, "a b")[0]
        self.assertEqual(ast.Call, type(x))
        self.assertEqual(0, x.loc)
        self.assertEqual(ast.Reference, type(x.callee))
        self.assertEqual(0, x.callee.loc)
        self.assertEqual("a", x.callee.name.text)
        self.assertEqual(ast.Reference, type(x.arg))
        self.assertEqual(2, x.arg.loc)
        self.assertEqual("b", x.arg.name.text)

    def test_parse_call_paren(self):
        x = parse(grammar.call, "(a) b (Type)")[0]
        self.assertEqual(ast.Call, type(x))
        self.assertEqual(0, x.loc)
        self.assertEqual(ast.Call, type(x.callee))
        self.assertEqual(ast.Reference, type(x.callee.callee))
        self.assertEqual(1, x.callee.callee.loc)
        self.assertEqual("a", x.callee.callee.name.text)
        self.assertEqual(ast.Reference, type(x.callee.arg))
        self.assertEqual(4, x.callee.arg.loc)
        self.assertEqual("b", x.callee.arg.name.text)
        self.assertEqual(ast.Type, type(x.arg))
        self.assertEqual(7, x.arg.loc)

    def test_parse_function_type(self):
        x = parse(grammar.function_type, "  (a : Type) -> a")[0]
        self.assertEqual(ast.FunctionType, type(x))
        self.assertEqual(Param, type(x.param))
        self.assertEqual("a", x.param.name.text)
        self.assertEqual(ast.Type, type(x.param.type))
        self.assertEqual(7, x.param.type.loc)
        self.assertEqual(ast.Reference, type(x.return_type))
        self.assertEqual("a", x.return_type.name.text)
        self.assertEqual(16, x.return_type.loc)

    def test_parse_function_type_long(self):
        x = parse(grammar.function_type, " {a : Type} -> (b: Type) -> a")[0]
        self.assertEqual(ast.FunctionType, type(x))
        self.assertEqual(Param, type(x.param))
        self.assertEqual("a", x.param.name.text)
        self.assertEqual(ast.Type, type(x.param.type))
        self.assertEqual(6, x.param.type.loc)
        self.assertEqual(ast.FunctionType, type(x.return_type))
        self.assertEqual(Param, type(x.return_type.param))
        self.assertEqual("b", x.return_type.param.name.text)
        self.assertEqual(ast.Type, type(x.return_type.param.type))
        self.assertEqual(19, x.return_type.param.type.loc)
        self.assertEqual(ast.Reference, type(x.return_type.return_type))
        self.assertEqual("a", x.return_type.return_type.name.text)
        self.assertEqual(28, x.return_type.return_type.loc)

    def test_parse_function(self):
        x = parse(grammar.function, "  fun a => a")[0]
        self.assertEqual(ast.Function, type(x))
        self.assertEqual(2, x.loc)
        self.assertEqual(Ident, type(x.param_name))
        self.assertEqual("a", x.param_name.text)
        self.assertEqual(ast.Reference, type(x.body))
        self.assertEqual("a", x.body.name.text)
        self.assertEqual(11, x.body.loc)

    def test_parse_definition_constant(self):
        x = parse(grammar.definition, "  def a : Type := Type")[0]
        self.assertEqual(Declaration, type(x))
        self.assertEqual(2, x.loc)
        self.assertEqual(0, len(x.params))
        self.assertEqual(ast.Type, type(x.return_type))
        self.assertEqual(10, x.return_type.loc)
        self.assertEqual(ast.Type, type(x.definition))
        self.assertEqual(18, x.definition.loc)
        # TODO: Definitions with non-empty parameters.
