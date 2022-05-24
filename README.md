# Pakettic

Pakettic is a command-line tool for minifying and compressing
[TIC-80](http://tic80.com/) fantasy console carts. The tool is written
in Python (3.9+) and used especially for
[sizecoding](http://www.sizecoding.org/wiki/TIC-80).

## Installation

Pakettic is not yet published in PyPI, but you can use pip to install it
with the `-e` option. After checking out the repo to folder `pakettic`,
run:

```bash
pip install -e path/to/pakettic
```

This will install it globally. Alternatively, if you can use
[poetry](https://python-poetry.org/) to install it in a nice virtual
environment with locked dependencies. Inside the pakettic folder, run:

```bash
poetry install
```

## Usage

To compress a cart, run:

```bash
pakettic path/to/cart.tic
```

If you installed using poetry into a virtual environment, you need to
prepend `poetry run` before every command i.e.

```bash
poetry run pakettic path/to/cart.tic
```

Pakettic supports both .tic and .lua carts. Multiple input files may be
defined. Input files are globbed, so `?`, `*`, and `**` work as
wildcards for a single character, multiple characters and a directory,
respectively.

For a full list of command line options, see:

```bash
pakettic --help
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
- There is a special `--|` operator that allows alternative expressions
  to be tested to see if they compress better. For example: `5--|4--|6`
  means that the algorithm will try 4 and 6 in place of the 5. This will
  naturally show up as a comment in LUA so you will have to continue the
  expression on next line if this is in the middle of an expression.
  `--|` has the lowest precedence, even lower than `^` so put
  parentheses if you want to try more complicated expressions e.g.
  `(x//256)--|(x>>8)`
- Unnecessary parentheses are removed so you do not have to worry about
  those.
- `load'<some-code-here>'` is parsed as `function()<some-code-here>end`
  so you can easily recompress already compressed carts.
- Another special comment is a pair of `--{` and `--}`. The algorithm
  assumes its ok to reorder all statements between these to see if it
  compresses better. For example, to try whether `x=0y=0` or `y=0x=0`
  compresses better, use:
```lua
 --{
 x=0
 y=0
 --}
```

## Known issues

- At the moment, all the branches of swappable operators are assumed to
  be without side effects. If they have side-effects, the swapping might
  inadvertedly swap the execution order of the two branches.

## Credits

[Veikko Sariola](https://github.com/vsariola) aka pestis/brainlez
Coders!

## License

[MIT](LICENSE)