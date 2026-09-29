"""Server settings from a TOML file."""
import tomllib
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    port: int


def load_config(path):
    with open(path, "rb") as f:
        data = tomllib.load(f)
    port = data.get("port", 8765)
    if not isinstance(port, int):
        raise ConfigError("port must be an integer")
    return Config(port=port)
