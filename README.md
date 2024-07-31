# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress. In the process of being refactored, reorganized, and redesigned a little to turn it from a draft tool into a more polished and useful library ready to be rolled out to the broader community.

## ToDo

- [x] reorganize project folder structure (proper /src directory, etc)
- [x] implement mypy type annotations to enforce types and prevent errors
- [x] add missing docstrings, conforming to a standard (currently using google convention)
- [x] add automated UML generation
- [x] add tests using pytest and hypothesis
- [x] add git hooks (e.g: format every commit with black/ruff  and check with mypy before pushing)
- [x] add proper debug logging
- [x] add debug messages
- [x] add proper user feedback mechanism
- [x] Refactor and implement patterns where appropriate
- [x] use `__init__.py` to simplify API
- [x] add automated documentation via mkdocs (and remove sphinx docs)
- [ ] implement a CLI for basic functions
- [ ] rewrite experimental GUI using flet
- [ ] implement Dask GPU support
- [ ] Add a dashboard using dash
- [ ] Add raster detection component as processor
- [ ] fix 3d tomography visualizations (see in-progress project)
- [x] clean up project in general
    - [x] remove unused files
    - [x] remove old code
    - [x] Replace old constructs (e.g: `typing.Union`) with more modern versions
    - [x] Update dependencies
- [x] Profile import time (takes long time to import library)
    - NOTE: Looked into this, it will take some work to solve. Leaving it for now.
- [x] Split library into groups, e.g: core, vis, statistics, etc so they dont all need to be installed every time.
- [ ] Carve out save/load functionality into a separate module
