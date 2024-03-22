# -*- coding: utf-8 -*-

"""A base class on which all other classes in this package are built."""

from dask import dataframe as dd
import pandas as pd
from tqdm.auto import tqdm


class Base:
    """A base class on which all other classes in this package are built."""

    __slots__ = ["data", "progressbar", "quiet"]

    def __init__(
        self: "Base",
        *,
        quiet: bool = False,
        progressbar: type[tqdm] = tqdm,  # todo: replace this with a progressbar interface
    ) -> None:
        """Initialisation shared by all classes in this package.

        Args:
            self (Base): The class instance.
            quiet (bool, optional): Sets the verbosity of the program. Defaults to False.
            progressbar (tqdm, optional):
                A passthrough iterative wrapper that updates a progress bar. Defaults to tqdm.
            **kwargs (Dict[str, Any]): Additional keyword arguments (unused).
        """
        self.quiet = quiet
        self.progressbar = progressbar
        # We need to create a dummy dataframe to avoid errors when calling methods
        self.data: dd.DataFrame = dd.from_pandas(pd.DataFrame(), npartitions=1)
        # embed a Julia interpreter at base for interoperability
        # print()
        # Pkg.activate(f"{__modpath__}/julia")
        # print()
        # self._jl_interpreter = Main

    def _qprint(self: "Base", string: str) -> None:
        """Prints a line if self.quiet is False.

        Args:
            string (str): The string to be printed.
        """
        if not self.quiet:
            print(string)
