# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[unreleased]: https://github.com/vsariola/pakettic/compare/v1.0.0...HEAD
[1.0.1]: https://github.com/vsariola/pakettic/releases/tag/v1.0.1
[1.0.0]: https://github.com/vsariola/pakettic/releases/tag/v1.0.0
[0.1.0]: https://github.com/vsariola/pakettic/releases/tag/v0.1.0