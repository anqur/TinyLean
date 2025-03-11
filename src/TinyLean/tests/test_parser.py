from unittest import TestCase

from pyparsing import ParseException

from . import parse
from .. import (
    ast,
    Name,
    grammar,
    Param,
    Decl,
    Def,
    Example,
    Data,
    Ctor,
    Class,
    Instance,
)


class TestParser(TestCase):
    def test_fresh(self):
        self.assertNotEqual(Name("i").id, Name("j").id)

    def test_parse_name(self):
        x = parse(grammar.name, "  hello")[0]
        assert isinstance(x, Name)
        self.assertEqual("hello", x.text)

    def test_parse_name_unbound(self):
        x = parse(grammar.name, "_")[0]
        self.assertTrue(x.is_unbound())

    def test_parse_type(self):
        x = parse(grammar.type_, "  Type")[0]
        assert isinstance(x, ast.Type)
        self.assertEqual(2, x.loc)

    def test_parse_reference(self):
        x = parse(grammar.ref, "  hello")[0]
        assert isinstance(x, ast.Ref)
        self.assertEqual(2, x.loc)
        self.assertEqual("hello", x.name.text)

    def test_parse_paren_expr(self):
        x = parse(grammar.p_expr, "(hello)")[0]
        assert isinstance(x, ast.Ref)
        self.assertEqual(1, x.loc)
        self.assertEqual("hello", x.name.text)

    def test_parse_implicit_param(self):
        x = parse(grammar.i_param, " {a: b}")[0]
        assert isinstance(x, Param)
        self.assertTrue(x.is_implicit)
        self.assertEqual("a", x.name.text)
        assert isinstance(x.type, ast.Ref)
        self.assertEqual(5, x.type.loc)

    def test_parse_explicit_param(self):
        x = parse(grammar.e_param, " (a : Type)")[0]
        assert isinstance(x, Param)
        self.assertFalse(x.is_implicit)
        self.assertEqual("a", x.name.text)
        assert isinstance(x.type, ast.Type)
        self.assertEqual(6, x.type.loc)

    def test_parse_call(self):
        x = parse(grammar.call, "a b")[0]
        assert isinstance(x, ast.Call)
        self.assertEqual(0, x.loc)
        assert isinstance(x.callee, ast.Ref)
        self.assertEqual(0, x.callee.loc)
        self.assertEqual("a", x.callee.name.text)
        self.assertEqual(2, x.arg.loc)
        assert isinstance(x.arg, ast.Ref)
        self.assertEqual("b", x.arg.name.text)

    def test_parse_call_paren(self):
        x = parse(grammar.call, "(a) b (Type)")[0]
        assert isinstance(x, ast.Call)
        self.assertEqual(0, x.loc)
        assert isinstance(x.callee, ast.Call)
        assert isinstance(x.callee.callee, ast.Ref)
        self.assertEqual(1, x.callee.callee.loc)
        self.assertEqual("a", x.callee.callee.name.text)
        assert isinstance(x.callee.arg, ast.Ref)
        self.assertEqual(4, x.callee.arg.loc)
        self.assertEqual("b", x.callee.arg.name.text)
        assert isinstance(x.arg, ast.Type)
        self.assertEqual(7, x.arg.loc)

    def test_parse_call_paren_function(self):
        x = parse(grammar.call, "(fun _ => Type) Type")[0]
        assert isinstance(x, ast.Call)
        self.assertEqual(0, x.loc)
        assert isinstance(x.callee, ast.Fn)
        self.assertEqual(1, x.callee.loc)
        self.assertTrue(x.callee.param.is_unbound())
        assert isinstance(x.callee.body, ast.Type)
        self.assertEqual(10, x.callee.body.loc)
        assert isinstance(x.arg, ast.Type)
        self.assertEqual(16, x.arg.loc)

    def test_parse_function_type(self):
        x = parse(grammar.fn_type, "  (a : Type) -> a")[0]
        assert isinstance(x, ast.FnType)
        assert isinstance(x.param, Param)
        self.assertEqual("a", x.param.name.text)
        assert isinstance(x.param.type, ast.Type)
        self.assertEqual(7, x.param.type.loc)
        assert isinstance(x.ret, ast.Ref)
        self.assertEqual("a", x.ret.name.text)
        self.assertEqual(16, x.ret.loc)

    def test_parse_function_type_long(self):
        x = parse(grammar.fn_type, " {a : Type} -> (b: Type) -> a")[0]
        assert isinstance(x, ast.FnType)
        assert isinstance(x.param, Param)
        self.assertEqual("a", x.param.name.text)
        assert isinstance(x.param.type, ast.Type)
        self.assertEqual(6, x.param.type.loc)
        assert isinstance(x.ret, ast.FnType)
        assert isinstance(x.ret.param, Param)
        self.assertEqual("b", x.ret.param.name.text)
        assert isinstance(x.ret.param.type, ast.Type)
        self.assertEqual(19, x.ret.param.type.loc)
        assert isinstance(x.ret.ret, ast.Ref)
        self.assertEqual("a", x.ret.ret.name.text)
        self.assertEqual(28, x.ret.ret.loc)

    def test_parse_function(self):
        x = parse(grammar.fn, "  fun a => a")[0]
        assert isinstance(x, ast.Fn)
        self.assertEqual(2, x.loc)
        assert isinstance(x.param, Name)
        self.assertEqual("a", x.param.text)
        assert isinstance(x.body, ast.Ref)
        self.assertEqual("a", x.body.name.text)
        self.assertEqual(11, x.body.loc)

    def test_parse_function_long(self):
        x = parse(grammar.fn, "   fun a => fun b => a b")[0]
        assert isinstance(x, ast.Fn)
        self.assertEqual(3, x.loc)
        assert isinstance(x.param, Name)
        self.assertEqual("a", x.param.text)
        assert isinstance(x.body, ast.Fn)
        self.assertEqual(12, x.body.loc)
        assert isinstance(x.body.param, Name)
        self.assertEqual("b", x.body.param.text)
        assert isinstance(x.body.body, ast.Call)
        self.assertEqual(21, x.body.body.loc)
        assert isinstance(x.body.body.callee, ast.Ref)
        self.assertEqual("a", x.body.body.callee.name.text)
        assert isinstance(x.body.body.arg, ast.Ref)
        self.assertEqual("b", x.body.body.arg.name.text)

    def test_parse_function_multi(self):
        x = parse(grammar.fn, "  fun c d => c d")[0]
        assert isinstance(x, ast.Fn)
        self.assertEqual(2, x.loc)
        assert isinstance(x.param, Name)
        self.assertEqual("c", x.param.text)
        assert isinstance(x.body, ast.Fn)
        self.assertEqual(2, x.body.loc)
        assert isinstance(x.body.param, Name)
        self.assertEqual("d", x.body.param.text)

    def test_parse_definition_constant(self):
        x = parse(grammar.def_, "  def f : Type := Type")[0]
        assert isinstance(x, Def)
        self.assertEqual(6, x.loc)
        self.assertEqual("f", x.name.text)
        self.assertEqual(0, len(x.params))
        assert isinstance(x.ret, ast.Type)
        self.assertEqual(10, x.ret.loc)
        assert isinstance(x.body, ast.Type)
        self.assertEqual(18, x.body.loc)

    def test_parse_definition(self):
        x = parse(grammar.def_, "  def f {a: Type} (b: Type): Type := a")[0]
        assert isinstance(x, Def)
        self.assertEqual(6, x.loc)
        self.assertEqual("f", x.name.text)
        assert isinstance(x.params, list)
        self.assertEqual(2, len(x.params))
        assert isinstance(x.params[0], ast.Param)
        self.assertTrue(x.params[0].is_implicit)
        self.assertEqual("a", x.params[0].name.text)
        assert isinstance(x.params[0].type, ast.Type)
        self.assertEqual(12, x.params[0].type.loc)
        assert isinstance(x.params[1], ast.Param)
        self.assertFalse(x.params[1].is_implicit)
        self.assertEqual("b", x.params[1].name.text)
        assert isinstance(x.params[1].type, ast.Type)
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
        assert isinstance(x[0], Decl)
        self.assertEqual("a", x[0].name.text)
        assert isinstance(x[1], Decl)
        self.assertEqual("b", x[1].name.text)

    def test_parse_example(self):
        x = parse(grammar.example, "  example: Type := Type")[0]
        assert isinstance(x, Example)
        self.assertEqual(2, x.loc)
        self.assertEqual(0, len(x.params))
        assert isinstance(x.ret, ast.Type)
        assert isinstance(x.body, ast.Type)

    def test_parse_placeholder(self):
        x = parse(grammar.fn, " fun _ => _")[0]
        assert isinstance(x, ast.Fn)
        self.assertTrue(x.param.is_unbound())
        assert isinstance(x.body, ast.Placeholder)
        self.assertEqual(10, x.body.loc)

    def test_parse_return_type(self):
        x = parse(grammar.return_type, ": Type")[0]
        assert isinstance(x, ast.Type)
        self.assertEqual(2, x.loc)

    def test_parse_return_placeholder(self):
        x = parse(grammar.return_type, "")[0]
        assert isinstance(x, ast.Placeholder)
        self.assertFalse(x.is_user)

    def test_parse_definition_no_return(self):
        x = parse(grammar.def_, "def a := Type")[0]
        assert isinstance(x, Def)
        assert isinstance(x.ret, ast.Placeholder)
        self.assertFalse(x.ret.is_user)

    def test_parse_call_implicit(self):
        x = parse(grammar.call, "a ( T := Nat )")[0]
        assert isinstance(x, ast.Call)
        assert isinstance(x.callee, ast.Ref)
        self.assertEqual("a", x.callee.name.text)
        self.assertEqual("T", x.implicit)
        assert isinstance(x.arg, ast.Ref)
        self.assertEqual("Nat", x.arg.name.text)

    def test_parse_call_explicit(self):
        x = parse(grammar.call, "a b")[0]
        assert isinstance(x, ast.Call)
        assert isinstance(x.callee, ast.Ref)
        self.assertEqual("a", x.callee.name.text)
        self.assertFalse(x.implicit)
        assert isinstance(x.arg, ast.Ref)
        self.assertEqual("b", x.arg.name.text)

    def test_parse_definition_call_implicit(self):
        x = parse(
            grammar.def_,
            """
            def f: Type := a ( 
                T := Nat 
            ) b
            """,
        )[0]
        assert isinstance(x, Def)
        assert isinstance(x.body, ast.Call)
        assert isinstance(x.body.callee, ast.Call)
        assert isinstance(x.body.callee.callee, ast.Ref)
        self.assertEqual("a", x.body.callee.callee.name.text)
        assert isinstance(x.body.callee.arg, ast.Ref)
        self.assertEqual("Nat", x.body.callee.arg.name.text)
        self.assertEqual("T", x.body.callee.implicit)
        assert isinstance(x.body.arg, ast.Ref)
        self.assertEqual("b", x.body.arg.name.text)

    def test_parse_datatype_empty(self):
        x = parse(
            grammar.data,
            """
            inductive Void where
            open Void
            """,
        )[0]
        assert isinstance(x, Data)
        self.assertEqual("Void", x.name.text)
        self.assertEqual(0, len(x.params))
        self.assertEqual(0, len(x.ctors))

    def test_parse_datatype_empty_failed(self):
        with self.assertRaises(ParseException) as e:
            parse(grammar.data, "inductive Foo where open Bar")
        self.assertIn("open and datatype name mismatch", str(e.exception))

    def test_parse_datatype_ctors(self):
        x = parse(
            grammar.data,
            """
            inductive D {T: Type} (U: Type) where
            | A
            | B {X: Type} (Y: Type) (U := Type)
            | C (T := Type)
            open D
            """,
        )[0]
        assert isinstance(x, Data)
        self.assertEqual("D", x.name.text)
        self.assertEqual(2, len(x.params))
        self.assertEqual("T", x.params[0].name.text)
        self.assertEqual("U", x.params[1].name.text)
        self.assertEqual(3, len(x.ctors))
        a, b, c = x.ctors
        assert isinstance(a, Ctor)
        self.assertEqual("A", a.name.text)
        self.assertEqual(0, len(a.params))
        assert isinstance(b, Ctor)
        self.assertEqual("B", b.name.text)
        self.assertEqual(2, len(b.params))
        self.assertEqual(1, len(b.ty_args))
        self.assertEqual("U", b.ty_args[0][0].name.text)
        assert isinstance(c, Ctor)
        self.assertEqual("C", c.name.text)
        self.assertEqual(0, len(c.params))
        self.assertEqual(1, len(c.ty_args))
        self.assertEqual("T", c.ty_args[0][0].name.text)

    def test_parse_expr_nomatch(self):
        x = parse(grammar.nomatch, "nomatch x")[0]
        assert isinstance(x, ast.Nomatch)
        assert isinstance(x.arg, ast.Ref)
        self.assertEqual("x", x.arg.name.text)

    def test_parse_expr_case(self):
        x = parse(grammar.case, "| A a b => a")[0]
        assert isinstance(x, ast.Case)
        self.assertEqual(2, x.loc)
        self.assertEqual("A", x.ctor.name.text)
        self.assertEqual(2, len(x.params))
        self.assertEqual("a", x.params[0].text)
        self.assertEqual("b", x.params[1].text)
        assert isinstance(x.body, ast.Ref)
        self.assertEqual("a", x.body.name.text)

    def test_parse_expr_match(self):
        x = parse(
            grammar.match,
            """
            match Type with
            | A a => a
            | B b => b
            | _ => x /- not actually a default case -/
            """,
        )[0]
        assert isinstance(x, ast.Match)
        assert isinstance(x.arg, ast.Type)
        self.assertEqual(3, len(x.cases))
        self.assertTrue(x.cases[2].ctor.name.is_unbound())

    def test_parse_class_param(self):
        x = parse(grammar.c_param, "[p: GAdd Type]")[0]
        assert isinstance(x, Param)
        self.assertEqual("p", x.name.text)
        assert isinstance(x.type, ast.Call)
        assert isinstance(x.type.callee, ast.Ref)
        self.assertEqual("GAdd", x.type.callee.name.text)
        assert isinstance(x.type.arg, ast.Type)
        self.assertTrue(x.is_implicit)

    def test_parse_class_empty(self):
        x = parse(
            grammar.class_,
            """
            class A where
            open A
            """,
        )[0]
        assert isinstance(x, Class)
        self.assertEqual("A", x.name.text)
        self.assertEqual(0, len(x.params))
        self.assertEqual(0, len(x.fields))

    def test_parse_class_empty_failed(self):
        with self.assertRaises(ParseException) as e:
            parse(grammar.class_, "class A where open B")
        self.assertIn("open and class name mismatch", str(e.exception))

    def test_parse_class_fields(self):
        x = parse(
            grammar.class_,
            """
            class Op {T: Type} where
                add: (a: T) -> (b: T) -> T
                mul: (a: T) -> (b: T) -> T
            open Op
            """,
        )[0]
        assert isinstance(x, Class)
        self.assertEqual(1, len(x.params))
        self.assertEqual("T", x.params[0].name.text)
        self.assertEqual("Op", x.name.text)
        self.assertEqual(2, len(x.fields))
        self.assertEqual("add", x.fields[0].name.text)
        assert isinstance(x.fields[0].type, ast.FnType)
        self.assertEqual("mul", x.fields[1].name.text)
        assert isinstance(x.fields[1].type, ast.FnType)

    def test_parse_instance_empty(self):
        x = parse(grammar.inst, "instance : Monad A\nwhere")[0]
        assert isinstance(x, Instance)
        assert isinstance(x.type, ast.Call)
        assert isinstance(x.type.callee, ast.Ref)
        self.assertEqual("Monad", x.type.callee.name.text)
        assert isinstance(x.type.arg, ast.Ref)
        self.assertEqual("A", x.type.arg.name.text)
        self.assertEqual(0, len(x.fields))

    def test_parse_instance_fields(self):
        x = parse(
            grammar.inst,
            """
            instance : AddOp T
            where
                add := (a: T) -> (b: T) -> T
            """,
        )[0]
        assert isinstance(x, Instance)
        self.assertEqual(1, len(x.fields))
        f = x.fields[0]
        assert isinstance(f, tuple)
        n, v = f
        assert isinstance(n, ast.Ref)
        self.assertEqual("add", n.name.text)
        assert isinstance(v, ast.FnType)
