
from typing import Callable

_registry: list[tuple[str, Callable[..., None]]] = []

def register_command(name: str):
    def decorator(func: Callable[..., None]):
        _registry.append((name, func))
        return func
    return decorator

def get_registry() -> list[tuple[str, Callable[..., None]]]:
    return _registry.copy()