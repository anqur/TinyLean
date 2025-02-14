from dataclasses import dataclass, field


_NEXT_ID = 0


def fresh():
    global _NEXT_ID
    _NEXT_ID += 1
    return _NEXT_ID


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
class Decl[T]:
    loc: int
    name: Name
    params: list[Param[T]]
    ret: T
    body: T
