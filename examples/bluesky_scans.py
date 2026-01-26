"""
Bluesky Scans with BCS Devices

This example demonstrates how to run Bluesky data acquisition scans
using BCS motors and detectors.
"""

import asyncio
import random
import time
from threading import Thread

from bluesky import RunEngine
from bluesky.callbacks.best_effort import BestEffortCallback
from bluesky.callbacks import LiveTable
from bluesky.plans import grid_scan, scan
from bluesky.preprocessors import monitor_during_wrapper

from ophyd import Component, Device, Signal
from ophyd.sim import det, motor

from bcsophyd.zmq.bcs_device_manager import BCSDeviceManager
from bcsophyd.zmq.bcs_area_detector import BCSAreaDetector


# =============================================================================
# Pure Bluesky Examples (no BCS connection required)
# =============================================================================


def scan_with_simulated_devices():
    """
    Run a simple scan using Ophyd's simulated motor and detector.

    This example requires no hardware connection.
    """
    RE = RunEngine({})
    live_table = LiveTable(["motor", "det"])
    RE.subscribe(live_table)

    print("Running scan with simulated motor and detector...")
    RE(scan([det], motor, 0, 10, 11))


def scan_with_random_signal():
    """
    Run a scan with a custom random signal device.

    Demonstrates creating custom Ophyd devices.
    """

    class RandomSignal(Signal):
        """Signal that returns random integers."""

        def get(self):
            return random.randint(0, 99)

    class FakeDetector(Device):
        """Detector with a random signal."""

        random_int = Component(RandomSignal, kind="hinted")

    RE = RunEngine()
    bec = BestEffortCallback()
    RE.subscribe(bec)

    fake_detector = FakeDetector(name="fake_detector")

    print("Running scan with random signal detector...")
    RE(scan([fake_detector], motor, 1, 5, 20))


# =============================================================================
# BCS + Bluesky Hybrid Examples
# =============================================================================


async def scan_with_bcs_signal(host: str, port: int):
    """
    Run a scan using a simulated motor and a real BCS analog input.

    Parameters
    ----------
    host : str
        BCS server host address
    port : int
        BCS server port
    """
    manager = BCSDeviceManager(host, port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    # Get an analog input signal
    results = manager.client.search_regex(name="new_ai_2")
    if not results:
        print("No signal found matching 'new_ai_2'")
        return

    ai_signal = results[0].get()

    # Create a wrapper device for the signal
    fake_device = Device(name="bcs_detector")
    fake_device.ai2 = ai_signal
    fake_device.ai2.kind = "hinted"

    RE = RunEngine()
    bec = BestEffortCallback()
    RE.subscribe(bec)

    print("Running scan with BCS analog input...")
    RE(scan([fake_device.ai2], motor, 0, 1, 11))


async def scan_with_bcs_motor(host: str, port: int):
    """
    Run a scan using a real BCS motor and simulated detector.

    Parameters
    ----------
    host : str
        BCS server host address
    port : int
        BCS server port
    """
    manager = BCSDeviceManager(host, port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    # Get a motor
    results = manager.client.search_regex(name="Motor3")
    if not results:
        print("No motor found matching 'Motor3'")
        return

    bcs_motor = results[0].get()
    print(f"Using motor: {bcs_motor}")

    RE = RunEngine()
    live_table = LiveTable([det, bcs_motor])
    RE.subscribe(live_table)

    print("Running scan with BCS motor...")
    RE(scan([det], bcs_motor, 40, 50, 11))


async def grid_scan_with_two_bcs_motors(host: str, port: int):
    """
    Run a 2D grid scan using two BCS motors.

    Parameters
    ----------
    host : str
        BCS server host address
    port : int
        BCS server port
    """
    manager = BCSDeviceManager(host, port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    # Get two motors
    motor3_results = manager.client.search_regex(name="Motor3")
    motor4_results = manager.client.search_regex(name="Motor4")

    if not motor3_results or not motor4_results:
        print("Could not find both Motor3 and Motor4")
        return

    motor3 = motor3_results[0].get()
    motor4 = motor4_results[0].get()

    RE = RunEngine()
    live_table = LiveTable([det, motor3, motor4])
    RE.subscribe(live_table)

    # Grid scan parameters
    motor3_start, motor3_stop, motor3_steps = 0, 5, 6
    motor4_start, motor4_stop, motor4_steps = 0, 2, 3
    snake = True

    print("Running 2D grid scan with two BCS motors...")
    RE(
        grid_scan(
            [det],
            motor3,
            motor3_start,
            motor3_stop,
            motor3_steps,
            motor4,
            motor4_start,
            motor4_stop,
            motor4_steps,
            snake,
        )
    )


async def scan_with_interruption(host: str, port: int):
    """
    Run a scan that gets interrupted after a delay.

    Demonstrates how to handle scan interruption.

    Parameters
    ----------
    host : str
        BCS server host address
    port : int
        BCS server port
    """
    manager = BCSDeviceManager(host, port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    results = manager.client.search_regex(name="Motor3")
    if not results:
        print("No motor found matching 'Motor3'")
        return

    bcs_motor = results[0].get()

    RE = RunEngine()
    live_table = LiveTable([det, bcs_motor])
    RE.subscribe(live_table)

    def interrupt_after_delay():
        """Interrupt the scan after 3 seconds."""
        time.sleep(3)
        print("Interrupting the scan...")
        RE.stop()

    interrupt_thread = Thread(target=interrupt_after_delay)
    interrupt_thread.start()

    try:
        print("Starting scan (will be interrupted)...")
        RE(scan([det], bcs_motor, 40, 1000, 11))
    except Exception as e:
        print(f"Scan interrupted: {e}")

    interrupt_thread.join()
    print("Scan complete.")


# =============================================================================
# Area Detector Examples (under development)
# =============================================================================


def scan_with_area_detector():
    """
    Run a scan with the BCS area detector.

    Note: Area detector functionality is under development.
    """
    bcs_detector = BCSAreaDetector(name="bcs_area_detector")

    RE = RunEngine({})
    live_table = LiveTable([motor, bcs_detector])
    RE.subscribe(live_table)

    print("Running scan with BCS area detector...")
    RE(scan([bcs_detector], motor, -1, 1, 11))


def fly_scan_with_area_detector():
    """
    Run a fly scan with monitored area detector.

    Note: Area detector functionality is under development.
    """
    bcs_detector = BCSAreaDetector(name="bcs_area_detector")

    RE = RunEngine({})
    live_table = LiveTable([motor, f"{bcs_detector.name}_total_intensity"])
    RE.subscribe(live_table)

    print("Running fly scan with BCS area detector...")
    RE(
        monitor_during_wrapper(
            scan([bcs_detector], motor, -1, 1, 11), [bcs_detector.total_intensity]
        )
    )


# =============================================================================
# Main Entry Point
# =============================================================================


if __name__ == "__main__":
    # Default BCS server address - modify as needed
    HOST = "192.168.195.129"
    PORT = 5577

    async def run_all_examples():
        # Pure Bluesky examples (no connection required)
        print("\n" + "=" * 60)
        print("PURE BLUESKY EXAMPLES")
        print("=" * 60 + "\n")

        scan_with_simulated_devices()
        print()
        scan_with_random_signal()

        # BCS + Bluesky hybrid examples
        print("\n" + "=" * 60)
        print("BCS + BLUESKY HYBRID EXAMPLES")
        print("=" * 60 + "\n")

        # Uncomment the examples you want to run:
        # await scan_with_bcs_signal(HOST, PORT)
        # await scan_with_bcs_motor(HOST, PORT)
        await grid_scan_with_two_bcs_motors(HOST, PORT)
        # await scan_with_interruption(HOST, PORT)

        # Area detector examples (under development)
        # print("\n" + "=" * 60)
        # print("AREA DETECTOR EXAMPLES")
        # print("=" * 60 + "\n")
        # scan_with_area_detector()
        # fly_scan_with_area_detector()

    asyncio.run(run_all_examples())
