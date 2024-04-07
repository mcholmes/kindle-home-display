from __future__ import annotations

from os import getcwd
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

import typer
import uvicorn
from fastapi import FastAPI

from server.app import App
from server.config import AppConfig

cli = typer.Typer(add_completion=False)

config_type = Annotated[
    Path,
    typer.Option(
        exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True
    ),
]


# https://jacobian.org/til/common-arguments-with-typer/
@cli.callback()
def setup(
    ctx: typer.Context,
    config: config_type | None = None,
    log_level: Annotated[str, typer.Option(help="Logging level")] = "INFO",
    log_to_console: bool = False
):
    """
    Command-line interface for an app which creates & serves an image to be polled by
    dashboard device using wget or similar.

    It requires a config.toml file. If not specified with --config, it will look for one
    in the directory from which this script is being run.
    """
    if config is None:
        config = Path(getcwd()) / "config.toml",

    if config.exists() and config.is_file():
        app_config = AppConfig.from_toml(config)
        _app = App(config=app_config)
        _app.configure_logging(log_level, log_to_console)

    else:
        print("The config file doesn't exist!")
        typer.Abort()

    ctx.obj = SimpleNamespace(app=_app)


@cli.command()
def logs(
    ctx: typer.Context,
    # limit: Annotated[int, typer.Option(help="Limit the number of log lines to retrieve (newest first)")] = None,
):
    app: App = ctx.obj.app
    logs = app.get_server_logs()
    print(logs)


@cli.command()
def once(ctx: typer.Context):
    app: App = ctx.obj.app
    app.run_once(save_img=True)


@cli.command()
def start(ctx: typer.Context):
    app: App = ctx.obj.app
    f = FastAPI()
    f.include_router(app.router)

    uvicorn.run(f, host="0.0.0.0", port=app.config.server.port)


if __name__ == "__main__":
    cli()
