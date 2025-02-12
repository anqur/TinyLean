import sys
from pathlib import Path

import pyparsing

from . import ast


infile = lambda: Path(sys.argv[1])


def fatal(m: str | Exception):
    print(m)
    sys.exit(1)


def fatal_on(text: str, loc: int, m: str):
    ln = pyparsing.util.lineno(loc, text)
    col = pyparsing.util.col(loc, text)
    fatal(f"{infile()}:{ln}:{col}: {m}")


def main():
    try:
        with open(infile()) as f:
            text = f.read()
            ast.check_string(text, infile().suffix == ".md")
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
    except ast.UnsolvedPlaceholderError as e:
        name, ctx, ty, loc = e.args
        ty_msg = f"  {name} : {ty}"
        ctx_msg = "".join([f"\n  {p}" for p in ctx.values()]) if ctx else " (none)"
        fatal_on(text, loc, f"unsolved placeholder:\n{ty_msg}\n\ncontext:{ctx_msg}")
    except AssertionError as e:
        print("Internal compiler error! Please report this issue:")
        raise e


if __name__ == "__main__":
    main()
