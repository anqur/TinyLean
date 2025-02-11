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

## License

MIT
