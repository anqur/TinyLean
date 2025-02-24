# TinyLean

![Supported Python versions](https://img.shields.io/pypi/pyversions/TinyLean)
![Lines of Python](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/anqurvanillapy/5d8f9b1d4b414b7076cf84f4eae089d9/raw/cloc.json)
[![Test](https://github.com/anqurvanillapy/TinyLean/actions/workflows/test.yml/badge.svg)](https://github.com/anqurvanillapy/TinyLean/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/anqurvanillapy/TinyLean/graph/badge.svg?token=M0P3GXBQDK)](https://codecov.io/gh/anqurvanillapy/TinyLean)

Tiny theorem prover in Python, with syntax like Lean 4.

## Tour

An identity function in TinyLean:

```lean
def id {T: Type} (a: T): T := a

example := id Type
```

Inductive data types:

```lean
inductive Maybe (A: Type) where
| Nothing
| Just (a: A)
open Maybe

inductive N where
| Z
| S (n: N)
open N

inductive Vec (A: Type) (n: N) where
| Nil (n := Z)
| Cons {m: N} (a: A) (v: Vec A m) (n := S m)
open Vec
```

The typechecker knows if any case is impossible (i.e. dependent pattern matching):

```lean
def v0: Vec N Z := Nil

example :=
  match v0 with
  | Nil => Z
  /- Cons is impossible, leaving it here yields errors. -/
```

So a bottom type eliminator is trivial via DPM:

```lean
inductive Weird (n: N) where
| MkWeird (n := Z)
open Weird

/- Impossible to construct a term for type `Weird (S Z)`. -/
example {A: Type} (x: Weird (S Z)): A := nomatch x
```

## License

MIT
