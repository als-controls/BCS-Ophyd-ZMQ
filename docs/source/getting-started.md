# Getting Started

## Installation

### Prerequisites

- Python 3.9 or higher
- A running BCS server (for full functionality)

### Install from source

```bash
git clone https://git.als.lbl.gov/bcs/bluesky/bcsophyd-zmq.git
cd bcsophyd-zmq
pip install -e .
```

### Optional dependencies

For development (includes Bluesky and matplotlib):
```bash
pip install -e ".[dev]"
```

For building documentation:
```bash
pip install -e ".[docs]"
```

For running tests:
```bash
pip install -e ".[tests]"
```

## Connecting to a BCS Server

The first step is to connect to a BCS server using the `BCSDeviceManager`:

```python
import asyncio
from bcsophyd.zmq import BCSDeviceManager

async def connect():
    # Create a device manager
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)

    # Connect to the server (this also discovers devices)
    success = await manager.connect()

    if success:
        print("Connected successfully!")

        # List all discovered devices
        for device in manager.client.items():
            print(device)
    else:
        print("Connection failed")

asyncio.run(connect())
```

## Working with Motors

Once connected, you can retrieve motors from the Happi database and use them:

```python
import asyncio
from bcsophyd.zmq import BCSDeviceManager

async def use_motor():
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)
    await manager.connect()

    # Search for a motor by name
    results = manager.client.search_regex(name="Motor3")

    if results:
        # Get the motor instance
        motor = results[0].get()

        # Read current position
        position = motor.get()
        print(f"Current position: {position}")

        # Move the motor (uncomment to execute)
        # await motor.set(50.0)

asyncio.run(use_motor())
```

## Working with Signals

Analog input signals can be read similarly:

```python
import asyncio
from bcsophyd.zmq import BCSDeviceManager

async def read_signal():
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)
    await manager.connect()

    # Search for a signal by name
    results = manager.client.search_regex(name="new_ai_2")

    if results:
        signal = results[0].get()

        # Read the value
        value = await signal.get()
        print(f"Signal value: {value}")

asyncio.run(read_signal())
```

## Running Bluesky Scans

The main purpose of bcsophyd is to enable Bluesky scans with BCS hardware:

```python
import asyncio
from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.callbacks import LiveTable
from ophyd.sim import det

from bcsophyd.zmq import BCSDeviceManager

async def run_scan():
    # Connect and get a motor
    manager = BCSDeviceManager(host="192.168.195.129", port=5577)
    await manager.connect()

    results = manager.client.search_regex(name="Motor3")
    motor = results[0].get()

    # Set up the RunEngine
    RE = RunEngine()
    RE.subscribe(LiveTable([det, motor]))

    # Run a scan from position 0 to 10 in 11 steps
    RE(scan([det], motor, 0, 10, 11))

asyncio.run(run_scan())
```

## Next Steps

- See the [API Reference](api.md) for detailed documentation
- Check out the [Examples](examples.md) for more usage patterns
