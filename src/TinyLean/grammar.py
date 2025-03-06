from pyparsing import *

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

IDENT = unicode_set.identifier()

DEF, EXAMPLE, IND, WHERE, OPEN, TYPE, NOMATCH, MATCH, WITH, UNDER, CLASS, INST = map(
    lambda w: Suppress(Keyword(w)),
    "def example inductive where open Type nomatch match with _ class instance".split(),
)

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET, COLON, BAR, NEWLINE = map(
    Suppress, "(){}[]:|\n"
)
INLINE_WHITE = Opt(Suppress(White(" \t\r"))).set_name("inline_whitespace")

forwards = lambda names: map(lambda n: Forward().set_name(n), names.split())

expr, fn_type, fn, match, nomatch, call, p_expr, type_, ph, ref = forwards(
    "expr fn_type fn match nomatch call paren_expr type placeholder ref"
)
case, i_arg, e_arg = forwards("case implicit_arg explicit_arg")

expr <<= fn_type | fn | match | nomatch | call | p_expr | type_ | ph | ref

name = Group(IDENT).set_name("name")
i_param = (LBRACE + name + COLON + expr + RBRACE).set_name("implicit_param")
e_param = (LPAREN + name + COLON + expr + RPAREN).set_name("explicit_param")
c_param = (LBRACKET + expr + RBRACKET).set_name("constraint_param")
param = (i_param | e_param | c_param).set_name("param")
fn_type <<= param + ARROW + expr
fn <<= FUN + Group(OneOrMore(name)) + TO + expr
match <<= MATCH + (type_ | ref | p_expr) + WITH + Group(OneOrMore(case))
case <<= BAR + ref + Group(ZeroOrMore(name)) + TO + expr
nomatch <<= (NOMATCH + INLINE_WHITE + e_arg).leave_whitespace()
callee = ref | p_expr
call <<= (callee + OneOrMore(INLINE_WHITE + (i_arg | e_arg))).leave_whitespace()
i_arg <<= LPAREN + IDENT + ASSIGN + expr + RPAREN
e_arg <<= (type_ | ref | p_expr).leave_whitespace()
p_expr <<= LPAREN + expr + RPAREN
type_ <<= Group(TYPE)
ph <<= Group(UNDER)
ref <<= Group(name)

return_type = Opt(COLON + expr)
params = Group(ZeroOrMore(param))
definition = (DEF + ref + params + return_type + ASSIGN + expr).set_name("definition")
example = (EXAMPLE + params + return_type + ASSIGN + expr).set_name("example")
type_arg = (LPAREN + ref + ASSIGN + expr + RPAREN).set_name("type_arg")
ctor = (BAR + ref + params + Group(ZeroOrMore(type_arg))).set_name("constructor")
data = (IND + ref + params + WHERE + Group(ZeroOrMore(ctor)) + OPEN + IDENT).set_name(
    "datatype"
)
c_field = (name + COLON + expr).set_name("class_field")
class_ = (
    CLASS + ref + params + WHERE + Group(ZeroOrMore(c_field)) + OPEN + IDENT
).set_name("class")
i_field = (ref + ASSIGN + expr).set_name("instance_field")
inst = (INST + COLON + expr + WHERE + Group(ZeroOrMore(i_field))).set_name("instance")
declaration = (definition | example | data | class_).set_name("declaration")

program = ZeroOrMore(declaration).ignore(COMMENT).set_name("program")

line_exact = lambda w: Suppress(AtLineStart(w) + LineEnd())
markdown = line_exact("```lean") + program + line_exact("```")
