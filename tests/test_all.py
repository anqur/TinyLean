from unittest import TestCase

from TinyLean.grammar import definition, program
from TinyLean import Ident


class TestIdent(TestCase):
    def test_fresh(self):
        self.assertLess(Ident.fresh("i").id, Ident.fresh("j").id)


parse = lambda g, text: g.parse_string(text, parse_all=True)


class TestGrammar(TestCase):
    def test_parse_oneline_definition(self):
        parse(definition, "def f (a : Type) : Type ≔ a\n")

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
