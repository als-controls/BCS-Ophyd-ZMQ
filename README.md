# bcsophyd-zmq

A Python package for interacting with the Beamline Control System (BCS) using ZeroMQ, providing Ophyd-compatible devices for use with the Bluesky data acquisition framework.

## Overview

`bcsophyd` bridges LabVIEW-based BCS control systems with Python's [Bluesky](https://blueskyproject.io/) data acquisition framework. It provides:

- **BCSServer**: Async ZeroMQ client for communication with the BCS API
- **BCSMotor**: Ophyd-compatible motor control for BCS system motors
- **BCSSignal**: Ophyd-compatible signal wrapper for BCS analog inputs
- **BCSDeviceManager**: Device configuration and [Happi](https://github.com/pcdshub/happi) database integration
- **BCSAreaDetector**: 2D detector support (under development)

## Installation

### From source

```bash
git clone https://git.als.lbl.gov/bcs/bluesky/bcsophyd-zmq.git
cd bcsophyd-zmq
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

### With documentation dependencies

```bash
pip install -e ".[docs]"
```

### With test dependencies

```bash
pip install -e ".[tests]"
```

## Quick Start

### Connect to BCS and discover devices

```python
import asyncio
from bcsophyd.zmq import BCSDeviceManager

async def main():
    # Connect to BCS server
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)
    await manager.connect()

    # List all discovered devices
    for device in manager.client.items():
        print(device)

asyncio.run(main())
```

### Use a BCS motor in a Bluesky scan

```python
import asyncio
from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.callbacks import LiveTable
from ophyd.sim import det
from bcsophyd.zmq import BCSDeviceManager

async def run_scan():
    # Connect and discover devices
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)
    await manager.connect()

    # Get a motor from the Happi database
    results = manager.client.search_regex(name="Motor3")
    motor = results[0].get()

    # Run a Bluesky scan
    RE = RunEngine()
    RE.subscribe(LiveTable([det, motor]))
    RE(scan([det], motor, 0, 10, 11))

asyncio.run(run_scan())
```

### Read an analog input signal

```python
import asyncio
from bcsophyd.zmq import BCSDeviceManager

async def read_signal():
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)
    await manager.connect()

    # Get an analog input signal
    results = manager.client.search_regex(name="new_ai_2")
    signal = results[0].get()

    # Read the value
    value = await signal.get()
    print(f"Signal value: {value}")

asyncio.run(read_signal())
```

## Requirements

- Python >= 3.9
- ophyd
- pyzmq
- happi

## Documentation

Build the documentation locally:

```bash
cd docs
make html
```

Then open `docs/build/html/index.html` in your browser.

## Examples

See the `examples/` directory for more detailed usage examples:

- `basic_connection.py` - Testing BCS server connectivity
- `device_discovery.py` - Using BCSDeviceManager with Happi
- `bluesky_scans.py` - Running Bluesky scans with BCS devices

## License

MIT License

## Authors

- Joao Gabriel Felipe Machado Gazolla (gabrielgazolla@lbl.gov)
