"""
BCS Device Discovery and Happi Integration

This example demonstrates how to use BCSDeviceManager to discover
devices from a BCS server and access them through the Happi database.
"""

import asyncio
from bcsophyd.zmq.bcs_device_manager import BCSDeviceManager


async def discover_all_devices(host: str, port: int):
    """
    Connect to BCS server and list all discovered devices.

    Parameters
    ----------
    host : str
        The BCS server host address
    port : int
        The BCS server port
    """
    print(f"Connecting to BCS server at {host}:{port}...")

    manager = BCSDeviceManager(host=host, port=port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    print("Successfully connected! Listing all devices:\n")

    for device in manager.client.items():
        print(device)


async def search_and_instantiate_signal(host: str, port: int, signal_name: str):
    """
    Search for an analog input signal by name and read its value.

    Parameters
    ----------
    host : str
        The BCS server host address
    port : int
        The BCS server port
    signal_name : str
        Name pattern to search for (regex supported)
    """
    print(f"Searching for signal matching '{signal_name}'...")

    manager = BCSDeviceManager(host=host, port=port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    results = manager.client.search_regex(name=signal_name)

    if not results:
        print(f"No devices found matching '{signal_name}'")
        print("Available devices:")
        for device in manager.client.items():
            print(f"  - {device}")
        return

    for item in results:
        print(f"Found: {item}")

        # Instantiate the device
        signal = item.get()
        print(f"Instantiated signal: {signal}")

        try:
            # Read the value
            value = await signal.get()
            print(f"Current value: {value}")

            # Test the Bluesky-compatible read() method
            read_result = await signal.read()
            print(f"Read result: {read_result}")
        except Exception as e:
            print(f"Error reading signal: {e}")

        print("=" * 40)


async def search_and_instantiate_motor(host: str, port: int, motor_name: str):
    """
    Search for a motor by name and read its position.

    Parameters
    ----------
    host : str
        The BCS server host address
    port : int
        The BCS server port
    motor_name : str
        Name pattern to search for (regex supported)
    """
    print(f"Searching for motor matching '{motor_name}'...")

    manager = BCSDeviceManager(host=host, port=port)
    success = await manager.connect()

    if not success:
        print("Failed to connect to BCS server")
        return

    results = manager.client.search_regex(name=motor_name)

    if not results:
        print(f"No motors found matching '{motor_name}'")
        return

    for item in results:
        print(f"Found: {item}")

        # Instantiate the motor
        motor = item.get()
        print(f"Instantiated motor: {motor}")

        try:
            # Read position (synchronous)
            position = motor.get()
            print(f"Current position: {position}")

            # Test the Bluesky-compatible read() method
            read_result = await motor.read()
            print(f"Read result: {read_result}")
        except Exception as e:
            print(f"Error reading motor: {e}")

        print("=" * 40)


if __name__ == "__main__":
    # Default BCS server address - modify as needed
    HOST = "192.168.195.129"
    PORT = 5577

    async def main():
        # Discover all devices
        await discover_all_devices(HOST, PORT)
        print("\n" + "=" * 60 + "\n")

        # Search for specific signal
        await search_and_instantiate_signal(HOST, PORT, "new_ai_2")
        print("\n" + "=" * 60 + "\n")

        # Search for specific motor
        await search_and_instantiate_motor(HOST, PORT, "Motor2")

    asyncio.run(main())
