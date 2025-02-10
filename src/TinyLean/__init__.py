from dataclasses import dataclass, field
from functools import reduce
from operator import iadd
from typing import Type


class InternalCompilerError(Exception): ...  # pragma: no cover


_NEXT_ID = 0


def fresh():
    global _NEXT_ID
    _NEXT_ID += 1
    return _NEXT_ID


@dataclass(frozen=True)
class Ident:
    text: str
    id: int = field(default_factory=fresh)

    def __str__(self):
        return self.text

    def is_unbound(self):
        return self.text == "_"


@dataclass(frozen=True)
class Param[T]:
    name: Ident
    type: T
    implicit: bool

    def __str__(self):
        l, r = "{}" if self.implicit else "()"
        return f"{l}{self.name}: {self.type}{r}"


@dataclass(frozen=True)
class Declaration[T]:
    loc: int
    name: Ident
    params: list[Param[T]]
    ret: T
    body: T

    def to_type(self, fn_type: Type):
        return reduce(lambda a, p: fn_type(p, a), reversed(self.params), self.ret)

    def to_value(self, fn: Type):
        return reduce(lambda a, p: fn(p, a), reversed(self.params), self.body)
