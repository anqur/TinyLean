from dataclasses import dataclass, field
from functools import reduce

from . import Ident, Param, Declaration, trustme


@dataclass(frozen=True)
class IR: ...


@dataclass(frozen=True)
class Reference(IR):
    name: Ident

    def __str__(self):
        return str(self.name)


@dataclass(frozen=True)
class Type(IR):
    def __str__(self):
        return "Type"


@dataclass(frozen=True)
class FunctionType(IR):
    param_type: Param[IR]
    return_type: IR

    def __str__(self):
        return f"{self.param_type} → {self.return_type}"


@dataclass(frozen=True)
class Function(IR):
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
            case Reference(v):
                try:
                    return Reference(Ident(v.text, self.locals[v.id]))
                except KeyError:
                    return v
            case Call(f, x):
                return Call(self.run(f), self.run(x))
            case Function(p, b):
                return Function(self._param(p), self.run(b))
            case FunctionType(p, b):
                return FunctionType(self._param(p), self.run(b))
            case Type():
                return v
        raise AssertionError("impossible")

    def _param(self, p: Param[IR]):
        name = Ident.fresh(p.name.text)
        self.locals[p.name.id] = name.id
        return Param(name, self.run(p.type))


rename = lambda v: Renamer().run(v)


def signature_type(d: Declaration[IR]) -> IR:
    return rename(reduce(trustme(FunctionType), reversed(d.param_types), d.return_type))


def definition_value(d: Declaration[IR]) -> IR:
    return rename(reduce(trustme(Function), reversed(d.param_types), d.definition))


@dataclass(frozen=True)
class Inliner:
    env: dict[int, IR] = field(default_factory=dict)

    def run(self, v: IR) -> IR:
        match v:
            case Reference(v):
                try:
                    return self.run(self.env[v.id])
                except KeyError:
                    return v
            case Call(f, x):
                f = self.run(f)
                x = self.run(x)
                match f:
                    case Function(p, b):
                        return self.run_with(p.name, x, b)
                    case _:
                        return Call(f, x)
            case Function(p, b):
                return Function(self._param(p), self.run(b))
            case FunctionType(p, b):
                return FunctionType(self._param(p), self.run(b))
            case Type():
                return v
        raise AssertionError("impossible")

    def run_with(self, a_name: Ident, a: IR, b: IR):
        self.env[a_name.id] = a
        return self.run(b)

    def apply(self, f: IR, *args: IR):
        ret = f
        for x in args:
            match f:
                case Function(p, b):
                    ret = self.run_with(p.name, x, b)
                case _:
                    ret = Call(ret, x)
        return ret

    def _param(self, p: Param[IR]):
        return Param(p.name, self.run(p.type))


inline = lambda v: Inliner().run(v)


@dataclass(frozen=True)
class Converter:
    globals: dict[int, Declaration[IR]]

    def check(self, lhs: IR, rhs: IR) -> bool:
        match lhs, rhs:
            case Reference(x), Reference(y):
                return x.name.id == y.name.id and x.name.text == y.name.text
            case Call(f, x), Call(g, y):
                return self.check(f, g) and self.check(x, y)
            case Function(p, b), Function(q, c):
                return self.check(b, Inliner().run_with(q.name, Reference(p.name), c))
            case FunctionType(p, b), FunctionType(q, c):
                if not self.check(p.type, q.type):
                    return False
                return self.check(b, Inliner().run_with(q.name, Reference(p.name), c))
            case Type(), Type():
                return True
        return False


can_convert = lambda g, a, b: Converter(g).check(a, b)
