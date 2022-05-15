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

## Credits

[Veikko Sariola](https://github.com/vsariola) aka pestis/brainlez
Coders!

## License

[MIT](LICENSE)