from unittest import TestCase

from . import resolve_expr, resolve
from .. import ast


class TestNameResolver(TestCase):
    def test_resolve_expr_function(self):
        x = resolve_expr("fun a => fun b => a b")
        assert isinstance(x, ast.Fn)
        assert isinstance(x.body, ast.Fn)
        assert isinstance(x.body.body, ast.Call)
        assert isinstance(x.body.body.callee, ast.Ref)
        assert isinstance(x.body.body.arg, ast.Ref)
        self.assertEqual(x.param.id, x.body.body.callee.name.id)
        self.assertEqual(x.body.param.id, x.body.body.arg.name.id)

    def test_resolve_expr_function_shadowed(self):
        x = resolve_expr("fun a => fun a => a")
        assert isinstance(x, ast.Fn)
        assert isinstance(x.body, ast.Fn)
        assert isinstance(x.body.body, ast.Ref)
        self.assertNotEqual(x.param.id, x.body.body.name.id)
        self.assertEqual(x.body.param.id, x.body.body.name.id)

    def test_resolve_expr_function_failed(self):
        with self.assertRaises(ast.UndefinedVariableError) as e:
            resolve_expr("fun a => b")
        n, loc = e.exception.args
        self.assertEqual(9, loc)
        self.assertEqual("b", n.text)

    def test_resolve_expr_function_type(self):
        x = resolve_expr("{a: Type} -> (b: Type) -> a")
        assert isinstance(x, ast.FnType)
        assert isinstance(x.ret, ast.FnType)
        assert isinstance(x.ret.ret, ast.Ref)
        self.assertEqual(x.param.name.id, x.ret.ret.name.id)
        self.assertNotEqual(x.ret.param.name.id, x.ret.ret.name.id)

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

    def test_resolve_expr_placeholder(self):
        resolve_expr("{a: Type} -> (b: Type) -> _")
