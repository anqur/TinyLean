from unittest import TestCase

from . import parse
from ..grammar import definition, program, expr, markdown


class TestGrammar(TestCase):
    def test_parse_expr_function_type(self):
        parse(expr, "{a: Type} -> (b: Type) -> a")
        parse(expr, "{a: Type} → (b: Type) → a")

    def test_parse_expr_paren_expr(self):
        parse(expr, "(((Type)))")

    def test_parse_expr_function(self):
        parse(expr, "fun _ => Type")
        parse(expr, "λ _ ↦ Type")
        parse(expr, "fun a => fun b => a")

    def test_parse_expr_call(self):
        parse(expr, "a b")
        parse(expr, "a b c")
        parse(expr, "a b c d")
        parse(expr, "(fun _ => Type) Type")
        parse(expr, "fun a => a b")

    def test_parse_oneline_definition(self):
        parse(definition, "def f (a : Type) : Type ≔ a")

    def test_parse_oneline_definition_white(self):
        parse(definition, " def t : Type := Type \n ")

    def test_parse_multiline_definition(self):
        parse(
            program,
            """
            /-- foo -/
            def foo
                {a : Type}
                (b: Type)
                : Type
                :=
                b
            """,
        )

    def test_parse_program_empty(self):
        parse(program, "")

    def test_parse_program_definitions(self):
        parse(
            program,
            """
            def f1 : Type := Type
            def f2 (a : Type) : Type :=
                a

            /- leave some space here -/



            def f3 (a : Type) : Type :=

                a
            """,
        )

    def test_parse_markdown(self):
        results = list(
            markdown.scan_string(
                """\
# Heading 1

```lean
def b: Type := Type
```

Invalid Lean program:

```lean
def a: Type := a b
    c
/-  ^~~~~ syntax error -/
```

Other language:

```python
print("Hello, world!")
```

Wrong Markdown syntax:

```lean
def c: Type := Type
````

Footer.
            """,
            )
        )
        self.assertEqual(1, len(results))
