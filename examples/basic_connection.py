"""
Basic BCS Server Connection Test

This example demonstrates how to test connectivity to a BCS ZeroMQ server.
"""

import asyncio
from bcsophyd.zmq.bcs_server import BCSServer


async def test_connection(host: str, port: int) -> bool:
    """
    Test connection to a BCS ZeroMQ server.

    Parameters
    ----------
    host : str
        The BCS server host address
    port : int
        The BCS server port

    Returns
    -------
    bool
        True if connection successful, False otherwise
    """
    print(f"Testing connection to BCS ZeroMQ server at {host}:{port}...")

    bcs_server = BCSServer()

    try:
        await bcs_server.connect(host, port)
        print(f"Successfully connected to BCS ZeroMQ server at {host}:{port}")

        # Test a simple command
        response = await bcs_server.test_connection()
        print(f"Test connection response: {response}")

        return True
    except Exception as e:
        print(f"Error connecting to BCS ZeroMQ server: {e}")
        return False


if __name__ == "__main__":
    # Default BCS server address - modify as needed
    HOST = "192.168.195.129"
    PORT = 5577

    asyncio.run(test_connection(HOST, PORT))
