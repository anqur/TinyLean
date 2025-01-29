from pyparsing import (
    Regex,
    Keyword,
    Group,
    unicode_set,
    Suppress,
    ParserElement,
    Forward,
    ZeroOrMore,
    Optional,
    DelimitedList,
)

ParserElement.enable_packrat()
ParserElement.set_default_whitespace_chars(" \t\r")

comment = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, TYPE = map(lambda w: Keyword(w).suppress(), "def Type".split())

NEWLINE = Suppress("\n")
ASSIGN = Suppress(":=")

LPAREN, RPAREN, LBRACE, RBRACE, COLON = map(Suppress, "(){}:")

NAME = unicode_set.identifier()

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
    + COLON
    + expr
    + ASSIGN
    + Optional(NEWLINE)
    + expr
    + NEWLINE
)

program = (
    ZeroOrMore(NEWLINE)
    + Optional(DelimitedList(definition, ZeroOrMore(NEWLINE)))
    + ZeroOrMore(NEWLINE)
).ignore(comment)
