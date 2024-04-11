# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress. In the process of being refactored, reorganized, and redesigned a little to turn it from a draft tool into a more polished and useful library ready to be rolled out to the broader community.

## Progress Notes

- Reorganized into more sane file tree
- Converted `Base` class to `BaseProtocol` protocol
- Implemented `vis` protocol and ABC
- Implemented rough `loaders` protocol and ABC
- Problem w/ libstdc++ due to using nixos? preventing import of dask.dataframe

NOTE FOR RETURNING TO THIS:
Currently, have implemented type guard to try and constrain the progressbar.
However, this isn't working because it is constraining to an instance instead
of a class. Need to figure out how to constrain to a class (not an instance)
that implements a protocol.

## Todo

- [x] reorganize project folder structure (proper /src directory, etc)
- [x] implement mypy type annotations to enforce types and prevent errors
- [x] add missing docstrings, conforming to a standard (currently using google convention)
- [x] add automated UML generation
- [ ] add tests using pytest and hypothesis
- [x] add git hooks (e.g: format every commit with black/ruff  and check with mypy before pushing)
- [x] add proper debug logging
- [ ] add debug messages
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

## Project UML

```mermaid
classDiagram
  class Base {
    data
    progressbar : tqdm_asyncio
    quiet : bool
  }
  class DataLoader {
    cache_metadata
    client
    cluster : NoneType
    data
    fs : Optional[AbstractFileSystem]
    temp_label : str
    temp_units : str
    apply_calibration_curve(calibration_curve: Optional[CalibrationFunction], temp_column: str, units: Optional[str]) None
    commit() None
    construct_cached_ddf(data_path: str, chunk_size: int) None
    generate_metadata(path: Optional[str]) PathMetadataTree
    get_memory_limit() int
    load(filepath: Union[Path, str]) None
    read_layers(data_path: str, calibration_curve: Optional[CalibrationFunction], temp_units: str, chunk_size: int) None
    reload_raw() None
    save(filepath: Path | str) None
    tree_metadata(path: Optional[str], meta_dict: Optional[PathMetadataTree]) PathMetadataTree
  }
  class DataPlotter {
  }
  class DataProcessor {
  }
  class DataStatistics {
    calculate_stats(groupby: Optional[Union[str, Iterable[str]]], confidence_interval: float) Dict[str, Any]
    export_datasheet(filepath: str) None
    write_to_file(stats: Dict[str, Any], filepath: str) None
  }
  class DataThresholder {
    data
    avg_greaterthan(column: str, threshold_percent: float) None
    avg_lessthan(column: str, threshold_percent: float) None
    avg_threshold(threshold_percent: float, column: str, comparison_func: Callable[[float, float], bool]) None
    avgspeed_threshold(threshold_percent: float, avgof: int) None
    mask_xyrectangles(sample_map: Dict[Any, Tuple[Tuple[int, int], Tuple[int, int]]]) None
    rotate_xy(angle: float) None
    threshold_all_layers(thresh_functions: Union[Callable[[float, float], bool], Iterable[Callable[[float, float], bool]]], threshfunc_kwargs: Union[Dict[str, Any], Iterable[Dict[str, Any]]]) None
  }
  class MeltpoolTomography {
  }
  class Plotter2D {
    distribution2d() Chart
    plot2d(kind: str, filename: Optional[str]) Chart
    scatter2d() Chart
  }
  class Plotter3D {
    plot3d(kind: str, filename: Optional[str]) Chart
    scatter3d() Chart
  }
  class PlotterBase {
    view_tag : str
    views : Dict[str, Chart]
    generate_view_id(kind: str, samples: Optional[Union[int, Iterable[int]]], kwargs: Optional[dict], xrange: Tuple[Optional[float], Optional[float]] | Optional[float], yrange: Tuple[Optional[float], Optional[float]] | Optional[float], zrange: Tuple[Optional[float], Optional[float]] | Optional[float], groupby: Optional[Union[str, Iterable[str]]]) str
  }
  DataLoader --|> Base
  DataProcessor --|> DataStatistics
  DataProcessor --|> DataThresholder
  DataStatistics --|> DataLoader
  DataThresholder --|> DataLoader
  DataPlotter --|> Plotter2D
  DataPlotter --|> Plotter3D
  Plotter2D --|> PlotterBase
  Plotter3D --|> PlotterBase
  PlotterBase --|> Base
  MeltpoolTomography --|> DataProcessor
  MeltpoolTomography --|> DataPlotter

```
