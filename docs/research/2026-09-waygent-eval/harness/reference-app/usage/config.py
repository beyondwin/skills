"""Server settings from a TOML file."""
import tomllib
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    port: int
    allowed_callers: tuple


def load_config(path):
    with open(path, "rb") as f:
        data = tomllib.load(f)
    port = data.get("port", 8765)
    if not isinstance(port, int):
        raise ConfigError("port must be an integer")
    callers = data.get("allowed_callers")
    if callers is None:
        raise ConfigError(f"{path}: allowed_callers is required")
    if not isinstance(callers, list) or not all(isinstance(c, str) and c for c in callers):
        raise ConfigError(f"{path}: allowed_callers must be a list of names")
    return Config(port=port, allowed_callers=tuple(callers))
