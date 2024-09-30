import argparse
import asyncio
from typing import Any

from rich.console import Console

from open_gopro import Params, WirelessGoPro, constants, proto
from open_gopro.logger import setup_logging

console = Console()  # rich consoler printer
mygopros = {
    "labhero1": "GoPro XXXX",

    "labhero2": "GoPro XXXX",

    "labhero3": "GoPro XXXX",

    "labhero4": "GoPro XXXX", # add as many as you have, describing the gopro makes it faster. 
}

async def setup_gopro(name: str, gopro_target: str, ssid: str, password: str) -> None:
    """ Set up the GoPros to stream"""
    print(gopro_target)
    gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
    await asyncio.sleep(2)
    await gopro_obj.open(retries=100)
    
    await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
    await gopro_obj.ble_command.register_livestream_status(
        register=[proto.EnumRegisterLiveStreamStatus.REGISTER_LIVE_STREAM_STATUS_STATUS]
    )

    console.print(f"[yellow]Connecting to {ssid}...")
    await gopro_obj.connect_to_access_point(ssid, password)

    # Start livestream
    livestream_is_ready = asyncio.Event()

    async def wait_for_livestream_start(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
        if update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_READY:
            livestream_is_ready.set()

    console.print("[yellow]Configuring livestream...")
    gopro_obj.register_update(wait_for_livestream_start, constants.ActionId.LIVESTREAM_STATUS_NOTIF)
    await gopro_obj.ble_command.set_livestream_mode(
        url=f"rtmp://IPADDRESSOFYOURSERVER/live/{name}",
        minimum_bitrate=800,
        maximum_bitrate=8000,
        starting_bitrate=5000,
    )

    # Wait to receive livestream started status
    console.print("[yellow]Waiting for livestream to be ready...\n")
    await livestream_is_ready.wait()

    # Optional delay
    await asyncio.sleep(2)

    console.print("[yellow]Starting livestream")
    assert (await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)).ok

    console.print("[yellow]Livestream is now streaming and should be available for viewing.")

async def main(args: argparse.Namespace) -> None:
    setup_logging(__name__, args.log)

    # List of tasks for concurrent execution
    tasks = []
    ssid = "YOURSSID"
    password = "YOURSSIDPASSWORD"

    for name, gopro_target in mygopros.items():
        tasks.append(setup_gopro(name, gopro_target, ssid, password))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", help="Log file", required=False)
    args = parser.parse_args()

    asyncio.run(main(args))
