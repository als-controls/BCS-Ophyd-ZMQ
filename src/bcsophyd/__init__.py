"""
bcsophyd - A package for interacting with the Beamline Control System (BCS) using ZeroMQ.

This package provides Ophyd-compatible devices for use with the Bluesky
data acquisition framework.
"""

from . import zmq

__all__ = ["zmq"]

try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("bcsophyd")
    except PackageNotFoundError:
        __version__ = "0.1.0"
except ImportError:
    __version__ = "0.1.0"
