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
    is_class: bool = False

    def __str__(self):
        l, r = "()" if not self.is_implicit else "{}" if not self.is_class else "[]"
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
class Sig[T](Decl):
    name: Name
    params: list[Param[T]]
    ret: T


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


@dataclass(frozen=True)
class Field[T](Decl):
    name: Name
    type: T
    cls_name: Name | None = None


@dataclass(frozen=True)
class Class[T](Decl):
    name: Name
    params: list[Param[T]]
    fields: list[Field[T]]
    instances: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class Instance[T](Decl):
    type: T
    fields: list[tuple[T, T]]
    id: int = field(default_factory=fresh)
