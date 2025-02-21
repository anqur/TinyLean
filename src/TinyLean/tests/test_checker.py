from unittest import TestCase

from . import resolve_expr
from .. import ast, Name, Param, ir, Data, Example

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
        with self.assertRaises(ast.UndefinedVariableError) as e:
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

    def test_check_program_call_mixed_implicit(self):
        ast.check_string(
            """
            def f (T: Type) {U: Type}: Type := U
            /- Cannot insert placeholders for an implicit function type. -/
            example: {U: Type} -> Type := f Type
            """
        )

    def test_check_program_datatype_nat(self):
        x, _, _, _2 = ast.check_string(
            """
            inductive N where
            | Z
            | S (n: N)
            open N

            example: N := Z
            example: N := S Z
            example: N := S (S Z)
            """
        )
        assert isinstance(x, Data)
        self.assertEqual(2, len(x.ctors))

        n_v, n_ty = ir.from_data(x)
        self.assertEqual("N", str(n_v))
        self.assertEqual("Type", str(n_ty))

        z_v, z_ty = ir.from_ctor(x.ctors[0], x)
        self.assertEqual("N.Z", str(z_v))
        self.assertEqual("N", str(z_ty))

        s_v, s_ty = ir.from_ctor(x.ctors[1], x)
        self.assertEqual("λ (n: N) ↦ (N.S n)", str(s_v))
        self.assertEqual("(n: N) → N", str(s_ty))

        assert isinstance(_2, Example)
        self.assertEqual("(N.S (N.S N.Z))", str(_2.body))

    def test_check_program_datatype_nat_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string(
                """
                inductive N where
                | Z
                | S (n: N)
                open N

                example: Type := Z
                """
            )
        want, got, loc = e.exception.args
        self.assertEqual("Type", str(want))
        self.assertEqual("N", str(got))
        self.assertEqual(139, loc)

    def test_check_program_datatype_maybe(self):
        x = ast.check_string(
            """
            inductive Maybe (A: Type) where
            | Nothing
            | Just (a: A)
            open Maybe

            example: Maybe Type := Nothing
            example: Maybe Type := Just Type
            """
        )[0]
        assert isinstance(x, Data)
        self.assertEqual(2, len(x.ctors))

        maybe_v, maybe_ty = ir.from_data(x)
        self.assertEqual("λ (A: Type) ↦ (Maybe A)", str(maybe_v))
        self.assertEqual("(A: Type) → Type", str(maybe_ty))

        nothing_v, nothing_ty = ir.from_ctor(x.ctors[0], x)
        self.assertEqual("λ {A: Type} ↦ Maybe.Nothing", str(nothing_v))
        self.assertEqual("{A: Type} → (Maybe A)", str(nothing_ty))

        just_v, just_ty = ir.from_ctor(x.ctors[1], x)
        self.assertEqual("λ {A: Type} ↦ λ (a: A) ↦ (Maybe.Just a)", str(just_v))
        self.assertEqual("{A: Type} → (a: A) → (Maybe A)", str(just_ty))

        assert isinstance(just_v, ir.Fn)
        assert isinstance(just_v.body, ir.Fn)
        assert isinstance(just_v.body.body, ir.Ctor)
        just_arg = just_v.body.body.args[0]
        assert isinstance(just_arg, ir.Ref)
        self.assertEqual(just_v.body.param.name.id, just_arg.name.id)

        assert isinstance(just_ty, ir.FnType)
        assert isinstance(just_ty.ret, ir.FnType)
        assert isinstance(just_ty.ret.ret, ir.Data)
        just_ty_arg = just_ty.ret.ret.args[0]
        assert isinstance(just_ty_arg, ir.Ref)
        self.assertEqual(just_ty.param.name.id, just_ty_arg.name.id)

    def test_check_program_datatype_maybe_unsolved(self):
        with self.assertRaises(ast.UnsolvedPlaceholderError) as e:
            ast.check_string(
                """
                inductive Maybe (A: Type) where
                | Nothing
                | Just (a: A)
                open Maybe

                example := Nothing
                """
            )
        name, ctx, ty, loc = e.exception.args
        self.assertTrue(name.startswith("?m"))
        self.assertEqual(1, len(ctx))
        assert isinstance(ty, ir.Type)
        self.assertEqual(160, loc)

    def test_check_program_datatype_maybe_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string(
                """
                inductive Maybe (A: Type) where
                | Nothing
                | Just (a: A)
                open Maybe

                inductive A where | AA open A
                inductive B where | BB open B
                example: Maybe B := Just AA
                """
            )
        want, got, _ = e.exception.args
        self.assertEqual("(Maybe B)", str(want))
        self.assertEqual("(Maybe A)", str(got))

    def test_check_program_datatype_vec(self):
        x = ast.check_string(
            """
            inductive N where
            | Z
            | S (n: N)
            open N

            inductive Vec (A: Type) (n: N) where
            | Nil (n := Z)
            | Cons {m: N} (a: A) (v: Vec A m) (n := S m)
            open Vec

            /- This will emit some "dirty" placeholders. -/
            def v1: Vec N (S Z) := Cons Z Nil
            """
        )[1]
        assert isinstance(x, Data)
        self.assertEqual(2, len(x.ctors))

        vec_v, vec_ty = ir.from_data(x)
        self.assertEqual("λ (A: Type) ↦ λ (n: N) ↦ (Vec A n)", str(vec_v))
        self.assertEqual("(A: Type) → (n: N) → Type", str(vec_ty))

        nil_v, nil_ty = ir.from_ctor(x.ctors[0], x)
        self.assertEqual("λ {A: Type} ↦ Vec.Nil", str(nil_v))
        self.assertEqual("{A: Type} → (Vec A N.Z)", str(nil_ty))

        cons_v, cons_ty = ir.from_ctor(x.ctors[1], x)
        self.assertEqual(
            "λ {A: Type} ↦ λ {m: N} ↦ λ (a: A) ↦ λ (v: (Vec A m)) ↦ (Vec.Cons m a v)",
            str(cons_v),
        )
        self.assertEqual(
            "{A: Type} → {m: N} → (a: A) → (v: (Vec A m)) → (Vec A (N.S m))",
            str(cons_ty),
        )

    def test_check_program_ctor_eq(self):
        ast.check_string(
            """
            def Eq {T: Type} (a: T) (b: T): Type := (p: (v: T) -> Type) -> (pa: p a) -> p b
            def refl {T: Type} (a: T): Eq a a := fun p pa => pa
            inductive A where | AA open A
            example: Eq AA AA := refl AA
            """
        )

    def test_check_program_nomatch(self):
        _, _, e = ast.check_string(
            """
            inductive Bottom where open Bottom
            def elimBot {A: Type} (x: Bottom): A := nomatch x
            example (x: Bottom): Type := elimBot x
            """
        )
        assert isinstance(e, Example)
        assert isinstance(e.body, ir.Nomatch)
        self.assertEqual("nomatch", str(e.body))

    def test_check_program_nomatch_non_data_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string("example := nomatch Type")
        want, got, loc = e.exception.args
        self.assertEqual("datatype", str(want))
        self.assertEqual("Type", str(got))
        self.assertEqual(19, loc)

    def test_check_program_nomatch_non_empty_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string(
                """
                inductive A where | AA open A
                example := nomatch AA
                """
            )
        want, got, loc = e.exception.args
        self.assertEqual("empty datatype", str(want))
        self.assertEqual("A", str(got))
        self.assertEqual(82, loc)

    def test_check_program_nomatch_eq(self):
        ast.check_string(
            """
            def Eq {T: Type} (a: T) (b: T): Type := (p: (v: T) -> Type) -> (pa: p a) -> p b
            def refl {T: Type} (a: T): Eq a a := fun p pa => pa
            inductive Bottom where open Bottom
            def a (x: Bottom): Type := nomatch x
            def b (x: Bottom): Type := nomatch x
            example (x: Bottom): Eq (a x) (b x) := refl (a x)
            """
        )

    def test_check_program_match(self):
        _, _, e = ast.check_string(
            """
            inductive V where
            | A (x: Type) (y: Type)
            | B (x: Type)
            open V

            def f (v: V): Type :=
            match v with
            | A x y => x
            | B x => x

            example := f (A Type Type)
            """
        )
        assert isinstance(e, Example)
        assert isinstance(e.body, ir.Type)
