#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
