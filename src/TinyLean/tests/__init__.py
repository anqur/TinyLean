from .. import ast, grammar

parse = lambda g, text: g.parse_string(text, parse_all=True)

resolve = lambda s: s | ast.Parser() | ast.NameResolver()
resolve_md = lambda s: s | ast.Parser(True) | ast.NameResolver()
resolve_expr = lambda s: ast.NameResolver().expr(parse(grammar.expr, s)[0])
