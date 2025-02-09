# TinyLean

[![codecov](https://codecov.io/gh/anqurvanillapy/TinyLean/graph/badge.svg?token=M0P3GXBQDK)](https://codecov.io/gh/anqurvanillapy/TinyLean)

Tiny theorem prover in Python, with syntax like Lean 4.

## Tour

An identity function in TinyLean:

```lean
def id {T: Type} (a: T): T := a

example: Type := id Type
```

## License

MIT
