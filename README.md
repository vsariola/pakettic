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

See also [tips for command line arguments](#tips-for-command-line-arguments)

Running all tests:

```bash
$ poetry run python -m unittest discover -s tests
```

## Features

Pakettic first parses the LUA-script to an abstract syntax tree, and
then uses a local optimization algorithm
([simulated annealing](https://en.wikipedia.org/wiki/Simulated_annealing),
[late acceptance hill climbing](https://arxiv.org/pdf/1806.09328.pdf) or
its variant diversified late acceptance search) to randomly mutate the
syntax tree & see if it compresses better. Implemented mutations
include:
  - shortening variable names
  - flipping comparisons `>`, `<`, `>=`, `<=`, `~=`, and `==`
  - reordering arithmetic operators `+`, `-`, `*` and `/` and bit logic
    operators `&`, `~` and `|`
  - using either single or double quotes for all strings
  - converting whole hexadecimals into decimals
  - convert `for a,b,1 do` into `for a,b do` and vice versa
  - reordering statements: statements that can be reordered are marked
    with [magic comments](#magic-comments)
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

Notice that only complete statements can be reordered. Thus, this will
NOT work:

```lua
 --{
 for x=0,239 do
  for y=0,135 do
 --}
  end
 end
```

A good rule of thumb is that you should be able to replace `--{` and
`--}` with `do` and `end`, respectively, and still have valid code.

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

## Tips for command line arguments

- Cranking up the Zopfli settings can usually save a few more bytes,
  with the expense of slowing down the optimization considerably. Try
  `-z3` to set the Zopfli-level. By default, the Zopfli-level is 2, and
  it goes up to 5.
- The algorithm uses a pseudorandom generator. Sometimes using a
  different seed finds a few byte better or worse solution. Use command
  line argument `--seed` to try different seeds.
- Similarly, different optimization heuristics produce slightly
  different results. Try different heuristics e.g. with `-alahc`,
  `-adlas` or `-aanneal`.
- To avoid re-optimizing all the expressions every time, do a long
  optimization run, study the results and change your expressions to the
  forms that pack well. Set the number of steps with `-s`. Use
  command-line argument `-p` to always print a reasonably readable
  version of the best solution when one is found.
- By default, pakettic only includes CODE and DEFAULT chunks. DEFAULT
  indicates that before loading the cart, TIC-80 loads the default cart,
  setting default palette, waveforms etc. If you don't need the default
  values (e.g. you set the palette yourself), save one byte by only
  including CODE chunk in the cart: `-ccode`
- Working on a tweet-cart? Use `-l` to output LUA carts, which are
  uncompressed. The optimization algorithm then just optimizes the
  uncompressed size of the code.

## Known issues

- At the moment, all the branches of swappable operators are assumed to
  be without side effects. If they have side-effects, the swapping might
  inadvertedly swap the execution order of the two branches.

## Credits

[Veikko Sariola](https://github.com/vsariola) aka pestis/brainlez
Coders!

## License

[MIT](LICENSE)