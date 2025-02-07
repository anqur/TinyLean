from dataclasses import dataclass, field
from functools import reduce

from . import Ident, Param, Declaration, ir, grammar


@dataclass(frozen=True)
class Node:
    loc: int


@dataclass(frozen=True)
class Type(Node): ...


@dataclass(frozen=True)
class Ref(Node):
    name: Ident


@dataclass(frozen=True)
class FnType(Node):
    param: Param[Node]
    ret: Node


@dataclass(frozen=True)
class Fn(Node):
    param: Ident
    body: Node


@dataclass(frozen=True)
class Call(Node):
    callee: Node
    arg: Node


grammar.IDENT.set_parse_action(lambda r: Ident.fresh(r[0]))
grammar.TYPE.set_parse_action(lambda l, r: Type(l))
grammar.REF.set_parse_action(lambda l, r: Ref(l, r[0][0]))
grammar.paren_expr.set_parse_action(lambda r: r[0][0])
grammar.implicit_param.set_parse_action(lambda r: Param(r[0], r[1][0], True))
grammar.explicit_param.set_parse_action(lambda r: Param(r[0], r[1][0], False))
grammar.function_type.set_parse_action(lambda l, r: FnType(l, r[0][0], r[0][1][0]))
grammar.function.set_parse_action(lambda l, r: Fn(l, r[0][0], r[0][1][0]))
grammar.call.set_parse_action(
    lambda l, r: reduce(lambda a, b: Call(l, a, b), r[0][1:], r[0][0])
)
grammar.definition.set_parse_action(
    lambda r: Declaration(r[0].loc, r[0].name, list(r[1]), r[2][0], r[3][0])
)


class DuplicateVariableError(Exception): ...


class UndefinedVariableError(Exception): ...


@dataclass(frozen=True)
class NameResolver:
    locals: dict[str, Ident] = field(default_factory=dict)
    globals: dict[str, Ident] = field(default_factory=dict)

    def run(self, decls: list[Declaration[Node]]):
        return [self.decl(d) for d in decls]

    def decl(self, d: Declaration[Node]):
        params = []
        for p in d.params:
            self._insert_local(p.name)
            params.append(Param(p.name, self.expr(p.type), p.implicit))
        ret = self.expr(d.ret)
        body = self.expr(d.body)

        if not d.name.is_unbound():
            if d.name.text in self.globals:
                raise DuplicateVariableError(d.name, d.loc)
            self.globals[d.name.text] = d.name

        self.locals.clear()
        return Declaration(d.loc, d.name, params, ret, body)

    def expr(self, node: Node) -> Node:
        match node:
            case Ref(loc, v):
                try:
                    return Ref(loc, self.locals[v.text])
                except KeyError:
                    pass
                try:
                    return Ref(loc, self.globals[v.text])
                except KeyError:
                    raise UndefinedVariableError(v, loc)
            case FnType(loc, p, body):
                typ = self.expr(p.type)
                b = self._guard_local(p.name, body)
                return FnType(loc, Param(p.name, typ, p.implicit), b)
            case Fn(loc, v, body):
                b = self._guard_local(v, body)
                return Fn(loc, v, b)
            case Call(loc, f, x):
                return Call(loc, self.expr(f), self.expr(x))
            case Type(_):
                return node
        raise AssertionError(f"impossible: {node}")

    def _guard_local(self, v: Ident, node: Node):
        old = self._insert_local(v)
        ret = self.expr(node)
        if old:
            self._insert_local(old)
        else:
            del self.locals[v.text]
        return ret

    def _insert_local(self, v: Ident):
        old = None
        try:
            old = self.locals[v.text]
        except KeyError:
            pass
        self.locals[v.text] = v
        return old


class TypeMismatchError(Exception): ...


@dataclass(frozen=True)
class TypeChecker:
    globals: dict[int, Declaration[ir.IR]] = field(default_factory=dict)
    locals: dict[int, ir.IR] = field(default_factory=dict)

    def run(self, ds: list[Declaration[Node]]):
        return [self._run(d) for d in ds]

    def _run(self, d: Declaration[Node]) -> Declaration[ir.IR]:
        self.locals.clear()
        params = []
        for p in d.params:
            typ = self.check(p.type, ir.Type())
            params.append(Param(p.name, typ, p.implicit))
            self.locals[p.name.id] = typ
        ret = self.check(d.ret, ir.Type())
        body = self.check(d.body, ret)
        checked_def = Declaration(d.loc, d.name, params, ret, body)
        self.globals[d.name.id] = checked_def
        return checked_def

    def check(self, n: Node, typ: ir.IR) -> ir.IR:
        match n:
            case Fn(loc, v, body):
                match ir.inline(typ):
                    case ir.FnType(p, b):
                        body_type = ir.Inliner().run_with(p.name, ir.Ref(v), b)
                        param = Param(v, p.type, p.implicit)
                        return ir.Fn(param, self._check_with(param, body, body_type))
                    case want:
                        raise TypeMismatchError(str(want), "function", loc)
            case _:
                val, got = self.infer(n)
                got = ir.inline(got)
                want = ir.inline(typ)
                if ir.Converter(self.globals).eq(got, want):
                    return val
                raise TypeMismatchError(str(want), str(got), n.loc)

    def infer(self, n: Node) -> tuple[ir.IR, ir.IR]:
        match n:
            case Ref(_, v):
                try:
                    return ir.Ref(v), self.locals[v.id]
                except KeyError:
                    pass
                try:
                    d = self.globals[v.id]
                    return ir.definition_value(d), ir.signature_type(d)
                except KeyError:
                    raise AssertionError(f"impossible: {repr(v)}")
            case FnType(_, p, b):
                p_typ = self.check(p.type, ir.Type())
                inferred_p = Param(p.name, p_typ, p.implicit)
                b_val = self._check_with(inferred_p, b, ir.Type())
                return ir.FnType(inferred_p, b_val), ir.Type()
            case Call(_, f, x):
                f_tm, f_typ = self.infer(f)
                match f_typ:
                    case ir.FnType(p, b):
                        x_tm = self._check_with(p, x, p.type)
                        typ = ir.Inliner().run_with(p.name, x_tm, b)
                        val = ir.Inliner().apply(f_tm, x_tm)
                        return val, typ
                    case got:
                        raise TypeMismatchError("function", str(got), f.loc)
            case Type(_):
                return ir.Type(), ir.Type()
        raise AssertionError(f"impossible: {n}")

    def _check_with(self, p: Param[ir.IR], n: Node, typ: ir.IR):
        self.locals[p.name.id] = p.type
        ret = self.check(n, typ)
        try:
            del self.locals[p.name.id]
        except KeyError:
            pass
        return ret

    def _infer_with(self, p: Param[ir.IR], n: Node):
        self.locals[p.name.id] = p.type
        ret = self.infer(n)
        try:
            del self.locals[p.name.id]
        except KeyError:
            pass
        return ret
