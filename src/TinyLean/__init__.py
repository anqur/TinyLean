from typing import ClassVar
from dataclasses import dataclass


@dataclass
class Ident:
    text: str = ""
    id: int = 0

    _NEXT_ID: ClassVar[int] = 0

    def __str__(self):
        return self.text

    @classmethod
    def fresh(cls, text: str):
        cls._NEXT_ID += 1
        return Ident(text, cls._NEXT_ID)


def main():
    print("Hello, TinyLean!")
