"""
bcsophyd.zmq - ZeroMQ-based interface to the Beamline Control System.

This module provides the main classes for BCS-Bluesky integration:

- BCSServer: Async ZeroMQ client for BCS API communication
- BCSDeviceManager: Device configuration and Happi database integration
- BCSMotor: Ophyd-compatible motor control
- BCSSignal: Ophyd-compatible signal wrapper for analog inputs
- BCSAreaDetector: 2D detector support (under development)
"""

from .bcs_server import BCSServer
from .bcs_motor import BCSMotor
from .bcs_signal import BCSSignal
from .bcs_device_manager import BCSDeviceManager
from .bcs_area_detector import BCSAreaDetector

__all__ = [
    "BCSServer",
    "BCSMotor",
    "BCSSignal",
    "BCSDeviceManager",
    "BCSAreaDetector",
]
