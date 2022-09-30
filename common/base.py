#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..__init__ import __modpath__
from pathlib import Path
from tqdm.auto import tqdm
import pickle
# from julia import Main, Pkg


class Base():
    """
    Base class for MTPy module classes

    Attributes
    ----------
        quiet: bool = False
            Determines whether object should be quiet or not

    Methods
    -------
        _qprint(string: str)
            Prints a line if self.quiet is False
        dump(dumppath)
            Pickles object to location in dumppath
        undump(dumppath)
            Unpickles object at dumppath and copies its attributes to self
    """

    def __init__(self,
                 quiet: bool = False,
                 progressbar=tqdm):
        """
        Constructor for the MTPy Base class

        Parameters
        ----------
            quiet: bool = False
                Determines whether object should be quiet or not
            progressbar = tqdm
                Sets the function used to generate progress bars (must use
                tqdm-like syntax)
        """

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

    # NOTE: These pickling functions might be removed later. They're
    # currently here for convenience but might be an  down the line
    def dump(self, dumppath):
        """Pickles object to location in dumppath"""
        self._qprint("Dumping object...")
        if Path(dumppath).is_dir():
            # Then dumps object to a file with that name
            pickle.dump(self, open(f"{dumppath}/mtpyobj.p",
                                   "wb"))
        else:
            pickle.dump(self, open(dumppath, "wb"))
        self._qprint("Dumped!")

    def undump(self, dumppath):
        """Unpickles object at dumppath and copies its attributes to self"""
        self._qprint("Undumping object...")
        self.__dict__ = pickle.load(open(dumppath, "rb")).__dict__.copy()
        self._qprint("Undumped!")
