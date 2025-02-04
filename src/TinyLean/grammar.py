from pyparsing import *

ParserElement.enable_packrat()

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, INDUCTIVE, TYPE = map(lambda w: Suppress(Keyword(w)), "def inductive Type".split())

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON = map(Suppress, "(){}:")

NAME = unicode_set.identifier()
INLINE_WHITE = Opt(Suppress(White(" \t\r")))

parenthesized = lambda e: LPAREN + e + RPAREN
braced = lambda e: LBRACE + e + RBRACE

expr = Forward()
paren_expr = parenthesized(expr)

param = NAME + COLON + expr
implicit_param = braced(param)
explicit_param = parenthesized(param)

function_type = (implicit_param | explicit_param) + ARROW + expr
function = FUN + NAME + TO + expr
call = ((NAME | paren_expr) + OneOrMore(INLINE_WHITE + expr)).leave_whitespace()
REFERENCE = NAME.copy()

expr << Group(function_type | function | call | paren_expr | TYPE | REFERENCE)

definition = Group(
    DEF
    + NAME
    + ZeroOrMore(implicit_param)
    + ZeroOrMore(explicit_param)
    + COLON  # TODO: optional return type
    + expr
    + ASSIGN
    + expr
)

program = ZeroOrMore(definition).ignore(COMMENT)
