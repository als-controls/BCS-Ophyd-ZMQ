# Examples

This page contains examples of common usage patterns for bcsophyd.

## Basic Connection Test

Test connectivity to a BCS server:

```python
import asyncio
from bcsophyd.zmq.bcs_server import BCSServer

async def test_connection(host: str, port: int):
    server = BCSServer()

    try:
        await server.connect(host, port)
        print(f"Connected to {host}:{port}")

        response = await server.test_connection()
        print(f"Server response: {response}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

asyncio.run(test_connection("192.168.195.129", 5577))
```

## Device Discovery

Discover all devices from a BCS server:

```python
import asyncio
from bcsophyd.zmq import BCSDeviceManager

async def discover_devices(host: str, port: int):
    manager = BCSDeviceManager(host=host, port=port)
    await manager.connect()

    print("Motors:")
    for device in manager.client.search_regex(name=".*[Mm]otor.*"):
        print(f"  - {device}")

    print("\nAnalog Inputs:")
    for device in manager.client.search_regex(name=".*ai.*"):
        print(f"  - {device}")

asyncio.run(discover_devices("192.168.195.129", 5577))
```

## Simple Linear Scan

Run a 1D scan with a BCS motor:

```python
import asyncio
from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.callbacks import LiveTable
from ophyd.sim import det

from bcsophyd.zmq import BCSDeviceManager

async def linear_scan(host: str, port: int):
    manager = BCSDeviceManager(host=host, port=port)
    await manager.connect()

    results = manager.client.search_regex(name="Motor3")
    motor = results[0].get()

    RE = RunEngine()
    RE.subscribe(LiveTable([det, motor]))

    # Scan from 0 to 10 in 11 steps
    RE(scan([det], motor, 0, 10, 11))

asyncio.run(linear_scan("192.168.195.129", 5577))
```

## 2D Grid Scan

Run a 2D grid scan with two BCS motors:

```python
import asyncio
from bluesky import RunEngine
from bluesky.plans import grid_scan
from bluesky.callbacks import LiveTable
from ophyd.sim import det

from bcsophyd.zmq import BCSDeviceManager

async def grid_scan_example(host: str, port: int):
    manager = BCSDeviceManager(host=host, port=port)
    await manager.connect()

    motor3 = manager.client.search_regex(name="Motor3")[0].get()
    motor4 = manager.client.search_regex(name="Motor4")[0].get()

    RE = RunEngine()
    RE.subscribe(LiveTable([det, motor3, motor4]))

    # Grid scan: motor3 from 0-5 (6 steps), motor4 from 0-2 (3 steps)
    RE(grid_scan(
        [det],
        motor3, 0, 5, 6,
        motor4, 0, 2, 3,
        snake=True
    ))

asyncio.run(grid_scan_example("192.168.195.129", 5577))
```

## Reading Analog Inputs During Scan

Use a BCS analog input as a detector:

```python
import asyncio
from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.callbacks.best_effort import BestEffortCallback
from ophyd import Device
from ophyd.sim import motor

from bcsophyd.zmq import BCSDeviceManager

async def scan_with_ai(host: str, port: int):
    manager = BCSDeviceManager(host=host, port=port)
    await manager.connect()

    # Get an analog input signal
    ai_signal = manager.client.search_regex(name="new_ai_2")[0].get()

    # Wrap it in a device for Bluesky
    detector = Device(name="bcs_detector")
    detector.ai = ai_signal
    detector.ai.kind = "hinted"

    RE = RunEngine()
    bec = BestEffortCallback()
    RE.subscribe(bec)

    RE(scan([detector.ai], motor, 0, 1, 11))

asyncio.run(scan_with_ai("192.168.195.129", 5577))
```

## Handling Scan Interruption

Gracefully stop a scan after a timeout:

```python
import asyncio
import time
from threading import Thread

from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.callbacks import LiveTable
from ophyd.sim import det

from bcsophyd.zmq import BCSDeviceManager

async def scan_with_timeout(host: str, port: int, timeout_seconds: float):
    manager = BCSDeviceManager(host=host, port=port)
    await manager.connect()

    motor = manager.client.search_regex(name="Motor3")[0].get()

    RE = RunEngine()
    RE.subscribe(LiveTable([det, motor]))

    def stop_after_timeout():
        time.sleep(timeout_seconds)
        print("Timeout reached, stopping scan...")
        RE.stop()

    Thread(target=stop_after_timeout).start()

    try:
        RE(scan([det], motor, 0, 1000, 100))
    except Exception as e:
        print(f"Scan stopped: {e}")

asyncio.run(scan_with_timeout("192.168.195.129", 5577, 3.0))
```

## Using with Simulated Hardware

Test scans without a BCS server using Ophyd's simulated devices:

```python
from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.callbacks import LiveTable
from ophyd.sim import det, motor

def test_scan_no_hardware():
    """Run a scan using only simulated devices."""
    RE = RunEngine()
    RE.subscribe(LiveTable(["motor", "det"]))

    RE(scan([det], motor, 0, 10, 11))

# No async needed for simulated devices
test_scan_no_hardware()
```
