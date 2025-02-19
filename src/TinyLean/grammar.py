from pyparsing import *

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

IDENT = unicode_set.identifier()

DEF, EXAMPLE, INDUCTIVE, WHERE, OPEN, TYPE, NOMATCH = map(
    lambda w: Suppress(Keyword(w)),
    "def example inductive where open Type nomatch".split(),
)

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON, UNDER, BAR = map(Suppress, "(){}:_|")
I_WHITE = Opt(Suppress(White(" \t\r"))).set_name("inline_whitespace")

expr, fn_type, fn, nomatch, call, i_arg, e_arg, p_expr, type_, ph, ref = map(
    lambda n: Forward().set_name(n),
    "expr fn_type fn nomatch call implicit_arg explicit_arg paren_expr type placeholder ref".split(),
)

expr <<= fn_type | fn | nomatch | call | p_expr | type_ | ph | ref

name = Group(IDENT).set_name("name")
i_param = (LBRACE + name + COLON + expr + RBRACE).set_name("implicit_param")
e_param = (LPAREN + name + COLON + expr + RPAREN).set_name("explicit_param")
fn_type <<= (i_param | e_param) + ARROW + expr
fn <<= FUN + Group(OneOrMore(name)) + TO + expr
nomatch = (NOMATCH + I_WHITE + e_arg).leave_whitespace()
callee = ref | p_expr
call <<= (callee + OneOrMore(I_WHITE + (i_arg | e_arg))).leave_whitespace()
i_arg <<= LPAREN + IDENT + ASSIGN + expr + RPAREN
e_arg <<= (type_ | ref | p_expr).leave_whitespace()
p_expr <<= LPAREN + expr + RPAREN
type_ <<= Group(TYPE)
ph <<= Group(UNDER)
ref <<= Group(name)

return_type = Opt(COLON + expr)
params = Group(ZeroOrMore(i_param | e_param))
definition = (DEF + ref + params + return_type + ASSIGN + expr).set_name("definition")
example = (EXAMPLE + params + return_type + ASSIGN + expr).set_name("example")
type_arg = (LPAREN + ref + ASSIGN + expr + RPAREN).set_name("type_arg")
ctor = (
    BAR + ref + Group(ZeroOrMore(i_param | e_param)) + Group(ZeroOrMore(type_arg))
).set_name("constructor")
data = (
    INDUCTIVE + ref + params + WHERE + Group(ZeroOrMore(ctor)) + OPEN + IDENT
).set_name("datatype")
declaration = (definition | example | data).set_name("declaration")

program = ZeroOrMore(declaration).ignore(COMMENT).set_name("program")

line_exact = lambda w: Suppress(AtLineStart(w) + LineEnd())
markdown = line_exact("```lean") + program + line_exact("```")
