from pyparsing import ParserElement

from .. import ast, grammar


def parse(g: ParserElement, text: str):
    return g.parse_string(text, parse_all=True)


def resolve(s: str):
    return s | ast.Parser() | ast.NameResolver()


def resolve_md(s: str):
    return s | ast.Parser(True) | ast.NameResolver()


def resolve_expr(s: str):
    return ast.NameResolver().expr(parse(grammar.expr, s)[0])
