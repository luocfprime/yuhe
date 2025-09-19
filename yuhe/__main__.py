import logging
from pathlib import Path
from typing import Annotated

import typer

from yuhe.__about__ import __application__
from yuhe.app import PolyscopeApp

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


def configure_logging(log_level: str):
    # Map text log level to numeric
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise typer.BadParameter(f"Invalid log level: {log_level}")

    # By default, root logger follows the chosen level
    root_level = numeric_level

    # Special case: if DEBUG is chosen, don't expose 3rd-party debug
    if numeric_level == logging.DEBUG:
        root_level = logging.INFO

    # Configure root logger
    logging.basicConfig(level=root_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Configure application logger separately
    app_logger = logging.getLogger(__application__)
    if numeric_level == logging.DEBUG:
        app_logger.setLevel(logging.DEBUG)
    else:
        app_logger.setLevel(numeric_level)


@app.command()
def _(
    mesh_path: Annotated[
        Path,
        typer.Argument(
            help="Path to mesh file (e.g. .stl file)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        case_sensitive=False,
    ),
):
    """Interactive 3D bounding box selector that generates point inclusion functions."""
    configure_logging(log_level)
    app_instance = PolyscopeApp(mesh_path)
    app_instance.run()


def main():
    app()


if __name__ == "__main__":
    main()
