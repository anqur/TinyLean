from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import reduce
from typing import Optional, cast, OrderedDict

from . import (
    Name,
    Param,
    Def,
    Data as DataDecl,
    Ctor as CtorDecl,
    Sig,
    Decl,
    Class as ClassDecl,
    Field as FieldDecl,
    Instance,
)


@dataclass(frozen=True)
class IR: ...


@dataclass(frozen=True)
class Type(IR):
    def __str__(self):
        return "Type"


@dataclass(frozen=True)
class Ref(IR):
    name: Name

    def __str__(self):
        return str(self.name)


@dataclass(frozen=True)
class FnType(IR):
    param: Param[IR]
    ret: IR

    def __str__(self):
        return f"{self.param} → {self.ret}"


@dataclass(frozen=True)
class Fn(IR):
    param: Param[IR]
    body: IR

    def __str__(self):
        return f"λ {self.param} ↦ {self.body}"


@dataclass(frozen=True)
class Call(IR):
    callee: IR
    arg: IR

    def __str__(self):
        return f"({self.callee} {self.arg})"


@dataclass(frozen=True)
class Placeholder(IR):
    id: int
    is_user: bool

    def __str__(self):
        t = "u" if self.is_user else "m"
        return f"?{t}.{self.id}"


@dataclass(frozen=True)
class Data(IR):
    name: Name
    args: list[IR]

    def __str__(self):
        s = " ".join(str(x) for x in [self.name, *self.args])
        return f"({s})" if len(self.args) else s


@dataclass(frozen=True)
class Ctor(IR):
    ty_name: Name
    name: Name
    args: list[IR]

    def __str__(self):
        n = f"{self.ty_name}.{self.name}"
        s = " ".join(str(x) for x in [n, *self.args])
        return f"({s})" if len(self.args) else s


@dataclass(frozen=True)
class Nomatch(IR):
    def __str__(self):
        return "nomatch"


@dataclass(frozen=True)
class Case(IR):
    ctor: Name
    params: list[Param[IR]]
    body: IR

    def __str__(self):
        s = " ".join([str(self.ctor), *map(str, self.params)])
        return f"| {s} ↦ {self.body}"


@dataclass(frozen=True)
class Match(IR):
    arg: IR
    cases: dict[int, Case]

    def __str__(self):
        cs = " ".join(map(str, self.cases.values()))
        return f"match {self.arg} with {cs}"


@dataclass(frozen=True)
class Recur(IR):
    name: Name

    def __str__(self):
        return str(self.name)


@dataclass(frozen=True)
class Class(IR):
    name: Name
    args: list[IR]

    def __str__(self):
        s = " ".join(str(x) for x in [self.name, *self.args])
        return f"({s})" if len(self.args) else s

    def is_unsolved(self):
        return any(isinstance(a, Ref) for a in self.args)


@dataclass(frozen=True)
class Field(IR):
    name: Name
    type: IR

    def __str__(self):
        return str(self.name)


@dataclass(frozen=True)
class Renamer:
    locals: dict[int, int] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        if isinstance(v, Ref):
            if v.name.id in self.locals:
                return Ref(Name(v.name.text, self.locals[v.name.id]))
            return v
        if isinstance(v, Call):
            return Call(self.run(v.callee), self.run(v.arg))
        if isinstance(v, Fn):
            return Fn(self._param(v.param), self.run(v.body))
        if isinstance(v, FnType):
            return FnType(self._param(v.param), self.run(v.ret))
        if isinstance(v, Data):
            return Data(v.name, [self.run(x) for x in v.args])
        if isinstance(v, Ctor):
            return Ctor(v.ty_name, v.name, [self.run(x) for x in v.args])
        if isinstance(v, Match):
            arg = self.run(v.arg)
            cases = {
                i: Case(c.ctor, [self._param(p) for p in c.params], self.run(c.body))
                for i, c in v.cases.items()
            }
            return Match(arg, cases)
        if isinstance(v, Class):
            return Class(v.name, [self.run(x) for x in v.args])
        if isinstance(v, Field):
            return Field(v.name, self.run(v.type))
        assert any(isinstance(v, c) for c in (Type, Placeholder, Nomatch, Recur))
        return v

    def _param(self, p: Param[IR]):
        name = Name(p.name.text)
        self.locals[p.name.id] = name.id
        return Param(name, self.run(p.type), p.is_implicit, p.is_class)


_rn = lambda v: Renamer().run(v)


def _to(p: list[Param[IR]], v: IR, t=False):
    return reduce(lambda a, q: cast(IR, FnType(q, a) if t else Fn(q, a)), reversed(p), v)


def from_def(d: Def[IR]):
    return _rn(_to(d.params, d.body)), _rn(_to(d.params, d.ret, True))


def from_sig(s: Sig[IR]):
    return Recur(s.name), _rn(_to(s.params, s.ret, True))


def from_data(d: DataDecl[IR]):
    args = [Ref(p.name) for p in d.params]
    return _rn(_to(d.params, Data(d.name, args))), _rn(_to(d.params, Type(), True))


def from_ctor(c: CtorDecl[IR], d: DataDecl[IR]):
    adhoc = {x.name.id: v for x, v in cast(dict[Ref, IR], c.ty_args)}
    miss = [Param(p.name, p.type, True) for p in d.params if p.name.id not in adhoc]

    v = _to(c.params, Ctor(d.name, c.name, [Ref(p.name) for p in c.params]))
    v = _to(miss, v)

    ty_args = [adhoc.get(p.name.id, Ref(p.name)) for p in d.params]
    ty = _to(c.params, Data(d.name, ty_args), True)
    ty = _to(miss, ty, True)

    return _rn(v), _rn(ty)


def from_class(c: ClassDecl[IR]):
    args = [Ref(p.name) for p in c.params]
    return _rn(_to(c.params, Class(c.name, args))), _rn(_to(c.params, Type(), True))


def from_field(f: FieldDecl[IR], c: ClassDecl[IR], has_c_param=True):
    t = Class(c.name, [Ref(p.name) for p in c.params])
    ps = [*c.params, Param(Name("inst"), t, True, True)] if has_c_param else c.params
    return _rn(_to(ps, Field(f.name, t))), _rn(_to(ps, f.type, True))


@dataclass
class Answer:
    type: IR
    value: Optional[IR] = None

    def is_unsolved(self):
        return self.value is None


@dataclass(frozen=True)
class Hole:
    loc: int
    is_user: bool
    locals: dict[int, Param[IR]]
    answer: Answer


@contextmanager
def dirty_holes(holes: OrderedDict[int, Hole]):
    l = len(holes)
    try:
        yield
    finally:
        [holes.popitem() for _ in range(len(holes) - l)]


class NoInstanceError(Exception): ...


@dataclass
class Inliner:
    holes: OrderedDict[int, Hole]
    globals: dict[int, Decl]
    can_recurse: bool = True
    env: dict[int, IR] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        if isinstance(v, Ref):
            return self.run(_rn(self.env[v.name.id])) if v.name.id in self.env else v
        if isinstance(v, Call):
            f = self.run(v.callee)
            x = self.run(v.arg)
            if isinstance(f, Fn):
                return self.run_with(f.body, (f.param.name, x))
            return Call(f, x)
        if isinstance(v, Fn):
            return Fn(self._param(v.param), self.run(v.body))
        if isinstance(v, FnType):
            return FnType(self._param(v.param), self.run(v.ret))
        if isinstance(v, Placeholder):
            h = self.holes[v.id]
            h.answer.type = self.run(h.answer.type)
            return v if h.answer.is_unsolved() else self.run(h.answer.value)
        if isinstance(v, Ctor):
            return Ctor(v.ty_name, v.name, [self.run(v) for v in v.args])
        if isinstance(v, Data):
            return Data(v.name, [self.run(v) for v in v.args])
        if isinstance(v, Match):
            arg = self.run(v.arg)
            can_recurse = self.can_recurse
            self.can_recurse = False
            cases = {
                i: Case(c.ctor, [self._param(p) for p in c.params], self.run(c.body))
                for i, c in v.cases.items()
            }
            self.can_recurse = can_recurse
            if not isinstance(arg, Ctor):
                return Match(arg, cases)
            c = cases[arg.name.id]
            env = [(x.name, v) for x, v in zip(c.params, arg.args)]
            return self.run_with(c.body, *env)
        if isinstance(v, Recur):
            if self.can_recurse:
                d = self.globals[v.name.id]
                if isinstance(d, Def):
                    return from_def(d)[0]
                assert isinstance(d, Sig)
            return v
        if isinstance(v, Class):
            return Class(v.name, [self.run(t) for t in v.args])
        if isinstance(v, Field):
            c = cast(Class, self.run(v.type))
            if c.is_unsolved():
                return Field(v.name, c)
            i = self._resolve_instance(c)
            val = next(val for n, val in i.fields if cast(Ref, n).name.id == v.name.id)
            return self.run(val)
        assert isinstance(v, Type) or isinstance(v, Nomatch)
        return v

    def run_with(self, x: IR, *env: tuple[Name, IR]):
        self.env.update({n.id: v for n, v in env})
        return self.run(x)

    def apply(self, f: IR, *args: IR):
        ret = f
        for x in args:
            if isinstance(ret, Fn):
                ret = self.run_with(ret.body, (ret.param.name, x))
            else:
                ret = Call(ret, x)
        return ret

    def _param(self, param: Param[IR]):
        p = Param(param.name, self.run(param.type), param.is_implicit, param.is_class)
        if not p.is_class:
            return p
        ty = cast(Class, p.type)
        if not ty.is_unsolved() and not self._resolve_instance(ty):
            raise NoInstanceError(str(ty), self.globals[ty.name.id].loc)
        return p

    def _resolve_instance(self, c: Class) -> Optional[Instance[IR]]:
        cls = cast(ClassDecl, self.globals[c.name.id])
        for inst_id in cls.instances:
            i = cast(Instance, self.globals[inst_id])
            with dirty_holes(self.holes):
                if Converter(self.holes, self.globals).eq(c, i.type):
                    return i
        return None


@dataclass(frozen=True)
class Converter:
    holes: OrderedDict[int, Hole]
    globals: dict[int, Decl]

    def eq(self, lhs: IR, rhs: IR):
        match lhs, rhs:
            case Placeholder() as x, y:
                return self._solve(x, y)
            case x, Placeholder() as y:
                return self._solve(y, x)
            case Ref(x), Ref(y):
                return x.id == y.id
            case Call(f, x), Call(g, y):
                return self.eq(f, g) and self.eq(x, y)
            case Fn(p, b), Fn(q, c):
                env = [(q.name, Ref(p.name))]
                return self.eq(b, Inliner(self.holes, self.globals).run_with(c, *env))
            case FnType(p, b), FnType(q, c):
                if not self.eq(p.type, q.type):
                    return False
                env = [(q.name, Ref(p.name))]
                return self.eq(b, Inliner(self.holes, self.globals).run_with(c, *env))
            case Data(x, xs), Data(y, ys):
                return x.id == y.id and self._args(xs, ys)
            case Ctor(t, x, xs), Ctor(u, y, ys):
                return t.id == u.id and x.id == y.id and self._args(xs, ys)
            case Type(), Type():
                return True
            case Class(x, xs), Class(y, ys):
                return x.id == y.id and self._args(xs, ys)

        # FIXME: Following cases not seen in tests yet:
        assert not (isinstance(lhs, Placeholder) and isinstance(rhs, Placeholder))
        assert not (isinstance(lhs, Match) and isinstance(rhs, Match))
        assert not (isinstance(lhs, Field) and isinstance(rhs, Field))

        return False

    def _solve(self, p: Placeholder, answer: IR):
        h = self.holes[p.id]
        if not h.answer.is_unsolved():
            return self.eq(h.answer.value, answer)
        h.answer.value = answer

        if isinstance(answer, Ref):
            for param in h.locals.values():
                if param.name.id == answer.name.id:
                    assert self.eq(param.type, h.answer.type)  # FIXME: will fail here?

        return True

    def _args(self, xs: list[IR], ys: list[IR]):
        assert len(xs) == len(ys)
        return all(self.eq(x, y) for x, y in zip(xs, ys))
