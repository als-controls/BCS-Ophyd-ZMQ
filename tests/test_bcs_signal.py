"""
Tests for the BCSSignal class.
"""

import pytest
from bcsophyd.zmq.bcs_signal import BCSSignal


class TestBCSSignal:
    """Tests for BCSSignal."""

    def test_signal_instantiation(self):
        """Test that BCSSignal can be instantiated."""
        signal = BCSSignal(
            name="test_signal",
            originalName="Test Signal",
            itemType="ai",
            bridgeIP="localhost",
            bridgePort=5577,
            units="V",
        )
        assert signal is not None
        assert signal.name == "test_signal"

    def test_signal_default_timeout(self):
        """Test default timeout value."""
        signal = BCSSignal(
            name="test_signal",
            originalName="Test Signal",
            itemType="ai",
            bridgeIP="localhost",
            bridgePort=5577,
            units="V",
        )
        assert signal.timeout == 10000

    def test_signal_custom_timeout(self):
        """Test custom timeout value."""
        signal = BCSSignal(
            name="test_signal",
            originalName="Test Signal",
            itemType="ai",
            bridgeIP="localhost",
            bridgePort=5577,
            units="V",
            timeout=5000,
        )
        assert signal.timeout == 5000

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_signal_read(self, bcs_host, bcs_port):
        """
        Test reading a signal value.

        This is an integration test that requires a running BCS server
        and a signal named 'new_ai_2'.
        """
        from bcsophyd.zmq.bcs_device_manager import BCSDeviceManager

        manager = BCSDeviceManager(host=bcs_host, port=bcs_port)
        await manager.connect()

        results = manager.client.search_regex(name="new_ai_2")
        if not results:
            pytest.skip("Signal 'new_ai_2' not found on server")

        signal = results[0].get()
        value = await signal.get()
        assert value is not None
