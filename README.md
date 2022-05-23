# Pakettic

Pakettic is a command-line tool for minifying and compressing
[TIC-80](http://tic80.com/) fantasy console carts. The tool is written
in Python (3.9+) and used especially for
[sizecoding](http://www.sizecoding.org/wiki/TIC-80).

## Installation

Pakettic uses [poetry](https://python-poetry.org/) for managing
dependencies. After checking out the repo, setup a virtual environment
and install dependencies by running:

```bash
poetry install
```

## Usage

While inside the pakettic folder, run:

```bash
poetry run pakettic path/to/cart.tic
```

See all command line options by running:

```bash
poetry run pakettic --help
```

Running all tests:

```bash
poetry run python -m unittest discover -s tests
```

## Features

- The packer parses the LUA source code and then uses a
  [simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing)
  algorithm to randomly make mutations to the abstract syntax tree, to
  see if it packs better.
- The algorithm swaps randomly expressions, so `a+b` can become `b+a`.
  Operators `*`, `+`, `&`, `~`, `|`, `>`, `<`, `>=`, `<=`, `~=`, `==`
  might get swapped and the right branches of `+-` ops and `*/` ops
  might get swapped.
- There is a special `---` operator that allows alternative expressions
  to be tried. For example: `5---4---6` means that the algorithm will
  try 4 and 6 in place of the 5, to see if it compresses better. This
  will naturally show up as a comment in LUA so you have to continue the
  expression on next line. `---` has the lowest precedence, even lower
  than `^` so put parentheses if you want to try more complicated
  expressions e.g. `(x//256)---(x>>8)`
- Unnecessary parentheses are removed so you do not have to worry about
  those.
- `load'<some-code-here>'` is parsed as `function()<some-code-here>end`
  so you can happily recompress already compressed carts.
- Another special comment is a pair of `--{` and `--}`. The algorithm
  tries to reorder all statements between these to see if it compresses
  better.

## Known issues

- At the moment, all the branches of swappable operators are assumed to
  be without side effects. If they have side-effects, the swapping might
  inadvertedly swap the execution order of the two branches.

## Credits

[Veikko Sariola](https://github.com/vsariola) aka pestis/brainlez
Coders!

## License

[MIT](LICENSE)