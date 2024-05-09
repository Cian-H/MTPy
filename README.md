# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress. In the process of being refactored, reorganized, and redesigned a little to turn it from a draft tool into a more polished and useful library ready to be rolled out to the broader community.

## Daily Notes

- Pulled read_layers out of module to more simplify project
    - Need to remove remnants from this project and reorganise it
    - Should probably remove julia remnants while im at it
- Test still failing
    - Giving error:
    ```
    FAILED tests/loaders/aconity_test.py::test_read_layers
    ValueError: Unable to coerce to DataFrame,
    shape must be (0, 4): given (128, 4)
    ```
- Error is surprisingly informative but not sure where its occuring
- Is `ValueError` so likely originates from python
- Huge logs returned by dask as it spins up many clients:
    - Might make sense to suppress dask logs
    - But error might be in `dask`?
    - Maybe just suppress `dask.distributed`
- Either way: need to clean up logs and go through in detail

## Todo

- [x] reorganize project folder structure (proper /src directory, etc)
- [x] implement mypy type annotations to enforce types and prevent errors
- [x] add missing docstrings, conforming to a standard (currently using google convention)
- [x] add automated UML generation
- [ ] add tests using pytest and hypothesis
- [x] add git hooks (e.g: format every commit with black/ruff  and check with mypy before pushing)
- [x] add proper debug logging
- [x] add debug messages
- [x] add proper user feedback mechanism
- [x] Refactor and implement patterns where appropriate
- [x] use `__init__.py` to simplify API
- [ ] ~~clean up namespaces with config files?~~ <- Unnecessary. Restructure made the API more sensible.
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
- [ ] Profile import time (takes long time to import library)
- [x] Split library into groups, e.g: core, vis, statistics, etc so they dont all need to be installed every time.

## Subprojects

### Loosen class couplings

- [x] Properly plan new UML
- [x] Create abstract classes/interfaces
- [x] Decouple main classes
- [x] Implement logger according to a protocol
- [x] Implement progress bars according to a protocol
- [x] Create dummy modules for each class

### Create proper testing regime

- [x] Create testing modules conforming to protocols
    - Might make sense for testing modules to be wrappers around hypothesis generators?
- Implement tests using:
    - [x] Traditional scripted testing (e.g: pytest)
    - [x] Property based testing (hypothesis)
- Testing Strategy:
    - [x] Loaders
        - [x] `read_layers`
        - [x] `apply_calibration_curve`
        - [x] `commit`

Note: This project is an absolute mess right now, i need to remember to make sure i branch each subsection of this work in git to manage it properly.
