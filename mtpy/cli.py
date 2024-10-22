"""A CLI for when library is called as an application."""


def run() -> None:
    """Runs a CLI app object."""
    import typer

    from .meltpool_tomography import MeltpoolTomography

    app = typer.Typer()

    @app.command()
    def scatter2d(target_dir: str, out_path: str) -> None:
        """Creates a 2d scatter plot.

        Args:
            target_dir: Directory of the layer data to be plotted
            out_path: Filepath to write scatter plot data to
        """
        mt = MeltpoolTomography()
        mt.read_layers(target_dir)
        mt.scatter2d(filename=str)

    app()
