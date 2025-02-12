from functools import reduce

from pyparsing import *

from . import Declaration, Param, Ident, ast

COMMENT = Regex(r"/\-(?:[^-]|\-(?!/))*\-\/").set_name("comment")

DEF, EXAMPLE, INDUCTIVE, TYPE_ = map(
    lambda w: Suppress(Keyword(w)), "def example inductive Type".split()
)

ASSIGN, ARROW, FUN, TO = map(
    lambda s: Suppress(s[0]) | Suppress(s[1:]), "≔:= →-> λfun ↦=>".split()
)

LPAREN, RPAREN, LBRACE, RBRACE, COLON, UNDER = map(Suppress, "(){}:_")
inline_one_or_more = lambda e: OneOrMore(Opt(Suppress(White(" \t\r"))) + e)

IDENT = unicode_set.identifier().set_name("IDENT")
IDENT.set_parse_action(lambda r: Ident(r[0]))

# NOTE: a hack for future set_parse_action
expr, function_type, function, REF, TYPE, call, paren_expr, PLACEHOLDER = map(
    lambda n: Forward().set_name(n),
    "expr function_type function REF TYPE call paren_expr PLACEHOLDER".split(),
)

expr <<= function_type | function | call | paren_expr | TYPE | PLACEHOLDER | REF

implicit_param = (LBRACE + IDENT + COLON + expr + RBRACE).set_name("implicit_param")
implicit_param.set_parse_action(lambda r: Param(r[0], r[1], True))

explicit_param = (LPAREN + IDENT + COLON + expr + RPAREN).set_name("explicit_param")
explicit_param.set_parse_action(lambda r: Param(r[0], r[1], False))

function_type <<= (implicit_param | explicit_param) + ARROW + expr
function_type.set_parse_action(lambda l, r: ast.FnType(l, r[0], r[1]))

function <<= FUN + Group(OneOrMore(IDENT)) + TO + expr
function.set_parse_action(
    lambda l, r: reduce(lambda a, n: ast.Fn(l, n, a), reversed(r[0]), r[1])
)

callee = REF | paren_expr
arg = TYPE | REF | paren_expr
call <<= (callee + inline_one_or_more(arg)).leave_whitespace()
call.set_parse_action(lambda l, r: reduce(lambda a, b: ast.Call(l, a, b), r[1:], r[0]))

paren_expr <<= LPAREN + expr + RPAREN
paren_expr.set_parse_action(lambda r: r[0])

TYPE <<= TYPE_
TYPE.set_parse_action(lambda l, r: ast.Type(l))

PLACEHOLDER <<= UNDER
PLACEHOLDER.set_parse_action(lambda l, r: ast.Placeholder(l, True))

REF <<= IDENT
REF.set_parse_action(lambda l, r: ast.Ref(l, r[0]))

return_type = Opt(COLON + expr)
return_type.set_parse_action(lambda l, r: r[0] if len(r) else ast.Placeholder(l, False))

params = Group(ZeroOrMore(implicit_param | explicit_param))
definition = (DEF + REF + params + return_type + ASSIGN + expr).set_name("definition")
definition.set_parse_action(
    lambda r: Declaration(r[0].loc, r[0].name, list(r[1]), r[2], r[3])
)

example = (EXAMPLE + params + return_type + ASSIGN + expr).set_name("example")
example.set_parse_action(
    lambda l, r: Declaration(l, Ident("_"), list(r[0]), r[1], r[2])
)

declaration = (definition | example).set_name("declaration")

program = ZeroOrMore(declaration).ignore(COMMENT).set_name("program")

line_exact = lambda w: Suppress(AtLineStart(w) + LineEnd())
markdown = line_exact("```lean") + program + line_exact("```")
