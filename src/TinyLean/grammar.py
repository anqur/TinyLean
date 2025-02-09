from pyparsing import *

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

# NOTE: a hack for future set_parse_action
expr, function_type, function, REF, TYPE, call, paren_expr, PLACEHOLDER = map(
    lambda n: Forward().set_name(n),
    "expr function_type function REF TYPE call paren_expr PLACEHOLDER".split(),
)

expr << Group(function_type | function | call | paren_expr | TYPE | PLACEHOLDER | REF)

annotated = IDENT + COLON + expr
implicit_param = (LBRACE + annotated + RBRACE).set_name("implicit_param")
explicit_param = (LPAREN + annotated + RPAREN).set_name("explicit_param")

function_type << Group((implicit_param | explicit_param) + ARROW + expr)
function << Group(FUN + IDENT + TO + expr)
callee = REF | paren_expr
arg = TYPE | REF | paren_expr
call << Group(callee + inline_one_or_more(arg)).leave_whitespace()
paren_expr << Group(LPAREN + expr + RPAREN)
TYPE << Group(TYPE_)
PLACEHOLDER << Group(UNDER)
REF << Group(IDENT)

return_type = Opt(COLON + expr)
params = Group(ZeroOrMore(implicit_param) + ZeroOrMore(explicit_param))
definition = (DEF + REF + params + return_type + ASSIGN + expr).set_name("definition")
example = (EXAMPLE + params + return_type + ASSIGN + expr).set_name("example")
declaration = (definition | example).set_name("declaration")

program = ZeroOrMore(declaration).ignore(COMMENT).set_name("program")

line_exact = lambda w: Suppress(AtLineStart(w) + LineEnd())
markdown = line_exact(f"```lean") + program + line_exact("```")
