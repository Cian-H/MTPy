#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pickle


class Base():
    """
    Base class for MTPy module classes

    Attributes
    ----------
        quiet : bool
            Determines whether object should be quiet or not
    """

    def __init__(self,
                 quiet: bool = False):
        """
        Constructor for the MTPy Base class

        Parameters
        ----------
            quiet : bool
                Determines whether object should be quiet or not
        """

        self.quiet = quiet

    def _qprint(self, string: str):
        """Prints a line if self.quiet is False"""
        if not self.quiet:
            print(string)

    # NOTE: These pickling functions might be removed later. They're
    # currently here for convenience but might be a security issue
    # down the line
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
