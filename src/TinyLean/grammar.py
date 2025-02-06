from pyparsing import *

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, INDUCTIVE = map(lambda w: Suppress(Keyword(w)), "def inductive".split())

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON = map(Suppress, "(){}:")

IDENT = unicode_set.identifier().set_name("identifier")

# NOTE: a hack for future set_parse_action
expr, REFERENCE, TYPE, call = map(
    lambda n: Forward().set_name(n),
    "expression,reference,type,function call".split(","),
)

annotated = IDENT + COLON + expr
implicit_param = (LBRACE + annotated + RBRACE).set_name("implicit parameter")
explicit_param = (LPAREN + annotated + RPAREN).set_name("explicit parameter")
param = implicit_param | explicit_param

function_type = (param + ARROW + expr).set_name("function type")
function = (FUN + IDENT + TO + expr).set_name("function")
paren_expr = LPAREN + expr + RPAREN

expr << Group(function_type | function | call | paren_expr | TYPE | REFERENCE)
callee = Group(REFERENCE) | paren_expr
arg = Group(TYPE | REFERENCE) | paren_expr
call << (callee + OneOrMore(Opt(Suppress(White(" \t\r"))) + arg)).leave_whitespace()
REFERENCE << IDENT.copy()  # NOTE: should keep unknown for rules that depend on this
TYPE << Keyword("Type")  # NOTE: ditto

definition = (
    DEF
    + REFERENCE
    + Group(ZeroOrMore(implicit_param) + ZeroOrMore(explicit_param))
    + COLON  # TODO: optional return type
    + expr
    + ASSIGN
    + expr
).set_name("definition")
declaration = Group(definition).set_name("declaration")

program = ZeroOrMore(declaration).ignore(COMMENT).set_name("program")
