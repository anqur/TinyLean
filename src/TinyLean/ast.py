from functools import reduce
from itertools import chain
from dataclasses import dataclass, field
from typing import OrderedDict, cast as _c

from . import Name, Param, Decl, ir, grammar as _g, fresh, Def, Example, Ctor, Data


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
    implicit: str | bool


@dataclass(frozen=True)
class Placeholder(Node):
    is_user: bool


@dataclass(frozen=True)
class Nomatch(Node):
    arg: Node


def _with_placeholders(f: Node, f_ty: ir.IR, implicit: str | bool) -> Node | None:
    if not isinstance(f_ty, ir.FnType) or not f_ty.param.is_implicit:
        return None

    if isinstance(implicit, bool):
        return _call_placeholder(f) if not implicit else None

    pending = 0
    while True:
        # FIXME: Would fail with `{a: Type} -> Type`?
        assert isinstance(f_ty, ir.FnType)

        if not f_ty.param.is_implicit:
            raise UndefinedImplicitParam(implicit, f.loc)
        if f_ty.param.name.text == implicit:
            break
        pending += 1
        f_ty = f_ty.ret

    if not pending:
        return None

    for _ in range(pending):
        f = _call_placeholder(f)
    return f


def _call_placeholder(f: Node):
    return Call(f.loc, f, Placeholder(f.loc, False), True)


_g.name.add_parse_action(lambda r: Name(r[0][0]))
_g.type_.add_parse_action(lambda l, r: Type(l))
_g.ph.add_parse_action(lambda l, r: Placeholder(l, True))
_g.ref.add_parse_action(lambda l, r: Ref(l, r[0][0]))
_g.i_param.add_parse_action(lambda r: Param(r[0], r[1], True))
_g.e_param.add_parse_action(lambda r: Param(r[0], r[1], False))
_g.fn_type.add_parse_action(lambda l, r: FnType(l, r[0], r[1]))
_g.fn.add_parse_action(
    lambda l, r: reduce(lambda a, n: Fn(l, n, a), reversed(r[0]), r[1])
)
_g.nomatch.add_parse_action(lambda l, r: Nomatch(l, r[0][0]))
_g.i_arg.add_parse_action(lambda l, r: (r[1], r[0]))
_g.e_arg.add_parse_action(lambda l, r: (r[0], False))
_g.call.add_parse_action(
    lambda l, r: reduce(lambda a, b: Call(l, a, b[0], b[1]), r[1:], r[0])
)
_g.p_expr.add_parse_action(lambda r: r[0])
_g.return_type.add_parse_action(lambda l, r: r[0] if len(r) else Placeholder(l, False))
_g.definition.add_parse_action(
    lambda r: Def(r[0].loc, r[0].name, list(r[1]), r[2], r[3])
)
_g.example.add_parse_action(lambda l, r: Example(l, list(r[0]), r[1], r[2]))
_g.type_arg.add_parse_action(lambda r: (r[0], r[1]))
_g.ctor.add_parse_action(lambda r: Ctor(r[0].loc, r[0].name, list(r[1]), list(r[2])))
_g.data.add_condition(
    lambda r: r[0].name.text == r[3], message="open and datatype name mismatch"
).add_parse_action(lambda r: Data(r[0].loc, r[0].name, list(r[1]), list(r[2])))


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

    def __ror__(self, decls: list[Decl]):
        return [self._decl(d) for d in decls]

    def _decl(self, decl: Decl) -> Decl:
        self.locals.clear()

        if isinstance(decl, Def) or isinstance(decl, Example):
            return self._def_or_example(decl)

        assert isinstance(decl, Data)
        return self._data(decl)

    def _def_or_example(self, d: Def[Node] | Example[Node]):
        params = self._params(d.params)
        ret = self.expr(d.ret)
        body = self.expr(d.body)

        assert len(self.locals) == len(params)

        if isinstance(d, Example):
            return Example(d.loc, params, ret, body)

        self._insert_global(d.loc, d.name)
        return Def(d.loc, d.name, params, ret, body)

    def _data(self, d: Data[Node]):
        self._insert_global(d.loc, d.name)
        params = self._params(d.params)
        ctors = [self._ctor(c, d.name) for c in d.ctors]
        assert len(self.locals) == len(params)
        return Data(d.loc, d.name, params, ctors)

    def _ctor(self, c: Ctor[Node], ty_name: Name):
        params = self._params(c.params)
        ty_args = [(self.expr(n), self.expr(t)) for n, t in c.ty_args]
        for p in params:
            del self.locals[p.name.text]
        self._insert_global(c.loc, c.name)
        return Ctor(c.loc, c.name, params, ty_args, ty_name)

    def _params(self, params: list[Param[Node]]):
        ret = []
        for p in params:
            self._insert_local(p.name)
            ret.append(Param(p.name, self.expr(p.type), p.is_implicit))
        return ret

    def expr(self, n: Node) -> Node:
        if isinstance(n, Ref):
            if v := self.locals.get(n.name.text, self.globals.get(n.name.text)):
                return Ref(n.loc, v)
            raise UndefinedVariableError(n.name.text, n.loc)
        if isinstance(n, FnType):
            typ = self.expr(n.param.type)
            b = self._guard_local(n.param.name, n.ret)
            return FnType(n.loc, Param(n.param.name, typ, n.param.is_implicit), b)
        if isinstance(n, Fn):
            return Fn(n.loc, n.param, self._guard_local(n.param, n.body))
        if isinstance(n, Call):
            return Call(n.loc, self.expr(n.callee), self.expr(n.arg), n.implicit)
        if isinstance(n, Nomatch):
            return Nomatch(n.loc, self.expr(n.arg))
        assert isinstance(n, Type) or isinstance(n, Placeholder)
        return n

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
        old = self.locals.get(v.text)
        self.locals[v.text] = v
        return old

    def _insert_global(self, loc: int, name: Name):
        if not name.is_unbound():
            if name.text in self.globals:
                raise DuplicateVariableError(name.text, loc)
            self.globals[name.text] = name


class TypeMismatchError(Exception): ...


class UnsolvedPlaceholderError(Exception): ...


class UndefinedImplicitParam(Exception): ...


@dataclass(frozen=True)
class TypeChecker:
    globals: dict[int, Decl] = field(default_factory=dict)
    locals: dict[int, Param[ir.IR]] = field(default_factory=dict)
    holes: OrderedDict[int, ir.Hole] = field(default_factory=OrderedDict)

    def __ror__(self, ds: list[Decl]):
        ret = [self._run(d) for d in ds]
        for i, h in self.holes.items():
            if h.answer.is_unsolved():
                p = ir.Placeholder(i, h.is_user)
                ty = self._inliner().run(h.answer.type)
                raise UnsolvedPlaceholderError(str(p), h.locals, ty, h.loc)
        return ret

    def _run(self, decl: Decl) -> Decl:
        self.locals.clear()
        if isinstance(decl, Def) or isinstance(decl, Example):
            return self._def_or_example(decl)
        assert isinstance(decl, Data)
        return self._data(decl)

    def _def_or_example(self, d: Def[Node] | Example[Node]):
        params = self._params(d.params)
        ret = self.check(d.ret, ir.Type())
        body = self.check(d.body, ret)

        if isinstance(d, Example):
            return Example(d.loc, params, ret, body)

        ret = Def(d.loc, d.name, params, ret, body)
        self.globals[d.name.id] = ret
        return ret

    def _data(self, d: Data[Node]):
        params = self._params(d.params)
        data = Data(d.loc, d.name, params, [])
        self.globals[d.name.id] = data
        data.ctors.extend(self._ctor(c) for c in d.ctors)
        return data

    def _ctor(self, c: Ctor[Node]):
        params = self._params(c.params)
        ty_args: list[tuple[ir.IR, ir.IR]] = []
        for x, v in c.ty_args:
            x_val, x_ty = self.infer(x)
            v_val = self.check(v, x_ty)
            assert isinstance(x_val, ir.Ref)
            ty_args.append((x_val, v_val))
        ctor = Ctor(c.loc, c.name, params, ty_args, c.ty_name)
        self.globals[c.name.id] = ctor
        return ctor

    def _params(self, params: list[Param[Node]]):
        ret = []
        for p in params:
            param = Param(p.name, self.check(p.type, ir.Type()), p.is_implicit)
            self.locals[p.name.id] = param
            ret.append(param)
        return ret

    def check(self, n: Node, typ: ir.IR) -> ir.IR:
        if isinstance(n, Fn):
            want = self._inliner().run(typ)
            if not isinstance(want, ir.FnType):
                raise TypeMismatchError(str(want), "function", n.loc)
            ret = self._inliner().run_with(want.param.name, ir.Ref(n.param), want.ret)
            param = Param(n.param, want.param.type, want.param.is_implicit)
            return ir.Fn(param, self._check_with(param, n.body, ret))

        holes_len = len(self.holes)
        val, got = self.infer(n)
        got = self._inliner().run(got)
        want = self._inliner().run(typ)

        # Check if we can insert placeholders for `val` of type `want` here.
        #
        # FIXME: No valid tests for this yet, we cannot insert placeholders for implicit function types.
        # Change this to an actual check if we got any examples.
        assert not isinstance(want, ir.FnType) or not want.param.is_implicit
        if new_f := _with_placeholders(n, got, False):
            # FIXME: No valid tests yet.
            assert len(self.holes) == holes_len
            val, got = self.infer(new_f)

        if not ir.Converter(self.holes).eq(got, want):
            raise TypeMismatchError(str(want), str(got), n.loc)

        return val

    def infer(self, n: Node) -> tuple[ir.IR, ir.IR]:
        if isinstance(n, Ref):
            if param := self.locals.get(n.name.id):
                return ir.Ref(param.name), param.type
            d = self.globals[n.name.id]
            if isinstance(d, Def):
                return ir.from_def(d)
            if isinstance(d, Data):
                return ir.from_data(d)
            assert isinstance(d, Ctor)
            data_decl = self.globals[d.ty_name.id]
            assert isinstance(data_decl, Data)
            return ir.from_ctor(d, data_decl)
        if isinstance(n, FnType):
            p_typ = self.check(n.param.type, ir.Type())
            inferred_p = Param(n.param.name, p_typ, n.param.is_implicit)
            b_val = self._check_with(inferred_p, n.ret, ir.Type())
            return ir.FnType(inferred_p, b_val), ir.Type()
        if isinstance(n, Call):
            holes_len = len(self.holes)
            f_val, got = self.infer(n.callee)

            if implicit_f := _with_placeholders(n.callee, got, n.implicit):
                for _ in range(len(self.holes) - holes_len):
                    self.holes.popitem()
                return self.infer(Call(n.loc, implicit_f, n.arg, n.implicit))

            if not isinstance(got, ir.FnType):
                raise TypeMismatchError("function", str(got), n.callee.loc)

            x_tm = self._check_with(got.param, n.arg, got.param.type)
            typ = self._inliner().run_with(got.param.name, x_tm, got.ret)
            val = self._inliner().apply(f_val, x_tm)
            return val, typ
        if isinstance(n, Placeholder):
            ty = self._insert_hole(n.loc, n.is_user, ir.Type())
            v = self._insert_hole(n.loc, n.is_user, ty)
            return v, ty
        if isinstance(n, Nomatch):
            _, got = self.infer(n.arg)
            if not isinstance(got, ir.Data):
                raise TypeMismatchError("datatype", str(got), n.arg.loc)
            if len(_c(Data, self.globals[got.name.id]).ctors):
                raise TypeMismatchError("empty datatype", str(got), n.arg.loc)
            return ir.Nomatch(), self._insert_hole(n.loc, False, ir.Type())
        assert isinstance(n, Type)
        return ir.Type(), ir.Type()

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
