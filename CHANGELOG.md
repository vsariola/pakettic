# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Option --data-to-code that puts the data in hexadecimal strings in the
  code and adds a small stub to load the data in the string at right
  address
- Option to disable using the load trick altogether. load'' is not
  entirely semantically identical to function()end, as the load'' cannot
  access local variables in the outer scope. However, this is such a
  rare occurrence that only disable it when absolutely necessary.
- Parse errors report the offending line more accurately

### Fixed

- Printing function calls with a single table or string parameter
- Local variables without immediate assignment crashed the parser
- The initial minification used reserved keywords (in particular: or)
- Handling carts with multiple CODE chunks
- Variable names that started with `or` or `and` could give an parse
  error; for example, in `x=1 orange=2` the first statement was parsed
  as `x=1 or ange`, followed by `=1` which gave the parse error.
- Escaping `\r` and `\f` in quoted string literals
- `-- {` was not considered comment, even though it was not considered
  permutation block either

## [1.2.0] - 2023-04-02

### Added

- Perform initial variable minification before starting optimization
- Constant folding: constant integer expressions are evaluated by
  pakettic, in case they compresses better
- More detailed reporting of the crunching results

### Fixed

- Spaces between tokens were not always printed even when needed
- Hex numbers with fractional digits had the fractional digits printed in reverse
- Hex numbers with an exponent raised an error when printed

### Changed

- The default compression level is now -z0; our benchmarking does not
  show significant advantage over -z2 (only 0.2% over the test corpus),
  yet it's almost 3 times slower. Use -z2 and higher only when you are
  desperate and absolutely need that last byte.

## [1.1.1] - 2023-02-03

### Fixed

- The operator precedence of ^ vs. unary operators was STILL wrong: it
  binds more strongly than unary to the operand on its left, but less
  strongly than unary to the operand on its right
- Long comments should be delimited by --[[ and ]], not --[[ and --]]

## [1.1.0] - 2023-02-01

### Added

- Treat --![ and --!] as multiline comments, so one can have debug code
  in unpacked intro, which is not included in the packed version

### Fixed

- The operator precedence of ^ vs. unary operators was wrong
- Numerals ending in . (e.g. "1.") gave parse error, but should be allowed

## [1.0.1] - 2023-01-02

### Fixed

- Parsing 'nil' gave an error.

## [1.0.0] - 2022-12-10

### Fixed

- Don't crash when optimizing carts without anything to mutate.
- Don't crash when packing code with method calls e.g. "obj:f()" (there was a bug both in the code formatter and the optimizer).
- Don't replace symbol "self", because it has a special meaning, so just to be safe.
- Parse method definitions correctly: function a:m()end is syntactic sugar for a.m=function(self)end
- Don't crash when formatting "do ... end" blocks
- Local functions now parse and print correctly.

## [0.1.0] - 2022-12-08

### Added

- Reading TIC-80 carts (.lua & .tic)
- LUA parser based on pyparsing
- Local optimization algorithms (simulated annealing, late acceptance hill
  climbing & diversified late acceptance search) that mutate the source code, to
  see if it compresses better
- Mutations include: variable shortening, flipping operators, reordering
  arithmetic, single vs. double quotes in strings, hexadecimals vs. decimals
- Magic comments to allow reordering statements and trying alternative
  expressions

[unreleased]: https://github.com/vsariola/pakettic/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/vsariola/pakettic/releases/tag/v1.2.0
[1.1.1]: https://github.com/vsariola/pakettic/releases/tag/v1.1.1
[1.1.0]: https://github.com/vsariola/pakettic/releases/tag/v1.1.0
[1.0.1]: https://github.com/vsariola/pakettic/releases/tag/v1.0.1
[1.0.0]: https://github.com/vsariola/pakettic/releases/tag/v1.0.0
[0.1.0]: https://github.com/vsariola/pakettic/releases/tag/v0.1.0