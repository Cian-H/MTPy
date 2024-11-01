"""A CLI for when library is called as an application."""

import typer

from .meltpool_tomography import MeltpoolTomography

app = typer.Typer()


def init(target_dir: str) -> MeltpoolTomography:
    """Initialises and MTPy object to use for plotting.

    Args:
        target_dir (str): Directory of the layer data to be plotted

    Returns:
        MeltpoolTomography: An initialised MeltpoolTomgoraphy object.
    """
    mt = MeltpoolTomography()
    mt.read_layers(target_dir)
    return mt


@app.command()
def scatter2d(target_dir: str, out_path: str, x: str = "x", y: str = "y", w: str = "t") -> None:
    """Creates a 2d scatter plot.

    Args:
        target_dir (str): Directory of the layer data to be plotted
        out_path (str): Filepath to write scatter plot data to
        x (str, optional): The columns to place on the x axis of the plot. Defaults to "x".
        y (str, optional): The columns to place on the y axis of the plot. Defaults to "y".
        w (str, optional): The columns to place on the w axis of the plot. Defaults to "t".
    """
    mt = init(target_dir)
    mt.scatter2d(filename=out_path, x=x, y=y, w=w)


@app.command()
def distribution2d(target_dir: str, out_path: str, x: str = "x") -> None:
    """Creates a 2d distribution plot.

    Args:
        target_dir (str): Directory of the layer data to be plotted
        out_path (str): Filepath to write scatter plot data to
        x (str, optional): The columns to place on the x axis of the plot. Defaults to "x".
    """
    mt = init(target_dir)
    mt.distribution2d(filename=out_path)


@app.command()
def scatter3d(
    target_dir: str, out_path: str, x: str = "x", y: str = "y", z: str = "z", w: str = "t"
) -> None:
    """Creates a 3d scatter plot.

    Args:
        target_dir (str): Directory of the layer data to be plotted
        out_path (str): Filepath to write scatter plot data to
        x (str, optional): The columns to place on the x axis of the plot. Defaults to "x".
        y (str, optional): The columns to place on the y axis of the plot. Defaults to "y".
        z (str, optional): The columns to place on the z axis of the plot. Defaults to "z".
        w (str, optional): The columns to place on the w axis of the plot. Defaults to "t".
    """
    mt = init(target_dir)
    mt.distribution(filename=out_path)
