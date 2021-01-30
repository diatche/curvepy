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

## Basic usage:

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

## JSON Format

**Function values:**

Functions are denoted by `$`, for example, `$add`. Available functions:

- `$add`: Adds values. Example: `{ "$add": [1, 2] }`, which results in `1 + 2`.
- `$line`: Adds values. Example: `{ "$line": { "points": [[1, 2], [2, 3]] } }` which results in a line joining the points `(1, 2)` and `(2, 3)`.

For other functions, refer to `Curve` documentation.

Decorators modify applicable values and functions inside of them as well as deeply nested values. Available decorators:

- `@date`: Converts all string values to seconds from Unix epoch. If no GMT offset is given, uses the local time zone at the time of parsing.
- `@log`: Converts all number literals to log space. On exit from the decorator, the result is raised bacj by the base into linear space. Available varaints: `@log2`, `@log10`.
- `@args`: Allows using both named and unamed arguments in a function. For example: `{ '$raised': { '@args': [4], 'base': 2 } }`, which will result in `pow(2, 4)`.

A full example:

The following price will be in the form of a line (on a log chart) joining the prices **10080.2** and **8975.0** on dates **8 May 2020 11:01 am** and **13 May 2020 5 am** respectively.

```json
{
    "price": {
        "@log": {
            "$line": {
                "points": [
                    [{"@date": "2020-05-08 11:01"}, 10080.2],
                    [{"@date": "2020-05-13 05:00"}, 8975.0]
                ]
            }
        }
    }
}
```

# Development

## Setup

Clone repository and run:

```bash
poetry install
```

## Running Unit Tests

```bash
poetry run test
```

## Updating Documentation

The module [pdoc3](https://pdoc3.github.io/pdoc/) is used to automatically generate documentation. To update the documentation:

1. Install `pdoc3` if needed with `pip3 install pdoc3`.
2. Navigate to project root and install dependencies: `poetry install`.
3. Generate documetation files with: `pdoc3 -o docs --html curvepy`.
4. The new files will be in `docs/curvepy`. Move them to `docs/` and replace existing files.
