from unittest import TestCase

from . import resolve_expr, resolve, resolve_md
from .. import ast, Data


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
        self.assertEqual("b", n)

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
        self.assertEqual("c", n)

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
        self.assertEqual("c", n)

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
        self.assertEqual("f0", n)

    def test_resolve_md(self):
        resolve_md(
            """\
# Heading

```lean
def a := Type
```

Some text.

```lean
def b := a
```

Footer.
            """
        )

    def test_resolve_expr_placeholder(self):
        resolve_expr("{a: Type} -> (b: Type) -> _")

    def test_resolve_datatype_empty(self):
        resolve("inductive Void where open Void")

    def test_resolve_datatype_nat(self):
        x = resolve(
            """
            inductive N where
            | Z
            | S (n: N)
            open N
            """
        )[0]
        assert isinstance(x, Data)
        a = x.name.id
        b_typ = x.ctors[1].params[0].type
        assert isinstance(b_typ, ast.Ref)
        b = b_typ.name.id
        self.assertEqual(a, b)

    def test_resolve_datatype_maybe(self):
        x = resolve(
            """
            inductive Maybe (A: Type) where
            | Nothing
            | Just (a: A)
            open Maybe
            """
        )[0]
        assert isinstance(x, Data)
        a = x.params[0].name.id
        b_typ = x.ctors[1].params[0].type
        assert isinstance(b_typ, ast.Ref)
        b = b_typ.name.id
        self.assertEqual(a, b)

    def test_resolve_datatype_vec(self):
        resolve(
            """
            inductive N where
            | Z
            | S (n: N)
            open N

            inductive Vec (A : Type) (n : N) where
            | Nil (n := Z)
            | Cons {m: N} (a: A) (v: Vec A m) (n := S m)
            open Vec
            """
        )

    def test_resolve_datatype_duplicate(self):
        with self.assertRaises(ast.DuplicateVariableError) as e:
            resolve("inductive A where | A open A")
        name, loc = e.exception.args
        self.assertEqual("A", name)
        self.assertEqual(20, loc)

    def test_resolve_match(self):
        resolve(
            """
            inductive A where | AA (T: Type) open A
            example (x: A) :=
              match x with
              | A t => t
            """
        )

    def test_resolve_match_failed(self):
        with self.assertRaises(ast.UndefinedVariableError) as e:
            resolve(
                """
                inductive A where | AA open A
                example (x: A) :=
                  match x with
                  | A => b
                """
            )
        name, loc = e.exception.args
        self.assertEqual("b", name)
        self.assertEqual(137, loc)

    def test_resolve_class(self):
        resolve(
            """
            class A (T: Type) where
                a: T
            open A
            example := a
            """
        )

    def test_resolve_instance(self):
        resolve(
            """
            inductive Void where open Void

            class A (T: Type) where
                a: T
            open A

            instance: A Void
            where
                a := Type
            """
        )
