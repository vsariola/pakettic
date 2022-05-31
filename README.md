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
$ pip install -e path/to/pakettic
```

This will install it globally. Alternatively, you can use
[poetry](https://python-poetry.org/) to install it in a nice virtual
environment with locked dependencies. Inside the pakettic folder:

```bash
$ poetry install
```

## Usage

To compress a cart, run:

```bash
$ pakettic path/to/cart.tic
```

If your PATH is not configured to include pip installed executables, you
can use

```bash
$ python -m pakettic path/to/cart.tic
```

If you installed using poetry into a virtual environment, you need to
prepend `poetry run` before every command e.g.

```bash
$ poetry run pakettic path/to/cart.tic
```

Pakettic supports both .tic and .lua carts. Multiple input files may be
defined. Input files are globbed, so `?`, `*`, and `**` work as
wildcards for a single character, multiple characters and a directory,
respectively.

For a full list of command line options, see:

```bash
$ pakettic --help
```

Running all tests:

```bash
$ poetry run python -m unittest discover -s tests
```

## Features

Pakettic first parses the LUA-script to an abstract syntax tree, and
then uses a local optimization algorithm -
[simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing)
or
[late acceptance hill climbing](https://en.wikipedia.org/wiki/Late_acceptance_hill_climbing)
- to randomly mutate the syntax tree & see if it compresses better.
Implemented mutations include:
  - shortening variable names
  - flipping binary operators `*`, `+`, `&`, `~`, `|`, `>`, `<`, `>=`,
    `<=`, `~=`, and `==`
  - swapping right branches of `+-` ops and `*/` ops
  - reordering statements: statements that can be reordered are marked with [magic comments](#magic-comments)
  - alternative expressions: alternatives are marked with
    [magic comments](#magic-comments)

Internally, pakettic uses [zopfli](https://github.com/google/zopfli) for
actual compression.

`load'...'` is parsed as `function()...end` so you can easily recompress
already compressed carts. Conversely, `function()...end` is replaced
with `load'...'` during compression.

Unnecessary parentheses are removed from expressions so you do not have
to worry about those.

## Magic comments

### Reorderable statements

The algorithm will try to reorder statements between `--{` and `--}`.
For example:

```lua
 --{
 a="hello"
 b="world"
 --}
```

will try both `a="hello"b="world"` and `b="world"a="hello"` to see if
compresses better.

Statements between `--{!` and `--}` are not ordered, so you can make
blocks of statements that are kept in order within a pair of `--{` and
`--}` tags.

### Alternative expressions

There is a special `--|` operator that allows alternative expressions to
be tested, to see if they compress better. For example: `5--|4--|6`
means that the algorithm will try 4 and 6 in place of the 5. This will
naturally show up as a comment in LUA so you will have to continue the
expression on next line if this is in the middle of an expression. `--|`
has the lowest precedence, even lower than `^` so put parentheses if you
want to try more complicated expressions e.g. `(x//256)--|(x>>8)`

## Known issues

- At the moment, all the branches of swappable operators are assumed to
  be without side effects. If they have side-effects, the swapping might
  inadvertedly swap the execution order of the two branches.

## Credits

[Veikko Sariola](https://github.com/vsariola) aka pestis/brainlez
Coders!

## License

[MIT](LICENSE)