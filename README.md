# yuhe

[![Python Versions](https://img.shields.io/pypi/pyversions/yuhe)](https://pypi.org/project/yuhe/)
[![PyPI Version](https://img.shields.io/pypi/v/yuhe)](https://pypi.org/project/yuhe/)

Interactive 3D bounding box selector that generates point inclusion functions.

- **Git repository**: <https://github.com/luocfprime/yuhe/>


- **Documentation** <https://luocfprime.github.io/yuhe/>


## Install

Prerequisites: You must have at least one Python package manager installed (e.g. [uv](https://docs.astral.sh/uv/getting-started/installation/)).

Install it from PyPI:

```bash
uv tool install yuhe
```

Or, if you want to run it once without installing it, you can use the `uv run` command:

```bash
uv run --with yuhe yuhe xxx  # xxx being the subcommand you want to run
```


## Usage

```text
$ yuhe -h

 Usage: yuhe [OPTIONS] MESH_PATH

 Interactive 3D bounding box selector that generates point inclusion functions.

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    mesh_path      FILE  Path to mesh file (e.g. .stl file) [required]                                                                         │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --log-level           -l      TEXT  Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) [default: INFO]                               │
│ --install-completion                Install completion for the current shell.                                                                   │
│ --show-completion                   Show completion for the current shell, to copy it or customize the installation.                            │
│ --help                -h            Show this message and exit.                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT.
