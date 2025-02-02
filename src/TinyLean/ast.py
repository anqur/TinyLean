from dataclasses import dataclass, field

from . import Ident, Param, Declaration, ir, grammar


@dataclass(frozen=True)
class Node:
    loc: int


@dataclass(frozen=True)
class Type(Node): ...


@dataclass(frozen=True)
class Reference(Node):
    name: Ident


@dataclass(frozen=True)
class FunctionType(Node):
    param_type: Param[Node]
    return_type: Node


@dataclass(frozen=True)
class Function(Node):
    param_name: Ident
    body: Node


@dataclass(frozen=True)
class Call(Node):
    callee: Node
    arg: Node


grammar.NAME.set_parse_action(lambda s: Ident(s))
grammar.param.set_parse_action(lambda s, l, r: Param(r[0], r[1]))
grammar.function_type.set_parse_action(lambda s, l, r: FunctionType(l, r[0], r[1]))
grammar.paren_expr.set_parse_action(lambda s, l, r: r[0])
grammar.function.set_parse_action(lambda s, l, r: Function(l, r[0], r[1]))
grammar.TYPE.set_parse_action(lambda s, l: Type(l))
grammar.call.set_parse_action(lambda s, l, r: Call(l, r[0], r[1]))
grammar.REFERENCE.set_parse_action(lambda s, l, r: Reference(l, r[0]))
grammar.definition.set_parse_action(
    lambda s, l, r: Declaration(l, r[0], r[1], r[2], r[3])
)


def parse(s: str):
    return grammar.program.parse_string(s, parse_all=True)


class NameResolveError(Exception): ...


@dataclass(frozen=True)
class NameResolver:
    locals: dict[str, Ident] = field(default_factory=dict)
    globals: set[str] = field(default_factory=set)

    def resolve(self, decls: list[Declaration[Node]]):
        return [self._resolve_def(d) for d in decls]

    def _resolve_def(self, d: Declaration[Node]):
        params = []
        for name, ty in d.param_types:
            self._insert_local(name)
            params.append(Param(name, self._resolve_expr(ty)))
        ret = self._resolve_expr(d.return_type)
        body = self._resolve_expr(d.definition)

        if not d.name.is_unbound():
            if d.name.text in self.globals:
                raise NameResolveError("duplicate variable", d.loc, d.name.text)
            self.globals.add(d.name.text)

        self.locals.clear()
        return Declaration(d.loc, d.name, params, ret, body)

    def _resolve_expr(self, node: Node) -> Node:
        match node:
            case Reference(loc, v):
                try:
                    return Reference(loc, self.locals[v.text])
                except KeyError:
                    raise NameResolveError("undefined variable", v.loc, v.text)
            case FunctionType(loc, p, body):
                typ = self._resolve_expr(p.type)
                b = self._guard_local(p.name, body)
                return FunctionType(loc, Param(p.name, typ), b)
            case Function(loc, v, body):
                b = self._guard_local(v, body)
                return Function(loc, v, b)
            case Call(loc, f, x):
                return Call(loc, self._resolve_expr(f), self._resolve_expr(x))
            case Type(_):
                return node
        raise AssertionError("impossible")

    def _guard_local(self, v: Ident, node: Node):
        old = self._insert_local(v)
        ret = self._resolve_expr(node)
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


class TypeAssertionError(Exception): ...


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
        for p in d.param_types:
            typ = self._check(p.type, ir.Type())
            params.append(Param(p.name, typ))
            self.locals[p.name.id] = typ
        ret = self._check(d.return_type, ir.Type())
        body = self._check(d.definition, ret)
        checked_def = Declaration(d.loc, d.name, params, ret, body)
        self.globals[d.name.id] = checked_def
        return checked_def

    def _check(self, n: Node, typ: ir.IR) -> ir.IR:
        match n:
            case Function(loc, v, body):
                match ir.inline(typ):
                    case ir.FunctionType(p, b):
                        body_type = ir.Inliner().run_with(p.name, ir.Reference(v), b)
                        param = Param(v, p.type)
                        return ir.Function(
                            param, self._check_with(param, body, body_type)
                        )
                    case got:
                        raise TypeAssertionError("expected function type", loc, got)
            case _:
                val, got = self._infer(n)
                got = ir.inline(got)
                want = ir.inline(typ)
                if ir.Converter(self.globals).check(got, want):
                    return val
                raise TypeMismatchError("type mismatch", n.loc, got, want)

    def _infer(self, n: Node) -> tuple[ir.IR, ir.IR]:
        match n:
            case Reference(_, v):
                try:
                    return ir.Reference(v), self.locals[v.id]
                except KeyError:
                    pass
                try:
                    d = self.globals[v.id]
                    return ir.definition_value(d), ir.signature_type(d)
                except KeyError:
                    raise AssertionError("impossible")
            case FunctionType(_, p, b):
                p_typ = self._check(p.type, ir.Type())
                inferred_p = Param(p.name, p_typ)
                b_val = self._check_with(inferred_p, b, ir.Type())
                return ir.FunctionType(inferred_p, b_val), ir.Type()
            case Call(_, f, x):
                f_tm, f_typ = self._infer(f)
                match f_typ:
                    case ir.FunctionType(p, b):
                        x_tm = self._check_with(p, x, p.type)
                        typ = ir.Inliner().run_with(p.name, x_tm, b)
                        val = ir.Inliner().apply(f_tm, x_tm)
                        return val, typ
                    case got:
                        raise TypeAssertionError("expected function type", f.loc, got)
            case Type(_):
                return ir.Type(), ir.Type()
        raise AssertionError("impossible")

    def _check_with(self, p: Param[ir.IR], n: Node, typ: ir.IR):
        self.locals[p.name.id] = p.type
        ret = self._check(n, typ)
        try:
            del self.locals[p.name.id]
        except KeyError:
            pass
        return ret

    def _infer_with(self, p: Param[ir.IR], n: Node):
        self.locals[p.name.id] = p.type
        ret = self._infer(n)
        try:
            del self.locals[p.name.id]
        except KeyError:
            pass
        return ret
