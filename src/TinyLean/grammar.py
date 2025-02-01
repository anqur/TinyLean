from pyparsing import *

ParserElement.enable_packrat()

comment = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, INDUCTIVE, TYPE = map(
    lambda w: Keyword(w).suppress(), "def inductive Type".split()
)

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON = map(Suppress, "(){}:")

NAME = unicode_set.identifier()
NEWLINE = Opt(Suppress(White(" \t\r"))) + Suppress("\n")

oneline = lambda e: (e + NEWLINE).leave_whitespace()
parenthesized = lambda e: LPAREN + e + RPAREN
braced = lambda e: LBRACE + e + RBRACE

expr = Forward()
paren_expr = parenthesized(expr)

param = Group(NAME + COLON + expr)
implicit_param = braced(param)
explicit_param = parenthesized(param)

function_type = ZeroOrMore(implicit_param) + OneOrMore(explicit_param) + ARROW + expr
function = FUN + NAME + TO + expr
call = (NAME | paren_expr) + expr

expr << Group(function_type | function | TYPE | oneline(call) | NAME | paren_expr)

definition = Group(
    DEF
    + NAME
    + ZeroOrMore(implicit_param)
    + ZeroOrMore(explicit_param)
    + Opt(COLON + expr)
    + ASSIGN
    + oneline(expr)
)

program = ZeroOrMore(definition).ignore(comment).set_parse_action()
