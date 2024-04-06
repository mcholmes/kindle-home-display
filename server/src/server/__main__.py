from __future__ import annotations

from typing_extensions import Annotated
import logging
from os import path, mkdir, getcwd
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
import typer
import uvicorn

from .config import AppConfig
from .app import App

### Get logger ###
LOG_FILE_NAME = "app.log"
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s :: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
    )

cli = typer.Typer()

def configure_logging(log_level: str, log_dir: str = None):
    
    valid_log_levels = ", ".join(logging.getLevelNamesMapping().keys())
    
    if log_level.upper() in valid_log_levels:
        logger.setLevel(log_level)
    else:
        err = f"Invalid log level: {log_level}. Possible values are {valid_log_levels}"
        raise ValueError(err)

    if log_dir is not None:
        if not path.exists(log_dir):
            mkdir(log_dir)
        
        log_path = path.join(log_dir, LOG_FILE_NAME)
        logger.addHandler(logging.FileHandler(log_path))


configType = Annotated[
        Path, 
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True
        )]

# https://jacobian.org/til/common-arguments-with-typer/
@cli.callback()
def setup(
    ctx: typer.Context,
    config: configType = Path(getcwd()) / "config.toml",
    log_level: Annotated[str, typer.Option(help="Logging level")] = "INFO",
    log_to_console: bool = False
):

    if config.exists() and config.is_file():
        app_config = AppConfig.from_toml(config)
        
        if log_to_console:
            configure_logging(log_level)
        else:
            configure_logging(log_level, app_config.server.server_dir)

        _app = App(config=app_config)
    else:
        print("The config file doesn't exist")
        typer.Abort()

    ctx.obj = SimpleNamespace(app = _app)

@cli.command()
def logs(
    ctx: typer.Context,
    limit: Annotated[int, typer.Option(help="Limit the number of log lines to retrieve (newest first)")] = None,
):

    app: App = ctx.obj.app
    logs = app.get_logs(limit=limit)
    print(logs)

@cli.command()
def once(
    ctx: typer.Context
):
    app: App = ctx.obj.app
    app.run_once(save_img=True)

@cli.command()
def start(
    ctx: typer.Context
):
    app: App = ctx.obj.app
    f = FastAPI()
    f.include_router(app.router)
    uvicorn.run(f, host="0.0.0.0", port=8000)

def main():
    cli()

if __name__ == "__main__":
    main()
    
"""
CLI:
dashboard stop
dashboard send-break
"""