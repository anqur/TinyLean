from dataclasses import dataclass
from functools import reduce
from typing import cast

from . import Ident, Param, Declaration


@dataclass(frozen=True)
class IR: ...


@dataclass(frozen=True)
class Reference(IR):
    v: Ident

    def __str__(self):
        return str(self.v)


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


def signature_type(decl: Declaration[IR]) -> IR:
    return reduce(cast(any, FunctionType), reversed(decl.param_types), decl.return_type)


def definition_value(decl: Declaration[IR]) -> IR:
    return reduce(cast(any, Function), reversed(decl.param_types), decl.definition)
