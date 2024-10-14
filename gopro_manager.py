# gopro_manager.py
import asyncio
from open_gopro import Params, WirelessGoPro, constants, proto
from typing import Any
import requests

class GoProManager:
    def __init__(self, log_callback):
        self.log = log_callback

    async def setup_gopro(self, name: str, gopro_target: str, ssid: str, password: str, server_address: str) -> None:
        """Set up the GoPros to stream."""
        try:
            gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
            await gopro_obj.open(retries=100)
        except Exception as e:
            self.log(f"Failed to connect to {gopro_target}: {e}")
            return

        try:
            await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
            await asyncio.sleep(2)
            await gopro_obj.ble_command.register_livestream_status(
                register=[proto.EnumRegisterLiveStreamStatus.REGISTER_LIVE_STREAM_STATUS_STATUS]
            )

            self.log(f"{gopro_target}: Connecting to {ssid}...")
            await gopro_obj.connect_to_access_point(ssid, password)

            # Start livestream
            livestream_is_ready = asyncio.Event()

            async def wait_for_livestream_start(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
                if update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_READY:
                    livestream_is_ready.set()

            self.log(f"{gopro_target}: Configuring livestream for...")
            gopro_obj.register_update(wait_for_livestream_start, constants.ActionId.LIVESTREAM_STATUS_NOTIF)
            await gopro_obj.ble_command.set_livestream_mode(
                url=f"rtmp://{server_address}/live/{name}",
                minimum_bitrate=800,
                maximum_bitrate=8000,
                starting_bitrate=5000,
            )

            self.log(f"{gopro_target}: Waiting for livestream to be ready...\n")
            await livestream_is_ready.wait()

            # Optional delay
            await asyncio.sleep(2)

            self.log(f"{gopro_target}: Starting livestream")
            await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)
            self.log(f"{gopro_target}: Livestream is now streaming and should be available for viewing.")
            await gopro_obj.close()
            return
        except Exception as e:
            self.log(f"Error during setup for {gopro_target}: {e}")

    async def stop_live_stream(self, gopro_target: str) -> None:
        """Stop the live stream for a specific GoPro."""
        gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
        await gopro_obj.open(retries=100)

        await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        await gopro_obj.close()
        self.log(f"{gopro_target}: Livestream has been stopped.")
        return

    def run_script_on_server(self, script_path: str, action: str, server_address: str, input_streams=None, output_stream=None):
        """Run a Python script on the server with optional arguments."""
        server_url = server_address
        try:
            # Construct the query parameters
            query_params = f'script_path={script_path}&action={action}'
            if input_streams:
                for i, stream in enumerate(input_streams):
                    query_params += f'&input{i}={stream}'
            if output_stream:
                query_params += f'&output={output_stream}'
            
            # Send the request to the server
            response = requests.get(f'http://{server_url}:8080?{query_params}')
            if response.status_code == 200:
                self.log(f"Script output: {response.text}")
            else:
                self.log(f"Error: {response.status_code}\n{response.text}")
            
        except Exception as e:
            self.log(f"Failed to connect to server: {e}")



