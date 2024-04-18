# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress. In the process of being refactored, reorganized, and redesigned a little to turn it from a draft tool into a more polished and useful library ready to be rolled out to the broader community.

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
- [ ] use `__init__.py` to simplify API
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

## Subprojects

### Loosen class couplings

- [x] Properly plan new UML
- [x] Create abstract classes/interfaces
- [x] Decouple main classes
- [x] Implement logger according to a protocol
- [x] Implement progress bars according to a protocol
- [ ] Create dummy modules for each class

### Create proper testing regime

- [ ] Create testing modules conforming to protocols
    - Might make sense for testing modules to be wrappers around hypothesis generators?
- Implement tests using:
    - [ ] Traditional scripted testing (e.g: pytest)
    - [ ] Property based testing (hypothesis)

Note: This project is an absolute mess right now, i need to remember to make sure i branch each subsection of this work in git to manage it properly.
