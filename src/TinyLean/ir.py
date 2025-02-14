from dataclasses import dataclass, field
from functools import reduce
from typing import Optional, cast

from . import Name, Param, Decl


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
class Renamer:
    locals: dict[int, int] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        match v:
            case Ref(n):
                if n.id in self.locals:
                    return Ref(Name(n.text, self.locals[n.id]))
                return v
            case Call(f, x):
                return Call(self.run(f), self.run(x))
            case Fn(p, b):
                return Fn(self._param(p), self.run(b))
            case FnType(p, b):
                return FnType(self._param(p), self.run(b))
            case Type() | Placeholder():
                return v
        raise AssertionError(v)  # pragma: no cover

    def _param(self, p: Param[IR]):
        name = Name(p.name.text)
        self.locals[p.name.id] = name.id
        return Param(name, self.run(p.type), p.is_implicit)


_rn = lambda v: Renamer().run(v)


def decl_type(d: Decl[IR]):
    return _rn(reduce(lambda a, p: cast(IR, FnType(p, a)), reversed(d.params), d.ret))


def decl_value(d: Decl[IR]):
    return _rn(reduce(lambda a, p: cast(IR, Fn(p, a)), reversed(d.params), d.body))


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


@dataclass(frozen=True)
class Inliner:
    holes: dict[int, Hole]
    env: dict[int, IR] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        match v:
            case Ref(n):
                if n.id in self.env:
                    return self.run(_rn(self.env[n.id]))
                return v
            case Call(f, x):
                f = self.run(f)
                x = self.run(x)
                match f:
                    case Fn(p, b):
                        return self.run_with(p.name, x, b)
                    case _:
                        return Call(f, x)
            case Fn(p, b):
                return Fn(self._param(p), self.run(b))
            case FnType(p, b):
                return FnType(self._param(p), self.run(b))
            case Type():
                return v
            case Placeholder(i) as ph:
                h = self.holes[i]
                h.answer.type = self.run(h.answer.type)
                if h.answer.is_unsolved():
                    return ph
                return self.run(h.answer.value)
        raise AssertionError(v)  # pragma: no cover

    def run_with(self, a_name: Name, a: IR, b: IR):
        self.env[a_name.id] = a
        return self.run(b)

    def apply(self, f: IR, *args: IR):
        ret = f
        for x in args:
            match ret:
                case Fn(p, b):
                    ret = self.run_with(p.name, x, b)
                case _:
                    ret = Call(ret, x)
        return ret

    def _param(self, p: Param[IR]):
        return Param(p.name, self.run(p.type), p.is_implicit)


@dataclass(frozen=True)
class Converter:
    holes: dict[int, Hole]

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
            case FnType(p, b), FnType(q, c):
                if not self.eq(p.type, q.type):
                    return False
                return self.eq(b, Inliner(self.holes).run_with(q.name, Ref(p.name), c))
            case Type(), Type():
                return True

        # FIXME: Following cases not seen in tests yet:
        assert not (isinstance(lhs, Fn) and isinstance(rhs, Fn))
        assert not (isinstance(lhs, Placeholder) and isinstance(rhs, Placeholder))

        return False

    def _solve(self, p: Placeholder, answer: IR):
        h = self.holes[p.id]
        assert h.answer.is_unsolved()  # FIXME: can be not None here?
        h.answer.value = answer

        if isinstance(answer, Ref):
            for param in h.locals.values():
                if param.name.id == answer.name.id:
                    assert self.eq(param.type, h.answer.type)  # FIXME: will fail here?
        return True
