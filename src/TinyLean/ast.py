from dataclasses import dataclass, field

from . import Ident, Param, Declaration


@dataclass(frozen=True)
class Node:
    loc: int


@dataclass(frozen=True)
class Type(Node): ...


@dataclass(frozen=True)
class Reference(Node):
    name: Ident


@dataclass(frozen=True)
class FunctionType(Node):
    param_type: Param[Node]
    return_type: Node


@dataclass(frozen=True)
class Function(Node):
    param_name: Ident
    body: Node


@dataclass(frozen=True)
class Call(Node):
    callee: Node
    arg: Node


class NameResolveError(Exception): ...


@dataclass(frozen=True)
class NameResolver:
    locals: dict[str, Ident] = field(default_factory=dict)
    globals: set[str] = field(default_factory=set)

    def resolve(self, decls: list[Declaration[Node]]):
        return [self._resolve_def(d) for d in decls]

    def _resolve_def(self, d: Declaration[Node]):
        params = []
        for name, ty in d.param_types:
            self._insert_local(name)
            params.append(Param(name, self._resolve_expr(ty)))
        ret = self._resolve_expr(d.return_type)
        body = self._resolve_expr(d.definition)

        if not d.name.is_unbound():
            if d.name.text in self.globals:
                raise NameResolveError("duplicate variable", d.loc, d.name.text)
            self.globals.add(d.name.text)

        self.locals.clear()
        return Declaration(d.loc, d.name, params, ret, body)

    def _resolve_expr(self, node: Node) -> Node:
        match node:
            case Reference(loc, v):
                try:
                    return Reference(loc, self.locals[v.text])
                except KeyError:
                    raise NameResolveError("undefined variable", v.loc, v.text)
            case FunctionType(loc, p, body):
                typ = self._resolve_expr(p.type)
                b = self._guard_local(p.name, body)
                return FunctionType(loc, Param(p.name, typ), b)
            case Function(loc, v, body):
                b = self._guard_local(v, body)
                return Function(loc, v, b)
            case Call(loc, f, x):
                return Call(loc, self._resolve_expr(f), self._resolve_expr(x))
            case Type(_):
                return node
        raise AssertionError("impossible")

    def _guard_local(self, v: Ident, node: Node):
        old = self._insert_local(v)
        ret = self._resolve_expr(node)
        if old:
            self._insert_local(old)
        else:
            del self.locals[v.text]
        return ret

    def _insert_local(self, v: Ident):
        old = None
        try:
            old = self.locals[v.text]
        except KeyError:
            pass
        self.locals[v.text] = v
        return old
