# Quick Start

## Library Usage

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

NOTE: It is important to note here that for reliable usage the `mt` object must be initialised inside
an `if __name__ == "__main__":` block. This is because the underlying computational engine
([`dask`](https://www.dask.org)) will import the running script in multiple subinterpreters
meaning that omission of this block will result in errors.

### Advanced Usage

For users with more complex, advanced needs MTPy provides a modular, composable, and extensively
documented collection of objects for quickly performing custom data analyses on meltpool data.

In cases where a full-featured [`MeltpoolTomography`][mtpy.MeltpoolTomography] class is not needed subcomponents may be used
individually to avoid unnecessary complexity. For example, if we only need to read data produced
by an Aconity PBF machine and save/load checkpoint files we can simply use the [`AconityLoader`][mtpy.loaders.aconity.AconityLoader]
subcomponent.

```python
from mtpy.loaders.aconity import AconityLoader


if __name__ == "__main__":
    loader = AconityLoader()
    loader.read_layers("layers")
    # We may wish to save the data before we analyse it
    loader.save("before_analysis.h5")
    # We can make use of convenience methods on the loader, e.g: to calibrate the temperature
    def calibrate(x, y, z, t):
        return (2.5 * t) + 500 # simple y=mx+c curve to apply to temp

    loader.apply_calibration_curve(calibrate, column="t", units="ExampleUnit")
    # Data can be accessed directly at `loader.data`
    print(loader.data.head())
    # Then, we can perform our analyses
    # For example, we can do maths directly
    loader.data["t"] *= 2
    # We can also do more advanced dask operations
    avg_layer_temp = loader.data.groupby("z").t.mean().compute()
    print(avg_layer_temp)
    # Now, we can commit our analysis to the disk and cave the result
    loader.commit()
    loader.save("after_analysis.h5")
    # And, if we want to reload our initial data, we can do that easily too
    loader.load("before_analysis.h5")
```

Currently, we provide only sucomponents and a top-level composite object encompassing all the
available functioonality. However, custom composites can also be easily created by overloading
the `__init__` of the [`MeltpoolTomography`][mtpy.MeltpoolTomography] object.

```python
from mtpy import MeltpoolTomography
from mtpy.loaders.aconity import Aconity
from mtpy.vis.vis2d.plotter import Plotter


# Here, we define a custom composite that can only load aconity data
# and create 2d plots.
class MyComposite(MeltpoolTomography):
    def __init__( self):
        self.loader = Aconity()
        self.plotter = Plotter()

# Then, we can use our custom composite to do some analysis
if __name__ == "__main__":
    mt = MyComposite()
    mt.read_layers("layers")
    mt.scatter2d(filename="layers.html")
```

### Developer Usage

To develop new components to use with MTPy, the library contains many types compatible with
mypy type checking to aid with correct implementation. Currently, wach subcomponent type provides
an abstract class defining some helpful, shared functionality. However, type checking is
implemented via `typing.Protocol` definitions, meaning that the usage of these abstract classes is
optional. As long as the components developed match the protocol, they will be recognised as a valid
and correct implementation by mypy. For example, to implement a custom plotter that can be seamlessly
integrated with the rest of the MTPy library we simply need to create a class that conforms to the
[`PlotterProtocol`][mtpy.vis.protocol.PlotterProtocol], which requires the object to have a [`loader`][mtpy.loaders.protocol.LoaderProtocol] and two methods:
- [`plot`][mtpy.vis.protocol.PlotterProtocol.plot]: to generate plots from the data in `loader`
- [`generate_view_id`][mtpy.vis.protocol.PlotterProtocol.plot]: to generate unique view ids, to avoid unnecessary reduplication of plots
```python
# custom_plotter.py

from typing import Any, Iterable, Optional, Tuple
from datashader.reductions import Reduction
from holoviews.element.chart import Chart
from mtpy.loaders.protocol import LoaderProtocol


class MyPlotter:
    def __init__(self: "MyPlotter", loader: LoaderProtocol) -> None:
        self.loader = loader

    def plot(
        self: "MyPlotter",
        filename: Optional[str] = None,
        *args: Any,
        kind: str,
        add_to_dashboard: bool = False,
        samples: Optional[int | Iterable[int]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[str | Iterable[str]] = None,
        aggregator: Optional[Reduction] = None,
        **kwargs: Any,
    ) -> Chart:
        if kind == "my_custom_plot"
            ... # Do some complex, custom plotting and return a chart

        raise NotImplementedError # If given kind isn't implemented, raise an error

    def generate_view_id(
        self: "MyPlotter",
        kind: str,
        samples: Optional[int | Iterable[int]] = None,
        kwargs: Optional[dict[str, object]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[str | Iterable[str]] = None,
    ) -> str:
        # This is a quick-and-dirty way to generate a "good enough" fingerprint for plots
        params = (
            kind, tuples(samples), tuple(kwargs.items()), xrange, yrange, zrange, tuple(groupby)
        )
        return hash(params)
```

As long as this conforms to the correct protocols, it should be able to be used as a drop-in
component with the rest of the MTPy library, as described in previous sections.

```python
from mtpy import MeltpoolTomography
from mtpy.loaders.aconity import Aconity

from custom_plotter import MyPlotter


# Here, we define a custom composite that can only load aconity data
# and create 2d plots.
class MyComposite(MeltpoolTomography):
    def __init__( self):
        self.loader = Aconity()
        self.plotter = MyPlotter()

# Then, we can use our custom composite to do some analysis
if __name__ == "__main__":
    mt = MyComposite()
    mt.read_layers("layers")
    mt.plot(kind="my_custom_plot")
```
