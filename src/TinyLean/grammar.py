from pyparsing import *

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, EXAMPLE, INDUCTIVE, TYPE = map(
    lambda w: Suppress(Keyword(w)), "def example inductive Type".split()
)

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON, UNDER = map(Suppress, "(){}:_")
inline_one_or_more = lambda e: OneOrMore(Opt(Suppress(White(" \t\r"))) + e)

IDENT = unicode_set.identifier().set_name("IDENT")

expr, fn_type, fn, call, paren_expr, type_, placeholder, ref = map(
    lambda n: Forward().set_name(n),
    "expr function_type function call paren_expr type placeholder ref".split(),
)

expr <<= fn_type | fn | call | paren_expr | type_ | placeholder | ref

implicit_param = (LBRACE + IDENT + COLON + expr + RBRACE).set_name("implicit_param")
explicit_param = (LPAREN + IDENT + COLON + expr + RPAREN).set_name("explicit_param")
fn_type <<= (implicit_param | explicit_param) + ARROW + expr
fn <<= FUN + Group(OneOrMore(IDENT)) + TO + expr
callee = ref | paren_expr
arg = type_ | ref | paren_expr
call <<= (callee + inline_one_or_more(arg)).leave_whitespace()
paren_expr <<= LPAREN + expr + RPAREN
type_ <<= Group(TYPE)
placeholder <<= Group(UNDER)
ref <<= Group(IDENT)

return_type = Opt(COLON + expr)
params = Group(ZeroOrMore(implicit_param | explicit_param))
definition = (DEF + ref + params + return_type + ASSIGN + expr).set_name("definition")
example = (EXAMPLE + params + return_type + ASSIGN + expr).set_name("example")
declaration = (definition | example).set_name("declaration")

program = ZeroOrMore(declaration).ignore(COMMENT).set_name("program")

line_exact = lambda w: Suppress(AtLineStart(w) + LineEnd())
markdown = line_exact("```lean") + program + line_exact("```")
