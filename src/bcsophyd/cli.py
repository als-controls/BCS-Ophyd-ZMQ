"""
Command-line interface for bcsophyd.

Provides tools for testing BCS server connections and listing available devices.
"""

import asyncio
import sys

import click
from loguru import logger

from . import __version__
from .zmq import BCSDeviceManager, BCSServer


def configure_logging(verbose: int, quiet: bool):
    """Configure loguru based on verbosity level."""
    logger.remove()  # Remove default handler

    if quiet:
        # Only show errors
        logger.add(sys.stderr, level="ERROR")
    elif verbose == 0:
        # Normal: show warnings and above
        logger.add(sys.stderr, level="WARNING")
    elif verbose == 1:
        # -v: show info
        logger.add(sys.stderr, level="INFO")
    elif verbose == 2:
        # -vv: show debug
        logger.add(sys.stderr, level="DEBUG")
    else:
        # -vvv+: show trace
        logger.add(sys.stderr, level="TRACE")


@click.group()
@click.version_option(version=__version__, prog_name="bcsophyd")
@click.option("-v", "--verbose", count=True, help="Increase verbosity (use -v, -vv, -vvv)")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output except errors")
@click.pass_context
def main(ctx, verbose, quiet):
    """
    bcsophyd - CLI tools for the Beamline Control System (BCS).

    Test connections and discover devices on BCS servers.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    configure_logging(verbose, quiet)


@main.command()
@click.option(
    "-H", "--host",
    default="127.0.0.1",
    show_default=True,
    help="BCS server host address"
)
@click.option(
    "-p", "--port",
    default=5577,
    show_default=True,
    type=int,
    help="BCS server port"
)
@click.option(
    "-t", "--timeout",
    default=5000,
    show_default=True,
    type=int,
    help="Connection timeout in milliseconds"
)
@click.pass_context
def test(ctx, host, port, timeout):
    """
    Test connection to a BCS server.

    Attempts to connect to the specified BCS server and reports success or failure.
    """
    quiet = ctx.obj.get("quiet", False)

    if not quiet:
        click.echo(f"Testing connection to BCS server at {host}:{port}...")

    async def _test_connection():
        manager = BCSDeviceManager(host=host, port=port, timeout_ms=timeout)
        return await manager.check_server_connection_async()

    try:
        success = asyncio.run(_test_connection())

        if success:
            if not quiet:
                click.secho("Connection successful!", fg="green")
            sys.exit(0)
        else:
            if not quiet:
                click.secho("Connection failed.", fg="red")
            sys.exit(1)

    except Exception as e:
        if not quiet:
            click.secho(f"Connection error: {e}", fg="red")
        sys.exit(1)


@main.command()
@click.option(
    "-H", "--host",
    default="127.0.0.1",
    show_default=True,
    help="BCS server host address"
)
@click.option(
    "-p", "--port",
    default=5577,
    show_default=True,
    type=int,
    help="BCS server port"
)
@click.option(
    "-t", "--timeout",
    default=5000,
    show_default=True,
    type=int,
    help="Connection timeout in milliseconds"
)
@click.option(
    "--motors/--no-motors",
    default=True,
    help="Show motors"
)
@click.option(
    "--signals/--no-signals",
    default=True,
    help="Show analog input signals"
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="Output as JSON"
)
@click.pass_context
def devices(ctx, host, port, timeout, motors, signals, output_json):
    """
    List available devices from a BCS server.

    Connects to the BCS server, retrieves the device configuration,
    and displays all available motors and analog input signals.
    """
    quiet = ctx.obj.get("quiet", False)

    async def _get_devices():
        manager = BCSDeviceManager(host=host, port=port, timeout_ms=timeout)
        success = await manager.connect()

        if not success:
            return None, None

        motor_list = []
        signal_list = []

        for item in manager.client.items():
            item_dict = {
                "name": item.name,
                "device_class": item.device_class,
            }

            # Add extra metadata if available
            if hasattr(item, "kwargs") and item.kwargs:
                if "originalName" in item.kwargs:
                    item_dict["original_name"] = item.kwargs["originalName"]
                if "units" in item.kwargs:
                    item_dict["units"] = item.kwargs["units"]

            if "motor" in item.device_class.lower():
                motor_list.append(item_dict)
            elif "signal" in item.device_class.lower():
                signal_list.append(item_dict)

        return motor_list, signal_list

    if not quiet and not output_json:
        click.echo(f"Connecting to BCS server at {host}:{port}...")

    try:
        motor_list, signal_list = asyncio.run(_get_devices())

        if motor_list is None:
            if not quiet:
                click.secho("Failed to connect to BCS server.", fg="red")
            sys.exit(1)

        if output_json:
            import json
            output = {}
            if motors:
                output["motors"] = motor_list
            if signals:
                output["signals"] = signal_list
            click.echo(json.dumps(output, indent=2))
        else:
            if motors and motor_list:
                click.secho(f"\nMotors ({len(motor_list)}):", fg="cyan", bold=True)
                click.echo("-" * 60)
                for m in sorted(motor_list, key=lambda x: x["name"]):
                    original = m.get("original_name", "")
                    units = m.get("units", "")
                    if original and original != m["name"]:
                        click.echo(f"  {m['name']:<30} ({original}){f' [{units}]' if units else ''}")
                    else:
                        click.echo(f"  {m['name']:<30}{f' [{units}]' if units else ''}")

            if signals and signal_list:
                click.secho(f"\nAnalog Inputs ({len(signal_list)}):", fg="cyan", bold=True)
                click.echo("-" * 60)
                for s in sorted(signal_list, key=lambda x: x["name"]):
                    original = s.get("original_name", "")
                    units = s.get("units", "")
                    if original and original != s["name"]:
                        click.echo(f"  {s['name']:<30} ({original}){f' [{units}]' if units else ''}")
                    else:
                        click.echo(f"  {s['name']:<30}{f' [{units}]' if units else ''}")

            if not motors and not signals:
                click.echo("No device types selected. Use --motors and/or --signals.")
            elif not motor_list and not signal_list:
                click.echo("No devices found on server.")
            else:
                total = (len(motor_list) if motors else 0) + (len(signal_list) if signals else 0)
                click.echo(f"\nTotal: {total} device(s)")

        sys.exit(0)

    except Exception as e:
        if not quiet:
            click.secho(f"Error: {e}", fg="red")
        logger.exception("Error listing devices")
        sys.exit(1)


@main.command()
@click.option(
    "-H", "--host",
    default="127.0.0.1",
    show_default=True,
    help="BCS server host address"
)
@click.option(
    "-p", "--port",
    default=5577,
    show_default=True,
    type=int,
    help="BCS server port"
)
@click.argument("name")
@click.pass_context
def read(ctx, host, port, name):
    """
    Read the current value of a device.

    NAME is the device name (use 'bcsophyd devices' to list available devices).
    """
    quiet = ctx.obj.get("quiet", False)

    async def _read_device():
        manager = BCSDeviceManager(host=host, port=port)
        success = await manager.connect()

        if not success:
            return None, "Failed to connect to BCS server"

        # Search for the device
        results = manager.client.search_regex(name=name)
        if not results:
            # Try case-insensitive search
            results = manager.client.search_regex(name=f"(?i){name}")

        if not results:
            return None, f"Device '{name}' not found"

        # Get the device
        device = results[0].get()

        # Try to read the value
        if hasattr(device, "get"):
            # Check if it's async
            value = device.get()
            if asyncio.iscoroutine(value):
                value = await value
            return value, None
        else:
            return None, f"Device '{name}' does not support reading"

    try:
        value, error = asyncio.run(_read_device())

        if error:
            if not quiet:
                click.secho(error, fg="red")
            sys.exit(1)

        click.echo(value)
        sys.exit(0)

    except Exception as e:
        if not quiet:
            click.secho(f"Error: {e}", fg="red")
        logger.exception("Error reading device")
        sys.exit(1)


if __name__ == "__main__":
    main()
