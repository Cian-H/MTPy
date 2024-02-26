from __future__ import annotations


def scatter(colorbar_label: str) -> None:
    """generates hooks for 3d holoviz plots

    Args:
        colorbar_label (str): the colorbar label
    """

    def hook(plot, element):
        plot.handles["components"]["traces"][0]["colorbar"][
            "title"
        ] = colorbar_label  # Set colorbar label
        plot.handles["layout"]["yaxis"]["scaleanchor"] = "x"  # Anchor y axis scale to x
        plot.handles["layout"]["yaxis"]["scaleratio"] = 1  # and maintain 1:1 aspect ratio
        # plot.handles["layout"]["dragmode"] = "pan"  # Set to pan on drag
        # plot.handles["fig"]["config"]["scrollZoom"] = True  # Set to zoom with mousewheel

    return hook
