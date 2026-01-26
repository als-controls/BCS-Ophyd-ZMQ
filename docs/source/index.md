# bcsophyd Documentation

```{toctree}
:maxdepth: 2
:caption: Contents

getting-started
api
examples
```

## Overview

`bcsophyd` is a Python package for interacting with the Beamline Control System (BCS) using ZeroMQ. It provides Ophyd-compatible devices for use with the [Bluesky](https://blueskyproject.io/) data acquisition framework.

## Features

- **BCSServer**: Async ZeroMQ client for communication with the BCS API
- **BCSMotor**: Ophyd-compatible motor control for BCS system motors
- **BCSSignal**: Ophyd-compatible signal wrapper for BCS analog inputs
- **BCSDeviceManager**: Device configuration and Happi database integration
- **BCSAreaDetector**: 2D detector support (under development)

## Quick Links

- [Getting Started](getting-started.md): Installation and basic usage
- [API Reference](api.md): Detailed API documentation
- [Examples](examples.md): Code examples and tutorials

## Installation

```bash
pip install bcsophyd
```

Or install from source:

```bash
git clone https://git.als.lbl.gov/bcs/bluesky/bcsophyd-zmq.git
cd bcsophyd-zmq
pip install -e .
```

## Basic Usage

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

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
