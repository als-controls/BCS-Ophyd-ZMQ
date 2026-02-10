"""
Tests for the BCSMotor class.
"""

import pytest
from bcsophyd.zmq.bcs_motor import BCSMotor


class TestBCSMotor:
    """Tests for BCSMotor."""

    def test_motor_instantiation(self):
        """Test that BCSMotor can be instantiated."""
        motor = BCSMotor(
            name="test_motor",
            originalName="Test Motor",
            itemType="motor",
            prefix="",
            units="mm",
            bridgeIP="localhost",
            bridgePort=5577,
        )
        assert motor is not None
        assert motor.name == "test_motor"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_motor_read(self, bcs_host, bcs_port):
        """
        Test reading motor position.

        This is an integration test that requires a running BCS server.
        """
        from bcsophyd.zmq.bcs_device_manager import BCSDeviceManager

        manager = BCSDeviceManager(host=bcs_host, port=bcs_port)
        await manager.connect()

        results = manager.client.search_regex(name="Motor3")
        if not results:
            pytest.skip("Motor 'Motor3' not found on server")

        motor = results[0].get()
        position = motor.get()
        assert position is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_motor_bluesky_read(self, bcs_host, bcs_port):
        """
        Test Bluesky-compatible read() method.

        This is an integration test that requires a running BCS server.
        """
        from bcsophyd.zmq.bcs_device_manager import BCSDeviceManager

        manager = BCSDeviceManager(host=bcs_host, port=bcs_port)
        await manager.connect()

        results = manager.client.search_regex(name="Motor3")
        if not results:
            pytest.skip("Motor 'Motor3' not found on server")

        motor = results[0].get()
        read_result = await motor.read()

        assert isinstance(read_result, dict)
        assert "value" in str(read_result) or len(read_result) > 0
