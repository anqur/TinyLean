from typing import ClassVar
from dataclasses import dataclass


class InternalCompilerError(Exception): ...


@dataclass(frozen=True)
class Ident:
    id: int
    text: str

    _NEXT_ID: ClassVar[int] = 0

    def __str__(self):
        return self.text

    def is_unbound(self):
        return self.text == "_"

    @classmethod
    def fresh(cls, text: str):
        cls._NEXT_ID += 1
        return Ident(cls._NEXT_ID, text)


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


def main():
    print("Hello, TinyLean!")
