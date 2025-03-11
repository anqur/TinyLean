from pathlib import Path
from unittest import TestCase

from .. import ast, ir


def nat_to_int(v: ir.IR):
    n = 0
    while True:
        if isinstance(v, ir.Fn):
            v = v.body
        else:
            break
    while True:
        if isinstance(v, ir.Call):
            assert isinstance(v.callee, ir.Ref)
            assert v.callee.name.text == "S"
            v = v.arg
            n += 1
        else:
            assert isinstance(v, ir.Ref)
            assert v.name.text == "Z"
            break
    return n


class TestMain(TestCase):
    def test_nat(self):
        _, _, _, _3, _6, _9 = ast.check_string(
            """
            def Nat: Type :=
                (T: Type) -> (S: (n: T) -> T) -> (Z: T) -> T

            def add (a: Nat) (b: Nat): Nat :=
                fun T S Z => (a T S) (b T S Z)

            def mul (a: Nat) (b: Nat): Nat :=
                fun T S Z => (a T) (b T S) Z

            def _3: Nat := fun T S Z => S (S (S Z))

            def _6: Nat := add _3 _3

            def _9: Nat := mul _3 _3
            """
        )
        self.assertEqual(3, nat_to_int(_3.body))
        self.assertEqual(6, nat_to_int(_6.body))
        self.assertEqual(9, nat_to_int(_9.body))

    def test_leibniz_equality(self):
        ast.check_string(
            """
            def Eq (T: Type) (a: T) (b: T): Type :=
                (p: (v: T) -> Type) -> (pa: p a) -> p b

            def refl (T: Type) (a: T): Eq T a a :=
                fun p pa => pa

            def sym (T: Type) (a: T) (b: T) (p: Eq T a b): Eq T b a :=
                (p (fun b => Eq T b a)) (refl T a)

            def A: Type := Type

            def B: Type := Type

            def lemma: Eq Type A B := refl Type A

            def theorem (p: Eq Type A B): Eq Type B A := sym Type A B lemma
            """
        )

    def test_leibniz_equality_failed(self):
        with self.assertRaises(ast.TypeMismatchError) as e:
            ast.check_string(
                """
                def Eq (T: Type) (a: T) (b: T): Type := (p: (v: T) -> Type) -> (pa: p a) -> p b
                def refl (T: Type) (a: T): Eq T a a := fun p => fun pa => pa
                def A: Type := (a: Type) -> Type
                def B: Type := (a: (b: Type) -> Type) -> Type
                def _: Eq Type A B := refl Type A
                /-                    ^~~^ failed here -/
                """
            )
        want, got, loc = e.exception.args
        self.assertEqual(323, loc)
        self.assertEqual(
            "(p: (v: Type) → Type) → (pa: (p (a: Type) → Type)) → (p (a: (b: Type) → Type) → Type)",
            str(want),
        )
        self.assertEqual(
            "(p: (v: Type) → Type) → (pa: (p (a: Type) → Type)) → (p (a: Type) → Type)",
            str(got),
        )

    def test_markdown(self):
        results = ast.check_string(
            """\
# Heading 1

```lean
def Eq (T: Type) (a: T) (b: T): Type := (p: (v: T) -> Type) -> (pa: p a) -> p b

def refl (T: Type) (a: T): Eq T a a := fun p => fun pa => pa
```

```lean
def sym (T: Type) (a: T) (b: T) (p: Eq T a b): Eq T b a := (p (fun b => Eq T b a)) (refl T a)
```

```lean4
def A: Type := Type
```

```python
print("Hello, world!")
```

```
Broken code.
```````

Footer.
            """,
            True,
        )
        self.assertEqual(3, len(results))
        eq, refl, sym = results
        self.assertEqual("Eq", eq.name.text)
        self.assertEqual("refl", refl.name.text)
        self.assertEqual("sym", sym.name.text)

    def test_readme(self):
        p = Path(__file__).parent / ".." / ".." / ".." / ".github" / "README.md"
        with open(p) as f:
            results = ast.check_string(f.read(), True)
        self.assertGreater(len(results), 1)

    def test_example(self):
        ast.check_string(
            """
            def T: Type := Type
            example: Type := T
            """
        )

    def test_leibniz_equality_implicit(self):
        ast.check_string(
            """
            def Eq {T: Type} (a: T) (b: T): Type :=
                (p: (v: T) -> Type) -> (pa: p a) -> p b

            def refl {T: Type} (a: T): Eq a a :=
                fun p pa => pa

            def sym {T: Type} (a: T) (b: T) (p: Eq a b): Eq b a :=
                (p (fun b => Eq b a)) (refl a)

            def A: Type := Type

            def B: Type := Type

            def lemma: Eq A B := refl A

            def theorem (p: Eq A B): Eq B A := sym A B lemma
            """
        )

    def test_operator_overloading(self):
        ast.check_string(
            """
            inductive N where
            | Z
            | S (n: N)
            open N

            def addN (a: N) (b: N): N :=
              match a with
              | Z => b
              | S pred => S (addN pred b)

            class Add {T: Type} where
              add: (a: T) -> (b: T) -> T
            open Add

            instance: Add (T := N)
            where
              add := addN

            def f := (S Z) + (S Z)
            """
        )
