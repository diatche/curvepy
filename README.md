# func

![Tests](https://github.com/diatche/func/workflows/Tests/badge.svg)

A mathematical and financial function curve utility library for Python.

# Installation

With [poetry](https://python-poetry.org):

```bash
poetry add func
```

Or with pip:

```
pip3 install func
```

# Usage

Have a look at the [documentation](https://diatche.github.io/func/).

Basic usage:

```python
from func import Func

# TODO
```

# Development

## Updating Documentation

The module [pdoc3](https://pdoc3.github.io/pdoc/) is used to automatically generate documentation. To update the documentation:

1. Install `pdoc3` if needed with `pip3 install pdoc3`.
2. Navigate to project root and install dependencies: `poetry install`.
3. Generate documetation files with: `pdoc3 -o docs --html func`.
4. The new files will be in `docs/func`. Move them to `docs/` and replace existing files.
