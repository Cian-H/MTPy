#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A module for handling L-PBF meltpool tomography data."""

from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Union

from dask.distributed import Client
from dask.distributed.deploy import Cluster
from fsspec import AbstractFileSystem

from .loaders.aconity import AconityLoader
from .loaders.protocol import LoaderProtocol
from .proc.processor import Processor
from .vis.plotter import Plotter


class MeltpoolTomography:
    """a class for handling the data pipeline and visualisation of meltpool tomography data."""

    _loaders: ClassVar[Dict[str, LoaderProtocol]] = {
        "aconity": AconityLoader,
    }

    def __init__(
        self: "MeltpoolTomography",
        loader_type: Optional[str] = "aconity",  # Currently the only one implemented
        client: Optional[Client] = None,
        cluster: Optional[Cluster] = None,
        fs: Optional[AbstractFileSystem] = None,
        data_cache: Optional[Union[Path, str]] = "cache",
        cluster_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialises a MeltpoolTomography object.

        Args:
            self (MeltpoolTomography): The MeltpoolTomography object.
            **kwargs: keyword arguments to be passed to the parent class initialisers
        """
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

    def __getattr__(self: "MeltpoolTomography", attr: str) -> Any: # noqa: ANN401
        for obj in (self.loader, self.processor, self.plotter):
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return AttributeError(f"{self.__class__.__name__!r} object has no attribute {attr!r}")
