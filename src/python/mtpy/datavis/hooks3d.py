# -*- coding: utf-8 -*-

"""Data visualisation components of the MTPy module."""

from __future__ import annotations

from typing import Callable


def scatter(colorbar_label: str) -> Callable[..., None]:
    """Generates hooks for 3d holoviz plots.

    Args:
        colorbar_label (str): the colorbar label
    Returns:
        Callable[..., None]: a hook function for 3d holoviz plots
    """

    def hook(plot, element) -> None:  # noqa: ANN001
        plot.handles["components"]["traces"][0]["colorbar"][
            "title"
        ] = colorbar_label  # Set colorbar label
        plot.handles["layout"]["yaxis"]["scaleanchor"] = "x"  # Anchor y axis scale to x
        plot.handles["layout"]["yaxis"]["scaleratio"] = 1  # and maintain 1:1 aspect ratio
        # plot.handles["layout"]["dragmode"] = "pan"  # Set to pan on drag
        # plot.handles["fig"]["config"]["scrollZoom"] = True  # Set to zoom with mousewheel

    return hook
