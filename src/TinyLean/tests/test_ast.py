from typing import cast
from unittest import TestCase

from .. import ast, Ident, grammar, Param, Declaration, ir

from . import parse


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Ident.fresh("i").id, Ident.fresh("j").id)


class TestParser(TestCase):
    def test_parse_name(self):
        x = parse(grammar.IDENT, "  hello")[0]
        self.assertEqual(Ident, type(x))
        self.assertEqual("hello", x.text)

    def test_parse_name_unbound(self):
        x = parse(grammar.IDENT, "_")[0]
        self.assertTrue(x.is_unbound())

    def test_parse_type(self):
        x = parse(grammar.TYPE, "  Type")[0]
        self.assertEqual(ast.Type, type(x))
        self.assertEqual(2, x.loc)

    def test_parse_reference(self):
        x = parse(grammar.REF, "  hello")[0]
        self.assertEqual(ast.Ref, type(x))
        self.assertEqual(2, x.loc)
        self.assertEqual("hello", x.name.text)

    def test_parse_paren_expr(self):
        x = parse(grammar.paren_expr, "(hello)")[0]
        self.assertEqual(ast.Ref, type(x))
        self.assertEqual(1, x.loc)
        self.assertEqual("hello", x.name.text)

    def test_parse_implicit_param(self):
        x = parse(grammar.implicit_param, " {a: b}")[0]
        self.assertEqual(Param, type(x))
        self.assertTrue(x.implicit)
        self.assertEqual("a", x.name.text)
        self.assertEqual(ast.Ref, type(x.type))
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
        self.assertEqual(ast.Ref, type(x.callee))
        self.assertEqual(0, x.callee.loc)
        self.assertEqual("a", x.callee.name.text)
        self.assertEqual(ast.Ref, type(x.arg))
        self.assertEqual(2, x.arg.loc)
        self.assertEqual("b", x.arg.name.text)

    def test_parse_call_paren(self):
        x = parse(grammar.call, "(a) b (Type)")[0]
        self.assertEqual(ast.Call, type(x))
        self.assertEqual(0, x.loc)
        self.assertEqual(ast.Call, type(x.callee))
        self.assertEqual(ast.Ref, type(x.callee.callee))
        self.assertEqual(1, x.callee.callee.loc)
        self.assertEqual("a", x.callee.callee.name.text)
        self.assertEqual(ast.Ref, type(x.callee.arg))
        self.assertEqual(4, x.callee.arg.loc)
        self.assertEqual("b", x.callee.arg.name.text)
        self.assertEqual(ast.Type, type(x.arg))
        self.assertEqual(7, x.arg.loc)

    def test_parse_call_paren_function(self):
        x = parse(grammar.call, "(fun _ => Type) Type")[0]
        self.assertEqual(ast.Call, type(x))
        self.assertEqual(0, x.loc)
        self.assertEqual(ast.Fn, type(x.callee))
        self.assertEqual(1, x.callee.loc)
        self.assertTrue(x.callee.param.is_unbound())
        self.assertEqual(ast.Type, type(x.callee.body))
        self.assertEqual(10, x.callee.body.loc)
        self.assertEqual(ast.Type, type(x.arg))
        self.assertEqual(16, x.arg.loc)

    def test_parse_function_type(self):
        x = parse(grammar.function_type, "  (a : Type) -> a")[0]
        self.assertEqual(ast.FnType, type(x))
        self.assertEqual(Param, type(x.param))
        self.assertEqual("a", x.param.name.text)
        self.assertEqual(ast.Type, type(x.param.type))
        self.assertEqual(7, x.param.type.loc)
        self.assertEqual(ast.Ref, type(x.ret))
        self.assertEqual("a", x.ret.name.text)
        self.assertEqual(16, x.ret.loc)

    def test_parse_function_type_long(self):
        x = parse(grammar.function_type, " {a : Type} -> (b: Type) -> a")[0]
        self.assertEqual(ast.FnType, type(x))
        self.assertEqual(Param, type(x.param))
        self.assertEqual("a", x.param.name.text)
        self.assertEqual(ast.Type, type(x.param.type))
        self.assertEqual(6, x.param.type.loc)
        self.assertEqual(ast.FnType, type(x.ret))
        self.assertEqual(Param, type(x.ret.param))
        self.assertEqual("b", x.ret.param.name.text)
        self.assertEqual(ast.Type, type(x.ret.param.type))
        self.assertEqual(19, x.ret.param.type.loc)
        self.assertEqual(ast.Ref, type(x.ret.ret))
        self.assertEqual("a", x.ret.ret.name.text)
        self.assertEqual(28, x.ret.ret.loc)

    def test_parse_function(self):
        x = parse(grammar.function, "  fun a => a")[0]
        self.assertEqual(ast.Fn, type(x))
        self.assertEqual(2, x.loc)
        self.assertEqual(Ident, type(x.param))
        self.assertEqual("a", x.param.text)
        self.assertEqual(ast.Ref, type(x.body))
        self.assertEqual("a", x.body.name.text)
        self.assertEqual(11, x.body.loc)

    def test_parse_function_long(self):
        x = parse(grammar.function, "   fun a => fun b => a b")[0]
        self.assertEqual(ast.Fn, type(x))
        self.assertEqual(3, x.loc)
        self.assertEqual(Ident, type(x.param))
        self.assertEqual("a", x.param.text)
        self.assertEqual(ast.Fn, type(x.body))
        self.assertEqual(12, x.body.loc)
        self.assertEqual(Ident, type(x.body.param))
        self.assertEqual("b", x.body.param.text)
        self.assertEqual(ast.Call, type(x.body.body))
        self.assertEqual(21, x.body.body.loc)
        self.assertEqual(ast.Ref, type(x.body.body.callee))
        self.assertEqual("a", x.body.body.callee.name.text)
        self.assertEqual(ast.Ref, type(x.body.body.arg))
        self.assertEqual("b", x.body.body.arg.name.text)

    def test_parse_definition_constant(self):
        x = parse(grammar.definition, "  def f : Type := Type")[0]
        self.assertEqual(Declaration, type(x))
        self.assertEqual(6, x.loc)
        self.assertEqual("f", x.name.text)
        self.assertEqual(0, len(x.params))
        self.assertEqual(ast.Type, type(x.ret))
        self.assertEqual(10, x.ret.loc)
        self.assertEqual(ast.Type, type(x.body))
        self.assertEqual(18, x.body.loc)

    def test_parse_definition(self):
        x = parse(grammar.definition, "  def f {a: Type} (b: Type): Type := a")[0]
        self.assertEqual(ast.Declaration, type(x))
        self.assertEqual(6, x.loc)
        self.assertEqual("f", x.name.text)
        self.assertEqual(list, type(x.params))
        self.assertEqual(2, len(x.params))
        self.assertEqual(ast.Param, type(x.params[0]))
        self.assertTrue(x.params[0].implicit)
        self.assertEqual("a", x.params[0].name.text)
        self.assertEqual(ast.Type, type(x.params[0].type))
        self.assertEqual(12, x.params[0].type.loc)
        self.assertEqual(ast.Param, type(x.params[1]))
        self.assertFalse(x.params[1].implicit)
        self.assertEqual("b", x.params[1].name.text)
        self.assertEqual(ast.Type, type(x.params[1].type))
        self.assertEqual(22, x.params[1].type.loc)

    def test_parse_program(self):
        x = list(
            parse(
                grammar.program,
                """
                def a: Type := Type
                def b: Type := Type
                """,
            )
        )
        self.assertEqual(2, len(x))
        self.assertEqual(Declaration, type(x[0]))
        self.assertEqual("a", x[0].name.text)
        self.assertEqual(Declaration, type(x[1]))
        self.assertEqual("b", x[1].name.text)


resolve_expr = lambda s: ast.NameResolver().expr(parse(grammar.expr, s)[0][0])
resolve = lambda s: ast.NameResolver().run(list(parse(grammar.program, s)))


class TestNameResolver(TestCase):
    def test_resolve_expr_function(self):
        x = cast(ast.Fn, resolve_expr("fun a => fun b => a b"))
        y = cast(ast.Fn, x.body)
        z = cast(ast.Call, y.body)
        callee = cast(ast.Ref, z.callee)
        arg = cast(ast.Ref, z.arg)
        self.assertEqual(x.param.id, callee.name.id)
        self.assertEqual(y.param.id, arg.name.id)

    def test_resolve_expr_function_failed(self):
        with self.assertRaises(ast.UndefinedVariableError) as e:
            resolve_expr("fun a => b")
        n, loc = e.exception.args
        self.assertEqual(9, loc)
        self.assertEqual("b", n.text)

    def test_resolve_expr_function_type(self):
        x = cast(ast.FnType, resolve_expr("{a: Type} -> (b: Type) -> a"))
        y = cast(ast.FnType, x.ret)
        z = cast(ast.Ref, y.ret)
        self.assertEqual(x.param.name.id, z.name.id)
        self.assertNotEqual(y.param.name.id, z.name.id)

    def test_resolve_expr_function_type_failed(self):
        with self.assertRaises(ast.UndefinedVariableError) as e:
            resolve_expr("{a: Type} -> (b: Type) -> c")
        n, loc = e.exception.args
        self.assertEqual(26, loc)
        self.assertEqual("c", n.text)

    def test_resolve_program(self):
        resolve(
            """
            def f0 (a: Type): Type := a
            def f1 (a: Type): Type := f0 a 
            """
        )

    def test_resolve_program_failed(self):
        with self.assertRaises(ast.UndefinedVariableError) as e:
            resolve("def f (a: Type) (b: c): Type := Type")
        n, loc = e.exception.args
        self.assertEqual(20, loc)
        self.assertEqual("c", n.text)

    def test_resolve_program_duplicate(self):
        with self.assertRaises(ast.DuplicateVariableError) as e:
            resolve(
                """
                def f0: Type := Type
                def f0: Type := Type
                """
            )
        n, loc = e.exception.args
        self.assertEqual(58, loc)
        self.assertEqual("f0", n.text)


check = lambda s: ast.TypeChecker().run(resolve(s))
check_expr = lambda s, t: ast.TypeChecker().check(resolve_expr(s), t)
infer_expr = lambda s: ast.TypeChecker().infer(resolve_expr(s))


class TestTypeChecker(TestCase):
    def test_check_expr_type(self):
        check_expr("Type", ir.Type())
        check_expr("{a: Type} -> (b: Type) -> a", ir.Type())

    def test_check_expr_type_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            check_expr("fun a => a", ir.Type())
        want, got, loc = e.exception.args
        self.assertEqual(0, loc)
        self.assertEqual("Type", want)
        self.assertEqual("function", got)

    def test_check_expr_function(self):
        check_expr(
            "fun a => a",
            ir.FnType(Param(Ident.fresh("a"), ir.Type(), False), ir.Type()),
        )

    def test_check_expr_on_infer(self):
        check_expr("Type", ir.Type())

    def test_check_expr_on_infer_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            check_expr("(a: Type) -> a", ir.Ref(Ident.fresh("a")))
        want, got, loc = e.exception.args
        self.assertEqual(0, loc)
        self.assertEqual("a", want)
        self.assertEqual("Type", got)

    def test_infer_expr_type(self):
        v, ty = infer_expr("Type")
        self.assertEqual(ir.Type, type(v))
        self.assertEqual(ir.Type, type(ty))

    def test_infer_expr_function_type(self):
        v, ty = infer_expr("{a: Type} -> a")
        self.assertEqual(ir.FnType, type(v))
        self.assertEqual("{a: Type} → a", str(v))
        self.assertEqual(ir.Type, type(ty))

    def test_check_program(self):
        check("def a: Type := Type")
        check("def id (a: Type): Type := a")

    def test_check_program_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            check("def id (a: Type): a := Type")
        want, got, loc = e.exception.args
        self.assertEqual(23, loc)
        self.assertEqual("a", str(want))
        self.assertEqual("Type", str(got))

    def test_check_program_call(self):
        check(
            """
            def f0 (a: Type): Type := Type
            def f1: Type := f0 Type
            """
        )
