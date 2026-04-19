import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

from loguru import logger
from typer import Context, Option, Typer

from server.app import App, create_app
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
    nohup server start > ~/uvicorn.log 2>&1

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

    config = ctx.obj.config
    f = create_app(config)

    uvicorn.run(f, host=str(config.server.host), port=config.server.port)

class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru."""
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message.
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(filepath: Path, log_level: str, log_to_console: bool = False):  # noqa: FBT002, FBT001
    """Configure Loguru and intercept standard logging."""
    import sys

    if filepath.is_dir():
        raise IsADirectoryError

    log_dir = filepath.parent
    if not log_dir.exists():
        print(f"Creating new log directory: {log_dir}")  # noqa: T201
        log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler
    if log_to_console:
        logger.add(sys.stderr, level=log_level)

    # Add file handler with rotation
    logger.add(filepath, rotation="10 MB", retention="10 days", level=log_level)

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept uvicorn logging
    for _log in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        _logger = logging.getLogger(_log)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

if __name__ == "__main__":
    cli()
