"""
Tests for the BCSServer class.

These tests require a running BCS server. Use pytest markers to skip
when no server is available.
"""

import pytest
from bcsophyd.zmq.bcs_server import BCSServer


class TestBCSServer:
    """Tests for BCSServer connectivity and basic operations."""

    @pytest.mark.asyncio
    async def test_server_instantiation(self):
        """Test that BCSServer can be instantiated."""
        server = BCSServer()
        assert server is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_connection(self, bcs_host, bcs_port):
        """
        Test connecting to a BCS server.

        This is an integration test that requires a running BCS server.
        Run with: pytest -m integration --bcs-host=<host> --bcs-port=<port>
        """
        server = BCSServer()
        await server.connect(bcs_host, bcs_port)
        # Connection should complete without error

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_server_test_connection(self, bcs_host, bcs_port):
        """
        Test the test_connection method.

        This is an integration test that requires a running BCS server.
        """
        server = BCSServer()
        await server.connect(bcs_host, bcs_port)
        response = await server.test_connection()
        assert response is not None
