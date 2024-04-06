from __future__ import annotations

from typing_extensions import Annotated
from os import getcwd
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
import typer
import uvicorn

from .config import AppConfig
from .app import App

cli = typer.Typer()

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
        _app = App(config=app_config)
        _app.configure_logging(log_level, log_to_console)

    else:
        print("The config file doesn't exist")
        typer.Abort()

    ctx.obj = SimpleNamespace(app = _app)

@cli.command()
def logs(
    ctx: typer.Context,
    # limit: Annotated[int, typer.Option(help="Limit the number of log lines to retrieve (newest first)")] = None,
):

    app: App = ctx.obj.app
    logs = app.get_logs()
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
dashboard send-break
"""