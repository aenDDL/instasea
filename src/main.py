import importlib
import pkgutil
import typer

from src.core.registry import get_registry
from src.core.logger import setup_logging
from src.core.config import load_config


def callback():
    config_dict["config"] = load_config()

instasea = typer.Typer(callback=callback)

config_dict: dict | None = {}


def load_commands() -> None:
    import src.commands

    for _, module_name, _ in pkgutil.iter_modules(src.commands.__path__):
        importlib.import_module(f"src.commands.{module_name}")


def register_with_typer() -> None:
    group_apps: dict[str, typer.Typer] = {}

    for group, func in get_registry():
        if group not in group_apps:
            group_apps[group] = typer.Typer()
            instasea.add_typer(group_apps[group], name=group)
        group_apps[group].command(group)(func)


def main() -> None:
    setup_logging()
    load_commands()
    register_with_typer()
    instasea()