import asyncio
import threading
from tkinter import Tk, Frame, Label, Entry, Button, Text
from rich.console import Console
from open_gopro import Params, WirelessGoPro, constants, proto
from open_gopro.logger import setup_logging
from typing import Any
from open_gopro.util import ainput

console = Console()  # rich console printer

class GoProApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("GoPro Streaming Setup")
        self.geometry("600x400")

        # Create UI elements
        self.ssid_label = Label(self, text="SSID:")
        self.ssid_label.pack()
        self.ssid_entry = Entry(self)
        self.ssid_entry.pack()

        self.password_label = Label(self, text="Password:")
        self.password_label.pack()
        self.password_entry = Entry(self, show='*')
        self.password_entry.pack()

        self.server_ip_label = Label(self, text="Server IP Address:")
        self.server_ip_label.pack()
        self.server_ip_entry = Entry(self)
        self.server_ip_entry.pack()

        self.gopro_frame = Frame(self)
        self.gopro_frame.pack()

        self.add_gopro_button = Button(self, text="Add GoPro", command=self.add_gopro_block)
        self.add_gopro_button.pack()

        self.start_button = Button(self, text="Start Streaming", command=self.start_streaming)
        self.start_button.pack()

        self.start_button = Button(self, text="Stop Streaming", command=self.stop_streaming)
        self.start_button.pack()

        self.console_output = Text(self, height=10)
        self.console_output.pack()

        self.gopro_blocks = []

    def add_gopro_block(self):
        gopro_block = Frame(self.gopro_frame)
        gopro_block.pack(pady=5)

        gopro_name_label = Label(gopro_block, text="GoPro Name:")
        gopro_name_label.pack(side='left')

        gopro_name_entry = Entry(gopro_block)
        gopro_name_entry.pack(side='left')

        gopro_target_label = Label(gopro_block, text="GoPro Target:")
        gopro_target_label.pack(side='left')

        gopro_target_entry = Entry(gopro_block)
        gopro_target_entry.pack(side='left')

        self.gopro_blocks.append((gopro_name_entry, gopro_target_entry))

    def log(self, message):
        self.console_output.insert("end", message + "\n")
        self.console_output.see("end")

    async def setup_gopro(self, name: str, gopro_target: str, ssid: str, password: str) -> None:
        """ Set up the GoPros to stream."""
        gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
        await gopro_obj.open(retries=100)

        await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        await gopro_obj.ble_command.register_livestream_status(
            register=[proto.EnumRegisterLiveStreamStatus.REGISTER_LIVE_STREAM_STATUS_STATUS]
        )

        self.log(f"Connecting to {ssid}...")
        await gopro_obj.connect_to_access_point(ssid, password)

        # Start livestream
        livestream_is_ready = asyncio.Event()

        async def wait_for_livestream_start(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
            if update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_READY:
                livestream_is_ready.set()

        self.log("Configuring livestream...")
        gopro_obj.register_update(wait_for_livestream_start, constants.ActionId.LIVESTREAM_STATUS_NOTIF)
        await gopro_obj.ble_command.set_livestream_mode(
            url=f"rtmp://{self.server_ip_entry.get()}/live/{name}",
            minimum_bitrate=800,
            maximum_bitrate=8000,
            starting_bitrate=5000,
        )

        self.log("Waiting for livestream to be ready...\n")
        await livestream_is_ready.wait()

        # Optional delay
        await asyncio.sleep(2)

        self.log("Starting livestream")
        assert (await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)).ok
        self.log("Livestream is now streaming and should be available for viewing.")

    async def stop_live_stream(self, gopro_target: str) -> None:
        gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
        await gopro_obj.open(retries=100)

        await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)

    async def main(self, stream: bool = True) -> None:
        ssid = self.ssid_entry.get()
        password = self.password_entry.get()

        # List of tasks for concurrent execution
        tasks = []
        for gopro_name_entry, gopro_target_entry in self.gopro_blocks:
            name = gopro_name_entry.get()
            target = gopro_target_entry.get()
            if stream:
                tasks.append(self.setup_gopro(name, target, ssid, password))
            else:
                tasks.append(self.stop_live_stream(target))

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    def start_streaming(self):
        """Start the streaming in a new thread to avoid blocking the Tkinter event loop."""
        threading.Thread(target=self.stream_gopros_concurrent).start()

    def stream_gopros_concurrent(self):
        """Connect to all GoPros and start streaming concurrently."""
        asyncio.run(self.main())
    
    def stop_streaming_concurrent(self):
        """Stop the streaming in a new thread to avoid blocking the Tkinter event loop."""
        asyncio.run(self.main(stream=False))

    def stop_streaming(self):
        """Stop the streaming in a new thread to avoid blocking the Tkinter event loop."""
        threading.Thread(target=self.stop_streaming_concurrent).start()

    

if __name__ == "__main__":
    setup_logging(__name__, None)  # You can modify logging as needed
    app = GoProApp()
    app.mainloop()