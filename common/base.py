#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

from tqdm.auto import tqdm

from ..__init__ import __modpath__

# from julia import Main, Pkg


class Base:

    def __init__(self, quiet: bool = False, progressbar=tqdm, **kwargs):
        super().__init__(**kwargs)
        self.quiet = quiet
        self.progressbar = progressbar
        # embed a Julia interpreter at base for interoperability
        # print()
        # Pkg.activate(f"{__modpath__}/julia")
        # print()
        # self._jl_interpreter = Main

    def _qprint(self, string: str):
        """Prints a line if self.quiet is False"""
        if not self.quiet:
            print(string)
