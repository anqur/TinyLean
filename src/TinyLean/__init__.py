from typing import ClassVar, cast, Any
from dataclasses import dataclass

trustme = lambda t: cast(Any, t)


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

    def __str__(self):
        return f"({self.name}: {self.type})"


@dataclass(frozen=True)
class Declaration[T]:
    loc: int
    name: Ident
    param_types: list[Param[T]]
    return_type: T
    definition: T


def main():
    print("Hello, TinyLean!")
