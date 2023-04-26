#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations


from tqdm.auto import tqdm


# from julia import Main, Pkg


class Base:
    """A base class on which all other classes in this package are built."""

    def __init__(self, quiet: bool = False, progressbar=tqdm, **kwargs):
        """Initialisation shared by all classes in this package.

        Args:
            quiet (bool, optional): Sets the verbosity of the program. Defaults to False.
            progressbar (Any, optional): A passthrough iterative wrapper that updates a progress
                bar. Defaults to tqdm.
        """
        super().__init__(**kwargs)
        self.quiet = quiet
        self.progressbar = progressbar
        # embed a Julia interpreter at base for interoperability
        # print()
        # Pkg.activate(f"{__modpath__}/julia")
        # print()
        # self._jl_interpreter = Main

    def _qprint(self, string: str):
        """Prints a line if self.quiet is False

        Args:
            string (str): The string to be printed.
        """
        if not self.quiet:
            print(string)
