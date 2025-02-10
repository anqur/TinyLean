from dataclasses import dataclass, field
from functools import reduce

from . import Ident, Param, Declaration, ir, grammar, InternalCompilerError


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


@dataclass(frozen=True)
class Placeholder(Node):
    is_user: bool


grammar.IDENT.set_parse_action(lambda r: Ident.fresh(r[0]))
grammar.TYPE.set_parse_action(lambda l, r: Type(l))
grammar.PLACEHOLDER.set_parse_action(lambda l, r: Placeholder(l, True))
grammar.REF.set_parse_action(lambda l, r: Ref(l, r[0][0]))
grammar.paren_expr.set_parse_action(lambda r: r[0][0])
grammar.implicit_param.set_parse_action(lambda r: Param(r[0], r[1][0], True))
grammar.explicit_param.set_parse_action(lambda r: Param(r[0], r[1][0], False))
grammar.function_type.set_parse_action(lambda l, r: FnType(l, r[0][0], r[0][1][0]))
grammar.function.set_parse_action(
    lambda l, r: reduce(lambda a, n: Fn(l, n, a), reversed(r[0][0]), r[0][1][0])
)
grammar.call.set_parse_action(
    lambda l, r: reduce(lambda a, b: Call(l, a, b), r[0][1:], r[0][0])
)
grammar.return_type.set_parse_action(
    lambda l, r: r[0] if len(r) > 0 else Placeholder(l, False)
)
grammar.definition.set_parse_action(
    lambda r: Declaration(r[0].loc, r[0].name, list(r[1]), r[2], r[3][0])
)
grammar.example.set_parse_action(
    lambda l, r: Declaration(l, Ident.fresh("_"), list(r[0]), r[1], r[2][0])
)


@dataclass(frozen=True)
class Parser:
    is_markdown: bool = False

    def __ror__(self, s: str):
        return (
            list(map(lambda r: r[0][0], grammar.markdown.scan_string(s)))
            if self.is_markdown
            else grammar.program.parse_string(s, parse_all=True)
        )


class DuplicateVariableError(Exception): ...


class UndefinedVariableError(Exception): ...


@dataclass(frozen=True)
class NameResolver:
    locals: dict[str, Ident] = field(default_factory=dict)
    globals: dict[str, Ident] = field(default_factory=dict)

    def __ror__(self, decls: list[Declaration[Node]]):
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
            case Call(loc, f, x):
                return Call(loc, self.expr(f), self.expr(x))
            case Type(_) | Placeholder(_, _):
                return node
        raise InternalCompilerError(node)  # pragma: no cover

    def _guard_local(self, v: Ident, node: Node):
        old = self._insert_local(v)
        ret = self.expr(node)
        if old:
            self._insert_local(old)
        elif not v.is_unbound():
            del self.locals[v.text]
        return ret

    def _insert_local(self, v: Ident):
        if v.is_unbound():
            return None
        old = None
        if v.text in self.locals:
            old = self.locals[v.text]
        self.locals[v.text] = v
        return old


class TypeMismatchError(Exception): ...


@dataclass(frozen=True)
class TypeChecker:
    globals: dict[int, Declaration[ir.IR]] = field(default_factory=dict)
    locals: dict[int, ir.IR] = field(default_factory=dict)

    def __ror__(self, ds: list[Declaration[Node]]):
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
        checked = Declaration(d.loc, d.name, params, ret, body)
        self.globals[d.name.id] = checked
        return checked

    def check(self, n: Node, typ: ir.IR) -> ir.IR:
        match n:
            case Fn(loc, v, body):
                match ir.Inliner().run(typ):
                    case ir.FnType(p, b):
                        body_type = ir.Inliner().run_with(p.name, ir.Ref(v), b)
                        param = Param(v, p.type, p.implicit)
                        return ir.Fn(param, self._check_with(param, body, body_type))
                    case want:
                        raise TypeMismatchError(str(want), "function", loc)
            case _:
                val, got = self.infer(n)
                got = ir.Inliner().run(got)
                want = ir.Inliner().run(typ)
                if ir.Converter().eq(got, want):
                    return val
                raise TypeMismatchError(str(want), str(got), n.loc)

    def infer(self, n: Node) -> tuple[ir.IR, ir.IR]:
        match n:
            case Ref(_, v):
                if v.id in self.locals:
                    return ir.Ref(v), self.locals[v.id]
                if v.id in self.globals:
                    d = self.globals[v.id]
                    return ir.rename(d.to_value(ir.Fn)), ir.rename(d.to_type(ir.FnType))
                raise InternalCompilerError(v)  # pragma: no cover
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
        raise InternalCompilerError(n)  # pragma: no cover

    def _check_with(self, p: Param[ir.IR], n: Node, typ: ir.IR):
        self.locals[p.name.id] = p.type
        ret = self.check(n, typ)
        if p.name.id in self.locals:
            del self.locals[p.name.id]
        return ret


def check_string(text: str, is_markdown=False):
    return text | Parser(is_markdown) | NameResolver() | TypeChecker()
