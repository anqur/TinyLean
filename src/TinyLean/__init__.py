from typing import ClassVar
from dataclasses import dataclass


@dataclass
class Ident:
    text: str = ""
    id: int = 0

    _NEXT_ID: ClassVar[int] = 0

    def __str__(self):
        return self.text

    def is_unbound(self):
        return self.text == "_"

    @classmethod
    def fresh(cls, text: str):
        cls._NEXT_ID += 1
        return Ident(text, cls._NEXT_ID)


@dataclass
class Param[T]:
    name: Ident
    type: T

    def __str__(self):
        return f"({self.name}: {self.type})"


def main():
    print("Hello, TinyLean!")
