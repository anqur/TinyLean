import sys
from pathlib import Path

from pyparsing import util, exceptions

from . import ast, ir


fatal = lambda m: sys.exit(int(not print(m)))


_F = Path(sys.argv[1]) if len(sys.argv) > 1 else None


def fatal_on(text: str, loc: int, m: str):
    fatal(f"{_F}:{util.lineno(loc, text)}:{util.col(loc, text)}: {m}")


def main(file=_F if _F else fatal("usage: tinylean FILE")):
    try:
        with open(file, encoding="utf-8") as f:
            text = f.read()
            ast.check_string(text, file.suffix == ".md")
    except OSError as e:
        fatal(e)
    except exceptions.ParseException as e:
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
    except ast.UnknownCaseError as e:
        want, got, loc = e.args
        fatal_on(text, loc, f"cannot match case '{got}' of type '{want}'")
    except ast.DuplicateCaseError as e:
        name, loc = e.args
        fatal_on(text, loc, f"duplicate case '{name}'")
    except ast.CaseParamMismatchError as e:
        want, got, loc = e.args
        fatal_on(text, loc, f"want '{want}' case parameters, but got '{got}'")
    except ast.CaseMissError as e:
        miss, loc = e.args
        fatal_on(text, loc, f"missing case: {miss}")
    except ast.FieldMissError as e:
        miss, loc = e.args
        fatal_on(text, loc, f"missing field: {miss}")
    except ast.UnknownFieldError as e:
        want, got, loc = e.args
        fatal_on(text, loc, f"unknown field '{got}' of class '{want}'")
    except ir.NoInstanceError as e:
        name, loc = e.args
        fatal_on(text, loc, f"no such instance for class '{name}'")
    except RecursionError as e:
        print("Program too complex or oops you just got '⊥'! Please report this issue:")
        raise e
    except Exception as e:
        print("Internal compiler error! Please report this issue:")
        raise e


if __name__ == "__main__":
    main()
