import json
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Optional

import typer

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
    config: Optional[config_type] = None,
    log_level: Annotated[str, typer.Option(help="Logging level")] = "INFO",
    log_to_console: Annotated[bool, typer.Option(help="Print logging to console (as well as file)")] = False,  # noqa: FBT002
):
    """
    Command-line interface for an app which creates & serves an image to be polled by
    dashboard device using wget or similar.

    It requires a config.toml file. If not specified with --config, it will look for one
    in the directory from which this script is being run.
    """
    if config is None:
        current_dir = Path.cwd()
        config = current_dir / "config.toml"
        api_keys = current_dir / "api_keys.json"

    if not config.exists():
        err = "No config.toml found."
        raise FileNotFoundError(err)

    if not api_keys.exists():
        err = "No api_keys.json found."
        raise FileNotFoundError(err)

    app_config = AppConfig.from_toml(config)

    with Path.open(api_keys) as f:
        api_keys = json.load(f)

    _app = App(app_config, api_keys)
    _app.configure_logging(log_level, log_to_console)

    ctx.obj = SimpleNamespace(app=_app)

@cli.command()
def logs(
    ctx: typer.Context
):
    app: App = ctx.obj.app
    logs = app.get_server_logs()
    print(logs)  # noqa: T201

@cli.command()
def once(ctx: typer.Context):
    app: App = ctx.obj.app
    app.generate_image_and_save()

@cli.command()
def start(ctx: typer.Context):
    import uvicorn
    from fastapi import FastAPI
    app: App = ctx.obj.app

    f = FastAPI()
    f.include_router(app.router)

    uvicorn.run(f, host=app.config.server.host, port=app.config.server.port)

if __name__ == "__main__":
    cli()
