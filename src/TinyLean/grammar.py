from pyparsing import (
    Regex,
    Keyword,
    Group,
    unicode_set,
    Suppress,
    ParserElement,
    Forward,
    ZeroOrMore,
    White,
    Opt,
)

ParserElement.enable_packrat()

comment = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, TYPE = map(lambda w: Keyword(w).suppress(), "def Type".split())

ASSIGN = Suppress(":=")

LPAREN, RPAREN, LBRACE, RBRACE, COLON = map(Suppress, "(){}:")

NAME = unicode_set.identifier()
NEWLINE = Opt(Suppress(White(" \t\r"))) + Suppress("\n")

oneline = lambda e: (e + NEWLINE).leave_whitespace()
parenthesized = lambda e: LPAREN + e + RPAREN
braced = lambda e: LBRACE + e + RBRACE

expr = Forward()
expr << Group(TYPE | NAME | parenthesized(expr))

param = Group(NAME + COLON + expr)
implicit_param = braced(param)
explicit_param = parenthesized(param)

definition = Group(
    DEF
    + NAME
    + ZeroOrMore(implicit_param)
    + ZeroOrMore(explicit_param)
    + Opt(COLON + expr)
    + ASSIGN
    + oneline(expr)
)

program = ZeroOrMore(definition).ignore(comment)
