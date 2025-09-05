#!/usr/bin/env python3

from os import environ


def get_secret(name: str, default: str = "", raise_if_missing: bool = True) -> str:
    if name in environ:
        return environ[name]
    if f"{name}_FILE" in environ:
        with open(environ[f"{name}_FILE"], "r") as f:
            return f.readline().rstrip("\n")
    if raise_if_missing:
        raise RuntimeError(f"Environment variable {name} was not set")
    return default
