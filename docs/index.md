# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress.
It is still in the process of being refactored, reorganized, and redesigned a little
to turn it from a rough internal tool into a more polished and useful library ready
to be rolled out to the broader community.

## Quick Start

### Basic Usage

To use the most basic functions of MTPy the user can simply import the [`MeltpoolTomography`][mtpy.MeltpoolTomography]
class and initialise it. Once initialised, this object can read the layer data from a given
directory and create an interactive html scatterplot using the `read_layers` and `scatter2d`
methods respectively.

```python
from mtpy import MeltpoolTomography


if __name__ == "__main__":
    mt = MeltpoolTomography()
    mt.read_layers("layers")
    mt.scatter2d(filename="layers.html")
```

It is important to note here that for reliable usage the `mt` object must be initialised inside
an `if __name__ == "__main__":` block. This is because the underlying computational engine
([`dask`](https://www.dask.org)) will import the running script in multiple subinterpreters
meaning that omission of this block will result in errors.
