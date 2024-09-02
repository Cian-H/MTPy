# MTPy

## Overview

A modular, extensible, and modifiable python based tool for Meltpool Tomography. The aim of this tool is to create a core library of PBF tools that can be applied in the many areas of our research on the topic.

## Current Features

- Streaming of larger-than-RAM datasets from HDD for:
    - analysis
    - plotting
    - Data mining
-  No need for binning or other data reduction methods
-  Distributed computing, allowing for analysis to take place on compute clusters and larger distributed systems
-  Extensive type hinting and structurally subtyped composition. This design ensures that:
    - New modules can easily be added
    - Documentation can be automatically generated
    - Users will get LSP tooltips to help them develop quickly
    - Static analysis can be used to catch errors quickly
    - Modules can easily and seamlessly be implemented in more performant, statically typed languages (e.g: the [`read_aconity_layers`](https://github.com/Cian-H/read_aconity_layers) submodule here, written in rust)
- Detailed, togglable user feedback and debug logs, allowing for quick diagnosis of problems when they occur
- Test coverage for core, IO interfaces (as they are most likely parts to error) with plans to expand coverage in the future

## Planned Features

- A CLI to avoid the need for scripting when doing common analyses
- A new GUI to allow non-programming researchers to use the tool (previous GUI [`Melter`](https://github.com/Cian-H/Melter) was a good demonstrator but isn't really fit for our current purposes)
- Reimplementation of the previouslt removed interactive 3d plot feature
- GPU support to further accelerate analysis of extremely large datasets
- Better sample detection via mathematically driven raster detection

## ToDo

- [ ] implement a CLI for basic functions
- [ ] rewrite experimental GUI using flet
- [ ] implement Dask GPU support
- [ ] Add raster detection component as processor
- [ ] fix interactive 3d tomography visualizations (in-progress project)
- [ ] Carve out save/load functionality into a separate module
