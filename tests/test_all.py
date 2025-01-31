from unittest import TestCase

from TinyLean.grammar import definition, program
from TinyLean import Ident


class TestIdent(TestCase):
    def test_fresh(self):
        i = Ident.fresh("i")
        j = Ident.fresh("j")
        self.assertLess(i.id, j.id)


class TestGrammar(TestCase):
    def test_parse_oneline_definition(self):
        definition.parse_string("def f (a : Type) : Type ≔ a\n", parse_all=True)

    def test_parse_oneline_definition_white(self):
        definition.parse_string(" def t := Type \n ", parse_all=True)

    def test_parse_multiline_definition(self):
        program.parse_string(
            """
            /-- foo -/
            def foo
                {a : Type}
                (b: Type)
                : Type
                :=
                b
            """,
            parse_all=True,
        )

    def test_parse_program_empty(self):
        program.parse_string("", parse_all=True)

    def test_parse_program_definitions(self):
        program.parse_string(
            """
            def f1 : Type := Type
            def f2 (a : Type) : Type :=
                a

            /- leave some space here -/



            def f3 (a : Type) : Type :=

                a
            """,
            parse_all=True,
        )
