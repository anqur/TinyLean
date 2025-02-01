from dataclasses import dataclass

from . import Ident, Param


@dataclass
class IR: ...


@dataclass
class Reference(IR):
    v: Ident

    def __str__(self):
        return str(self.v)


@dataclass
class Type(IR):
    def __str__(self):
        return "Type"


@dataclass
class FunctionType(IR):
    param_type: Param[IR]
    return_type: IR

    def __str__(self):
        return f"{self.param_type} → {self.return_type}"


@dataclass
class Function(IR):
    param: Param[IR]
    body: IR

    def __str__(self):
        return f"λ {self.param} ↦ {self.body}"


@dataclass
class Call(IR):
    callee: IR
    arg: IR

    def __str__(self):
        return f"({self.callee} {self.arg})"
