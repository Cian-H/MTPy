#!/usr/bin/env python3

"""A module for handling L-PBF meltpool tomography data."""

from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Type

from dask.distributed import Client
from dask.distributed.deploy import Cluster
from fsspec import AbstractFileSystem

from mtpy.loaders.aconity import AconityLoader
from mtpy.loaders.csv import CSVLoader
from mtpy.loaders.protocol import LoaderProtocol
from mtpy.proc.processor import Processor
from mtpy.vis.plotter import Plotter


class MeltpoolTomography:
    """A class for handling the data pipeline and visualisation of meltpool tomography data.

    Args:
        loader_type (str): The type of loader to use. Defaults to "aconity".
        client (Optional[Client]): The dask client for managing computations.
            Defaults to None.
        cluster (Optional[Cluster]): The dask cluster on which to perform computations.
            Defaults to None.
        fs (Optional[AbstractFileSystem]): The fsspec filesystem on which to store the cache.
            Defaults to `None`.
        data_cache (Path | str): The path to the directory in which to cache
            data. Defaults to "cache".
        cluster_config (Optional[Dict[str, Any]]): The configuration for any dask clusters to
            be initialised. Defaults to None.

    Raises:
        ValueError: If no implementation is found matching `loader` argument.
    """

    _loaders: ClassVar[Dict[str, Type[LoaderProtocol]]] = {
        "aconity": AconityLoader,
        "csv": CSVLoader,
    }

    def __init__(
        self: "MeltpoolTomography",
        loader_type: str = "aconity",  # Currently the only one implemented
        client: Optional[Client] = None,
        cluster: Optional[Cluster] = None,
        fs: Optional[AbstractFileSystem] = None,
        data_cache: Path | str = "cache",
        cluster_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if loader_type not in self._loaders:
            msg = f'No implementation for loader "{loader_type}" found.'
            raise ValueError(msg)

        self.loader: LoaderProtocol = self._loaders[loader_type](
            client,
            cluster,
            fs,
            data_cache,
            cluster_config,
        )

        self.processor = Processor(self.loader)
        self.plotter = Plotter(self.loader)

    def __getattr__(self: "MeltpoolTomography", attr: str) -> Any:  # noqa: ANN401
        """Fetches methods and attributes from components in this composite class.

        This is a fallback that fetches methods and attributes from subcomponents comprising this
        composite class. The resolution of methods and attributes follows the order:
            MeltpoolTomography > self.loader > self.processor > self.plotter
        If no matching attribute is found throws an AttributeError.

        Args:
            attr (str): The attribute/method to be fetched.

        Returns:
            Any: the object to which the attribute is resolved. Can be any type (obviously)
                as there is no way to predict what types a subcomponent might have as an attr.

        Raises:
            AttributeError: If no valid attribute is found on the MeltpoolTomography instance or
                any of its subcomponents.
        """
        for obj in (self.loader, self.processor, self.plotter):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        msg = f"{self.__class__.__name__!r} object has no attribute {attr!r}"
        raise AttributeError(msg)
