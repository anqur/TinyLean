import sys
from pathlib import Path

import pyparsing

from . import grammar, ast


def check_string(s: str, is_markdown=False):
    return ast.TypeChecker().run(
        ast.NameResolver().run(
            list(map(lambda r: r[0][0], grammar.markdown.scan_string(s)))
            if is_markdown
            else grammar.program.parse_string(s, parse_all=True)
        )
    )


infile = lambda: Path(sys.argv[1])  # pragma: no cover


def fatal(m: str | Exception):  # pragma: no cover
    print(m)
    sys.exit(1)


def fatal_on(text: str, loc: int, m: str):  # pragma: no cover
    ln = pyparsing.util.lineno(loc, text)
    col = pyparsing.util.col(loc, text)
    fatal(f"{infile()}:{ln}:{col}: {m}")


def main():  # pragma: no cover
    try:
        with open(infile()) as f:
            text = f.read()
            check_string(text, infile().suffix == ".md")
    except IndexError:
        fatal("usage: tinylean FILE")
    except OSError as e:
        fatal(e)
    except pyparsing.exceptions.ParseException as e:
        fatal_on(text, e.loc, str(e).split("(at char")[0].strip())
    except ast.UndefinedVariableError as e:
        v, loc = e.args
        fatal_on(text, loc, f"undefined variable '{v}'")
    except ast.DuplicateVariableError as e:
        v, loc = e.args
        fatal_on(text, loc, f"duplicate variable '{v}'")
    except ast.TypeMismatchError as e:
        want, got, loc = e.args
        fatal_on(text, loc, f"type mismatch:\nwant:\n  {want}\n\ngot:\n  {got}")


if __name__ == "__main__":  # pragma: no cover
    main()
