from unittest import TestCase

from . import resolve_expr
from .. import ast, Name, Param, ir

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
            ir.FnType(Param(Name("a"), ir.Type(), False), ir.Type()),
        )

    def test_check_expr_on_infer(self):
        check_expr("Type", ir.Type())

    def test_check_expr_on_infer_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            check_expr("(a: Type) -> a", ir.Ref(Name("a")))
        want, got, loc = e.exception.args
        self.assertEqual(0, loc)
        self.assertEqual("a", want)
        self.assertEqual("Type", got)

    def test_infer_expr_type(self):
        v, ty = infer_expr("Type")
        assert isinstance(v, ir.Type)
        assert isinstance(ty, ir.Type)

    def test_infer_expr_call_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            infer_expr("(Type) Type")
        want, got, loc = e.exception.args
        self.assertEqual(1, loc)
        self.assertEqual("function", want)
        self.assertEqual("Type", got)

    def test_infer_expr_function_type(self):
        v, ty = infer_expr("{a: Type} -> a")
        assert isinstance(v, ir.FnType)
        self.assertEqual("{a: Type} → a", str(v))
        assert isinstance(ty, ir.Type)

    def test_check_program(self):
        ast.check_string("def a: Type := Type")
        ast.check_string("def f (a: Type): Type := a")
        ast.check_string("def f: (_: Type) -> Type := fun a => a")
        ast.check_string("def id (T: Type) (a: T): T := a")

    def test_check_program_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string("def id (a: Type): a := Type")
        want, got, loc = e.exception.args
        self.assertEqual(23, loc)
        self.assertEqual("a", str(want))
        self.assertEqual("Type", str(got))

    def test_check_program_call(self):
        ast.check_string(
            """
            def f0 (a: Type): Type := a
            def f1: Type := f0 Type
            def f2: f0 Type := Type
            """
        )

    def test_check_program_call_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string(
                """
                def f0 (a: Type): Type := a
                def f1 (a: Type): Type := f0
                """
            )
        want, got, loc = e.exception.args
        self.assertEqual(87, loc)
        self.assertEqual("Type", str(want))
        self.assertEqual("(a: Type) → Type", str(got))

    def test_check_program_placeholder(self):
        ast.check_string(
            """
            def a := Type
            def b: Type := a
            """
        )

    def test_check_program_placeholder_locals(self):
        ast.check_string("def f (T: Type) (a: T) := a")

    def test_check_program_placeholder_unsolved(self):
        with self.assertRaises(ast.UnsolvedPlaceholderError) as e:
            ast.check_string("def a: Type := _")
        name, ctx, ty, loc = e.exception.args
        self.assertTrue(name.startswith("?u"))
        self.assertEqual(0, len(ctx))
        assert isinstance(ty, ir.Type)
        self.assertEqual(15, loc)

    def test_check_program_call_implicit_arg(self):
        _, _, example = ast.check_string(
            """
            def id {T: Type} (a: T): T := a
            def f := id (T := Type) Type
            example := f
            """
        )
        assert isinstance(example.body, ir.Type)

    def test_check_program_call_implicit_arg_failed(self):
        with self.assertRaises(ast.UndefinedImplicitParam) as e:
            ast.check_string(
                """
                def id {T: Type} (a: T): T := a
                def f := id (U := Type) Type
                """
            )
        name, loc = e.exception.args
        self.assertEqual("U", name)
        self.assertEqual(74, loc)

    def test_check_program_call_implicit_arg_long(self):
        ast.check_string(
            """
            def f {T: Type} {U: Type} (a: U): Type := T
            def g: f (U := Type) Type := Type
            """
        )

    def test_check_program_call_implicit(self):
        _, _, example = ast.check_string(
            """
            def id {T: Type} (a: T): T := a
            def f := id Type
            example := f
            """
        )
        assert isinstance(example.body, ir.Type)

    def test_check_program_call_no_explicit_failed(self):
        with self.assertRaises(ast.UnsolvedPlaceholderError) as e:
            ast.check_string(
                """
                def f {T: Type}: Type := T
                def g: Type := f
                """
            )
        name, ctx, ty, loc = e.exception.args
        self.assertTrue(name.startswith("?m"))
        self.assertEqual(1, len(ctx))
        assert isinstance(ty, ir.Type)
        self.assertEqual(75, loc)
