"""
Pytest configuration and fixtures for bcsophyd tests.
"""

import pytest


def pytest_addoption(parser):
    """Add command-line options for BCS server connection."""
    parser.addoption(
        "--bcs-host",
        action="store",
        default="192.168.195.129",
        help="BCS server host address",
    )
    parser.addoption(
        "--bcs-port",
        action="store",
        default=5577,
        type=int,
        help="BCS server port",
    )


@pytest.fixture
def bcs_host(request):
    """Get BCS host from command line or use default."""
    return request.config.getoption("--bcs-host")


@pytest.fixture
def bcs_port(request):
    """Get BCS port from command line or use default."""
    return request.config.getoption("--bcs-port")


@pytest.fixture
def bcs_connection(bcs_host, bcs_port):
    """Provide BCS connection parameters as a tuple."""
    return (bcs_host, bcs_port)
