from dataclasses import dataclass, field
from functools import reduce
from typing import cast

from . import Ident, Param, Declaration, InternalCompilerError


@dataclass(frozen=True)
class IR: ...


@dataclass(frozen=True)
class Type(IR):
    def __str__(self):
        return "Type"


@dataclass(frozen=True)
class Ref(IR):
    name: Ident

    def __str__(self):
        return str(self.name)


@dataclass(frozen=True)
class FnType(IR):
    param_type: Param[IR]
    return_type: IR

    def __str__(self):
        return f"{self.param_type} → {self.return_type}"


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
class Renamer:
    locals: dict[int, int] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        match v:
            case Ref(v):
                try:
                    return Ref(Ident(self.locals[v.id], v.text))
                except KeyError:
                    return v
            case Call(f, x):
                return Call(self.run(f), self.run(x))
            case Fn(p, b):
                return Fn(self._param(p), self.run(b))
            case FnType(p, b):
                return FnType(self._param(p), self.run(b))
            case Type():
                return v
        raise InternalCompilerError(v)  # pragma: no cover

    def _param(self, p: Param[IR]):
        name = Ident.fresh(p.name.text)
        self.locals[p.name.id] = name.id
        return Param(name, self.run(p.type), p.implicit)


rename = lambda v: Renamer().run(v)


_ir = lambda t: cast(IR, t)


def signature_type(d: Declaration[IR]) -> IR:
    return rename(reduce(lambda a, p: _ir(FnType(p, a)), reversed(d.params), d.ret))


def definition_value(d: Declaration[IR]) -> IR:
    return rename(reduce(lambda a, p: _ir(Fn(p, a)), reversed(d.params), d.body))


@dataclass(frozen=True)
class Inliner:
    env: dict[int, IR] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        match v:
            case Ref(n):
                try:
                    return self.run(self.env[n.id])
                except KeyError:
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
        raise InternalCompilerError(v)  # pragma: no cover

    def run_with(self, a_name: Ident, a: IR, b: IR):
        self.env[a_name.id] = a
        return self.run(b)

    def apply(self, f: IR, *args: IR):
        ret = f
        for x in args:
            match f:
                case Fn(p, b):
                    ret = self.run_with(p.name, x, b)
                case _:
                    ret = Call(ret, x)
        return ret

    def _param(self, p: Param[IR]):
        return Param(p.name, self.run(p.type), p.implicit)


inline = lambda v: Inliner().run(v)


@dataclass(frozen=True)
class Converter:
    globals: dict[int, Declaration[IR]]

    def eq(self, lhs: IR, rhs: IR) -> bool:
        match lhs, rhs:
            case Ref(x), Ref(y):
                return x.id == y.id and x.text == y.text
            case Call(f, x), Call(g, y):
                return self.eq(f, g) and self.eq(x, y)
            case Fn(p, b), Fn(q, c):
                return self.eq(b, Inliner().run_with(q.name, Ref(p.name), c))
            case FnType(p, b), FnType(q, c):
                if not self.eq(p.type, q.type):
                    return False
                return self.eq(b, Inliner().run_with(q.name, Ref(p.name), c))
            case Type(), Type():
                return True
        return False
