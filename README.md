# Pakettic

Pakettic is a command-line tool for minifying and compressing
[TIC-80](http://tic80.com/) fantasy console carts. The tool is written
in Python (3.9+) and used especially for
[sizecoding](http://www.sizecoding.org/wiki/TIC-80). It compresses
existing carts approximately ~1.2% better than best alternatives, and by
using its [magic comments](#magic-comments), pakettic might find code
that compresses even better.

## Installation

Installing with pip:

```bash
$ pip install pakettic
```

Installing the latest main branch from GitHub:

```bash
$ pip install git+https://github.com/vsariola/pakettic.git@main
```

Installing a checked out version of the repository:

```bash
$ pip install -e path/to/pakettic
```

Installing a checked out version of the repository using
[poetry](https://python-poetry.org/) for a nice virtual environment with
locked dependencies (run inside the pakettic folder):

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
  - converting `a^2` into `a*a` and vice versa
  - using either single or double quotes for all strings
  - converting whole hexadecimals into decimals
  - convert `for a,b,1 do` into `for a,b do` and vice versa
  - reordering statements: statements that can be reordered are marked
    with [magic comments](#magic-comments)
  - alternative expressions: alternatives are marked with
    [magic comments](#magic-comments)
  - folding constant expressions

Internally, pakettic uses [zopfli](https://github.com/google/zopfli) for
the compression.

`load'<code>'` is parsed as `function(...)<code>end` so you can easily
recompress already compressed carts. Conversely, `function()<code>end`
or `function(...)<code>end` is replaced with `load'<code>'` during
compression.

Note that `function(...)<code>end` and `load'<code>'` are not 100%
semantically identical: the load version cannot access locals in the outer
scope. For example: `local x="hello" function f()print(x)end` works but
`local x="hello" f=load'print(x)'` does not. Since locals are rarely
used in size-coding, we default to using the load-trick, but you can
disable it with the command-line parameter `--no-load`.

However, pakettic does not convert functions with parameters. In
particular, pakettic does not automatically convert
`function SCN(x)<code>end` into `SCN=load'x=...<code>'`, because they
are not semantically identical: in the load version, `x` is now global
and thus could trash a global variable, unintentionally breaking the
cart. To make `SCN` compress nicely, you have to write it as
`function SCN(...)x=...<code>end`, taking responsibility for `x` not
overwriting anything important.

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

will try both `a="hello"b="world"` and `b="world"a="hello"` to see which
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
has the lowest precedence, even lower than `^`, so put parentheses if
you want to try more complicated expressions e.g. `(x//256)--|(x>>8)`

### Debug code

Pakettic treats `--![` and `--!]` as multiline comment tags, while LUA
treats these as single line comments. Useful for including debug code in
the unpacked intro: the code will not be included in the packed cart.

## Tips for command line arguments

- If pakettic complains about CODE_ZIP chunk size, the code is just too
  big after compression. In TIC-80, CODE_ZIP chunks do not support
  multiple banks (and likely never will, as the feature is already
  deprecated), and thus are unfortunately limited to 65535 bytes.
  `--uncompressed` is a temporary fix, but code will be uncompressed and
  thus the size much larger.
- The Zopfli compression level can be set with `-z<level>`, with level
  ranging from 0 to 5. When developing, start with `-z0` for fast
  optimization, and only increase when necessary e.g. when you are just
  a few bytes over the limit. The default Zopfli-level is 0.
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
- If the packed cart is missing sprites, music, map etc., try adding
  `-call` (or something more specific) to include necessary chunks.
- Do you want to use the TIC-80 sprites or the tracker, but don't like
  the fact that the data chunks are uncompressed? Use `-d` to have
  pakettic automatically convert all data chunks into hexadecimal
  strings in the code, along with a small stub placed at the beginning
  of the code that interprets the string and loads the data at correct
  address. For example,
  `-d -cCODE,MUSIC,PATTERNS,WAVEFORM,SAMPLES,DEFAULT` would include the
  necessary chunks for the music.

## Known issues

- At the moment, all the branches of swappable operators are assumed to
  be without side effects. If they have side-effects, the swapping might
  inadvertedly swap the execution order of the two branches.
- The parser can crash with large carts. Carts in the size coding range
  (few thousand characters) do not seem to cause problems, but crashes
  have been observed parsing carts with tens of thousands of code
  characters. This may be related to how the pyparsing grammar is
  defined, which could result in highly recursive parsing and eventually
  stack overflows.

## Credits

Code contributors: [Veikko Sariola/pestis](https://github.com/vsariola), [wojciech-graj](https://github.com/wojciech-graj),
[koorogi](https://github.com/koorogi)

Test corpus contributors: [psenough](corpus/psenough/), [ilmenit](corpus/ilmenit/),
[gigabates](corpus/gigabates/), [gasman](corpus/gasman/), [pellicus](corpus/pellicus/),
[luchak](corpus/psenough/fabracid.lua).

## License

[MIT](https://choosealicense.com/licenses/mit/)

The test corpus carts have their own licenses, see the license files in
the subdirectories of the [corpus](corpus/) directory.
