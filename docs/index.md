# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress.
It is still in the process of being refactored, reorganized, and redesigned a little
to turn it from a rough internal tool into a more polished and useful library ready
to be rolled out to the broader community.

## CLI Usage

Creating an interactive 2d scatter plot using the MTPy CLI is as simple as running the
following command in the command line:
<!-- termynal -->
```
$ mtpy scatter2d ./layers ./scatter_plot.html
---> 100%
Plot saved to "./scatter_plot.html"!
```

Running this command will produce the following figure saved as "scatter_plot.html":

<div align="center">
    <iframe src="./assets/example_plot.html" height="400px" width="400px" frameborder="0" scrolling="no" margin="auto" text-align="center"></iframe>
</div>


## Library Usage

MTPy primarily exists as a framework for the building of tools for the analysis of PBF
pytometry data. A comprehensive introduction to its isage is available in the [Quickstart](./quickstart.md)
section. More detailed documentation is available in the Reference section.
