from functools import reduce
from itertools import chain
from dataclasses import dataclass, field

from . import Name, Param, Decl, ir, grammar as _g, fresh


@dataclass(frozen=True)
class Node:
    loc: int


@dataclass(frozen=True)
class Type(Node): ...


@dataclass(frozen=True)
class Ref(Node):
    name: Name


@dataclass(frozen=True)
class FnType(Node):
    param: Param[Node]
    ret: Node


@dataclass(frozen=True)
class Fn(Node):
    param: Name
    body: Node


@dataclass(frozen=True)
class Call(Node):
    callee: Node
    arg: Node
    implicit_to: str | None


@dataclass(frozen=True)
class Placeholder(Node):
    is_user: bool


_g.name.set_parse_action(lambda r: Name(r[0][0]))
_g.type_.set_parse_action(lambda l, r: Type(l))
_g.ph.set_parse_action(lambda l, r: Placeholder(l, True))
_g.ref.set_parse_action(lambda l, r: Ref(l, r[0][0]))
_g.implicit_param.set_parse_action(lambda r: Param(r[0], r[1], True))
_g.explicit_param.set_parse_action(lambda r: Param(r[0], r[1], False))
_g.fn_type.set_parse_action(lambda l, r: FnType(l, r[0], r[1]))
_g.fn.set_parse_action(
    lambda l, r: reduce(lambda a, n: Fn(l, n, a), reversed(r[0]), r[1])
)
_g.i_arg.set_parse_action(lambda l, r: (r[1], r[0]))
_g.e_arg.set_parse_action(lambda l, r: (r[0], None))
_g.call.set_parse_action(
    lambda l, r: reduce(lambda a, b: Call(l, a, b[0], b[1]), r[1:], r[0])
)
_g.p_expr.set_parse_action(lambda r: r[0])
_g.return_type.set_parse_action(lambda l, r: r[0] if len(r) else Placeholder(l, False))
_g.definition.set_parse_action(
    lambda r: Decl(r[0].loc, r[0].name, list(r[1]), r[2], r[3])
)
_g.example.set_parse_action(lambda l, r: Decl(l, Name("_"), list(r[0]), r[1], r[2]))


@dataclass(frozen=True)
class Parser:
    is_markdown: bool = False

    def __ror__(self, s: str):
        if not self.is_markdown:
            return list(_g.program.parse_string(s, parse_all=True))
        return chain.from_iterable(r[0] for r in _g.markdown.scan_string(s))


class DuplicateVariableError(Exception): ...


class UndefinedVariableError(Exception): ...


@dataclass(frozen=True)
class NameResolver:
    locals: dict[str, Name] = field(default_factory=dict)
    globals: dict[str, Name] = field(default_factory=dict)

    def __ror__(self, decls: list[Decl[Node]]):
        return [self.decl(d) for d in decls]

    def decl(self, d: Decl[Node]):
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
        return Decl(d.loc, d.name, params, ret, body)

    def expr(self, node: Node) -> Node:
        match node:
            case Ref(loc, v):
                if v.text in self.locals:
                    return Ref(loc, self.locals[v.text])
                if v.text in self.globals:
                    return Ref(loc, self.globals[v.text])
                raise UndefinedVariableError(v, loc)
            case FnType(loc, p, body):
                typ = self.expr(p.type)
                b = self._guard_local(p.name, body)
                return FnType(loc, Param(p.name, typ, p.implicit), b)
            case Fn(loc, v, body):
                b = self._guard_local(v, body)
                return Fn(loc, v, b)
            case Call(loc, f, x, n):
                return Call(loc, self.expr(f), self.expr(x), n)
            case Type() | Placeholder():
                return node
        raise AssertionError(node)  # pragma: no cover

    def _guard_local(self, v: Name, node: Node):
        old = self._insert_local(v)
        ret = self.expr(node)
        if old:
            self._insert_local(old)
        elif not v.is_unbound():
            del self.locals[v.text]
        return ret

    def _insert_local(self, v: Name):
        if v.is_unbound():
            return None
        old = None
        if v.text in self.locals:
            old = self.locals[v.text]
        self.locals[v.text] = v
        return old


class TypeMismatchError(Exception): ...


class UnsolvedPlaceholderError(Exception): ...


@dataclass(frozen=True)
class TypeChecker:
    globals: dict[int, Decl[ir.IR]] = field(default_factory=dict)
    locals: dict[int, Param[ir.IR]] = field(default_factory=dict)
    holes: dict[int, ir.Hole] = field(default_factory=dict)

    def __ror__(self, ds: list[Decl[Node]]):
        ret = [self._run(d) for d in ds]
        for i, h in self.holes.items():
            if h.answer.is_unsolved():
                p = ir.Placeholder(i, h.is_user)
                ty = self._inliner().run(h.answer.type)
                raise UnsolvedPlaceholderError(str(p), h.locals, ty, h.loc)
        return ret

    def _run(self, d: Decl[Node]) -> Decl[ir.IR]:
        self.locals.clear()
        params = []
        for p in d.params:
            param = Param(p.name, self.check(p.type, ir.Type()), p.implicit)
            self.locals[p.name.id] = param
            params.append(param)
        ret = self.check(d.ret, ir.Type())
        body = self.check(d.body, ret)
        checked = Decl(d.loc, d.name, params, ret, body)
        self.globals[d.name.id] = checked
        return checked

    def check(self, n: Node, typ: ir.IR) -> ir.IR:
        match n:
            case Fn(loc, v, body):
                match self._inliner().run(typ):
                    case ir.FnType(p, b):
                        body_type = self._inliner().run_with(p.name, ir.Ref(v), b)
                        param = Param(v, p.type, p.implicit)
                        return ir.Fn(param, self._check_with(param, body, body_type))
                    case want:
                        raise TypeMismatchError(str(want), "function", loc)
            case _:
                val, got = self.infer(n)
                got = self._inliner().run(got)
                want = self._inliner().run(typ)
                if ir.Converter(self.holes).eq(got, want):
                    return val
                raise TypeMismatchError(str(want), str(got), n.loc)

    def infer(self, n: Node) -> tuple[ir.IR, ir.IR]:
        match n:
            case Ref(_, v):
                if v.id in self.locals:
                    return ir.Ref(v), self.locals[v.id].type
                if v.id in self.globals:
                    d = self.globals[v.id]
                    return ir.rename(d.to_value(ir.Fn)), ir.rename(d.to_type(ir.FnType))
                raise AssertionError(v)  # pragma: no cover
            case FnType(_, p, b):
                p_typ = self.check(p.type, ir.Type())
                inferred_p = Param(p.name, p_typ, p.implicit)
                b_val = self._check_with(inferred_p, b, ir.Type())
                return ir.FnType(inferred_p, b_val), ir.Type()
            case Call(_, f, x, _):
                f_tm, f_typ = self.infer(f)
                match f_typ:
                    case ir.FnType(p, b):
                        x_tm = self._check_with(p, x, p.type)
                        typ = self._inliner().run_with(p.name, x_tm, b)
                        val = self._inliner().apply(f_tm, x_tm)
                        return val, typ
                    case got:
                        raise TypeMismatchError("function", str(got), f.loc)
            case Type():
                return ir.Type(), ir.Type()
            case Placeholder(loc, is_user):
                ty = self._insert_hole(loc, is_user, ir.Type())
                v = self._insert_hole(loc, is_user, ty)
                return v, ty
        raise AssertionError(n)  # pragma: no cover

    def _inliner(self):
        return ir.Inliner(self.holes)

    def _check_with(self, p: Param[ir.IR], n: Node, typ: ir.IR):
        self.locals[p.name.id] = p
        ret = self.check(n, typ)
        if p.name.id in self.locals:
            del self.locals[p.name.id]
        return ret

    def _insert_hole(self, loc: int, is_user: bool, typ: ir.IR):
        i = fresh()
        self.holes[i] = ir.Hole(loc, is_user, self.locals.copy(), ir.Answer(typ))
        return ir.Placeholder(i, is_user)


def check_string(text: str, is_markdown=False):
    return text | Parser(is_markdown) | NameResolver() | TypeChecker()
