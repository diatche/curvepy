# curvepy

![Tests](https://github.com/diatche/curvepy/workflows/Tests/badge.svg)

A mathematical and financial function curve utility library for Python.

# Installation

With [poetry](https://python-poetry.org):

```bash
poetry add curvepy
```

Or with pip:

```
pip3 install curvepy
```

# Usage

Have a look at the [documentation](https://diatche.github.io/curvepy/).

Basic usage:

```python
# Create a line
from curvepy import Line

line = Line(const=1, slope=2)
assert line.y(0) == 1
assert line.y(1) == 3

# Function arithmetic
line2 = Line(const=-1, slope=-2)
line_sum = line1 + line2
assert line_sum.y(0) == 0
assert line_sum.y(1) == 0
```

# Development

## Updating Documentation

The module [pdoc3](https://pdoc3.github.io/pdoc/) is used to automatically generate documentation. To update the documentation:

1. Install `pdoc3` if needed with `pip3 install pdoc3`.
2. Navigate to project root and install dependencies: `poetry install`.
3. Generate documetation files with: `pdoc3 -o docs --html curvepy`.
4. The new files will be in `docs/curvepy`. Move them to `docs/` and replace existing files.
