# MTPy

## Overview

A python based tool for Meltpool Tomography. Currently very much a work in progress. In the process of being refactored, reorganized, and redesigned a little to turn it from a draft tool into a more polished and useful library ready to be rolled out to the broader community.

## Todo

[X] reorganize project folder structure (proper /src directory, etc)\
[X] implement mypy type annotations to enforce types and prevent errors\
[X] add missing docstrings, conforming to a standard (currently using google convention)\
[X] add automated UML generation\
[ ] add tests using pytest and hypothesis\
[X] add git hooks (e.g: format every commit with black/ruff  and check with mypy before pushing)\
[ ] ~~add proper debug logging~~ <- This need is probably better addressed by [`snoop`](https://github.com/alexmojaki/snoop)\
[ ] REFACTOR AND IMPLEMENT PATTERNS USING [`attrs`](https://www.attrs.org/en/stable/)\
[ ] use `__init__.py` to simplify API\
[ ] clean up namespaces with config files?\
[ ] add automated documentation via mkdocs (and remove sphinx docs)\
[ ] implement a CLI for basic functions\
[ ] rewrite experimental GUI using flet\
[ ] implement Dask GPU support\
[ ] Add a dashboard using dash\
[ ] fix 3d tomography visualizations (see in-progress project)\
[ ] clean up project in general (e.g: remove unused files, remove old code, etc.)\

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
