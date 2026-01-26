"""
Tests for the BCSDeviceManager class.

These tests require a running BCS server for integration tests.
"""

import pytest
from bcsophyd.zmq.bcs_device_manager import BCSDeviceManager


class TestBCSDeviceManager:
    """Tests for BCSDeviceManager."""

    def test_manager_instantiation(self):
        """Test that BCSDeviceManager can be instantiated."""
        manager = BCSDeviceManager(host="localhost", port=5577)
        assert manager is not None
        assert manager.host == "localhost"
        assert manager.port == 5577

    def test_manager_default_timeout(self):
        """Test default timeout value."""
        manager = BCSDeviceManager(host="localhost", port=5577)
        assert manager.timeout_ms == 5000

    def test_manager_custom_timeout(self):
        """Test custom timeout value."""
        manager = BCSDeviceManager(host="localhost", port=5577, timeout_ms=10000)
        assert manager.timeout_ms == 10000

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_manager_connect(self, bcs_host, bcs_port):
        """
        Test connecting to BCS server and populating devices.

        This is an integration test that requires a running BCS server.
        """
        manager = BCSDeviceManager(host=bcs_host, port=bcs_port)
        success = await manager.connect()
        assert success is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_manager_devices_populated(self, bcs_host, bcs_port):
        """
        Test that devices are populated after connection.

        This is an integration test that requires a running BCS server.
        """
        manager = BCSDeviceManager(host=bcs_host, port=bcs_port)
        await manager.connect()

        # Should have at least some devices
        devices = list(manager.client.items())
        assert len(devices) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_manager_search_motor(self, bcs_host, bcs_port):
        """
        Test searching for motors by name.

        This is an integration test that requires a running BCS server.
        """
        manager = BCSDeviceManager(host=bcs_host, port=bcs_port)
        await manager.connect()

        # Search for any motor (case insensitive)
        results = manager.client.search_regex(name=".*[Mm]otor.*")
        # Results may vary based on server configuration
        assert isinstance(results, list)
