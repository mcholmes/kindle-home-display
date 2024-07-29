import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

from typer import Context, Option, Typer

from server.app import App, AppServer
from server.config import AppConfig

cli = Typer(add_completion=False)
current_dir = Path.cwd()

# https://jacobian.org/til/common-arguments-with-typer/
@cli.callback()
def setup(
    ctx: Context,
    config_dir: Annotated[
        Path,
        Option(
            help="""Location of 'config' & 'api_keys' files.
                Either file can be TOML, YAML or JSON.
                Default location is current dir."""
        ),
    ] = current_dir,
    log_level: Annotated[str, Option(help="Logging level")] = "INFO",
    log_to_console: Annotated[bool, Option(help="Print logging to console (as well as file)")] = False,  # noqa: FBT002
):
    """
    Command-line interface for an app which creates & serves an image to be polled by
    dashboard device using wget or similar.

    After pip installing the .whl, run this from the command line:
    nohup server start > ~/uvicorn.log &1>2

    """

    config = AppConfig.from_dir(config_dir)

    log_filepath = Path(config.server.server_dir) / config.server.server_log_file_name
    configure_logging(log_filepath, log_level, log_to_console)

    ctx.obj = SimpleNamespace(config=config)


@cli.command()
def logs(ctx: Context):
    """ Print server logs """
    app: App = App(ctx.obj.config)
    logs = app.get_server_logs()
    print(logs)  # noqa: T201

@cli.command()
def once(ctx: Context):
    """ Run the app once, generating an image and saving it """
    app: App = App(ctx.obj.config)
    app.generate_image_and_save()


@cli.command()
def start(ctx: Context):
    """ Start the server """
    import uvicorn
    from fastapi import FastAPI

    app: AppServer = AppServer(ctx.obj.config)
    f = FastAPI()
    f.include_router(app.router)

    uvicorn.run(f, host=str(app.config.server.host), port=app.config.server.port)

def configure_logging(filepath: Path, log_level: str, log_to_console: bool = False):  # noqa: FBT002, FBT001
        """Reconfigure the ROOT logger, not the module's logger"""
        if filepath.is_dir():
             raise IsADirectoryError

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        h_format = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s :: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(h_format)
            root_logger.addHandler(console_handler)

        log_dir = filepath.parent
        if not Path.exists(log_dir):
            print(f"Creating new log directory: {log_dir}")  # noqa: T201
            Path.mkdir(log_dir)

        file_handler = logging.FileHandler(filepath)
        file_handler.setFormatter(h_format)
        root_logger.addHandler(file_handler)

if __name__ == "__main__":
    cli()
