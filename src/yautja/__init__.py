"""Yautja's version. Importing this module does not load the rendering runtime."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("yautja")
except PackageNotFoundError:
    __version__ = "0.0.0+uninstalled"

__all__ = ["__version__"]
