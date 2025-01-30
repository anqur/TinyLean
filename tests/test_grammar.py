import unittest

from TinyLean.grammar import definition, program


class TestGrammar(unittest.TestCase):
    def test_parse_oneline_definition(self):
        definition.parse_string("def foo (a : Type) : Type := a\n", parse_all=True)

    def test_parse_oneline_definition_white(self):
        definition.parse_string(" def foo (a : Type) : Type := a \n ", parse_all=True)

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
            def f1 (a : Type) : Type := a
            def f2 (a : Type) : Type :=
                a

            /- leave some space here -/



            def f3 (a : Type) : Type :=

                a
            """,
            parse_all=True,
        )
