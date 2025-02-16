from dataclasses import dataclass, field
from itertools import count

fresh = count(1).__next__


@dataclass(frozen=True)
class Name:
    text: str
    id: int = field(default_factory=fresh)

    def __str__(self):
        return self.text

    def is_unbound(self):
        return self.text == "_"


@dataclass(frozen=True)
class Param[T]:
    name: Name
    type: T
    is_implicit: bool

    def __str__(self):
        l, r = "{}" if self.is_implicit else "()"
        return f"{l}{self.name}: {self.type}{r}"


@dataclass(frozen=True)
class Decl:
    loc: int


@dataclass(frozen=True)
class Def[T](Decl):
    name: Name
    params: list[Param[T]]
    ret: T
    body: T


@dataclass(frozen=True)
class Example[T](Decl):
    params: list[Param[T]]
    ret: T
    body: T


@dataclass(frozen=True)
class Ctor[T](Decl):
    name: Name
    params: list[Param[T]]
    ty_args: list[tuple[T, T]]
    ty_name: Name | None = None


@dataclass(frozen=True)
class Data[T](Decl):
    name: Name
    params: list[Param[T]]
    ctors: list[Ctor[T]]
