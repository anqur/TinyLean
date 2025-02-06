from pyparsing import *

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, INDUCTIVE, TYPE = map(lambda w: Suppress(Keyword(w)), "def inductive Type".split())

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON = map(Suppress, "(){}:")

NAME = unicode_set.identifier()

expr = Forward()
REFERENCE = Forward()  # NOTE: a hack for future set_parse_action
call = Forward()  # NOTE: mutual recursion workaround

param = NAME + COLON + expr
implicit_param = LBRACE + param + RBRACE
explicit_param = LPAREN + param + RPAREN

function_type = (implicit_param | explicit_param) + ARROW + expr
function = FUN + NAME + TO + expr
paren_expr = LPAREN + expr + RPAREN

expr << Group(function_type | function | call | paren_expr | TYPE | REFERENCE)
callee = Group(REFERENCE) | paren_expr
arg = Group(TYPE | REFERENCE) | paren_expr
call << (callee + OneOrMore(Opt(Suppress(White(" \t\r"))) + arg)).leave_whitespace()
REFERENCE << NAME.copy()  # NOTE: should be after `call` rule

definition = (
    DEF
    + NAME
    + Group(ZeroOrMore(implicit_param) + ZeroOrMore(explicit_param))
    + COLON  # TODO: optional return type
    + expr
    + ASSIGN
    + expr
)
declaration = Group(definition)

program = ZeroOrMore(declaration).ignore(COMMENT)
