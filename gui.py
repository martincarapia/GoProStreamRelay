import asyncio
import threading
from tkinter import Tk, Frame, Label, Entry, Button, Text
from rich.console import Console
from open_gopro import Params, WirelessGoPro, constants, proto
from open_gopro.logger import setup_logging
from typing import Any
import sys

console = Console()  # rich console printer

class GoProApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("GoPro Streaming Setup")
        self.geometry("600x400")

        # Create UI elements
        self.ssid_label = Label(self, text="SSID:")
        self.ssid_label.grid(row=0, column=0, sticky='w')
        self.ssid_entry = Entry(self)
        self.ssid_entry.grid(row=0, column=1, sticky='w')
        self.ssid_entry.bind("<KeyRelease>", lambda event: self.update_start_button_state())

        self.password_label = Label(self, text="Password:")
        self.password_label.grid(row=1, column=0, sticky='w')
        self.password_entry = Entry(self, show='*')
        self.password_entry.grid(row=1, column=1, sticky='w')
        self.password_entry.bind("<KeyRelease>", lambda event: self.update_start_button_state())

        self.server_ip_label = Label(self, text="Server IP Address:")
        self.server_ip_label.grid(row=2, column=0, sticky='w')
        self.server_ip_entry = Entry(self)
        self.server_ip_entry.grid(row=2, column=1, sticky='w')
        self.server_ip_entry.bind("<KeyRelease>", lambda event: self.update_start_button_state())

        self.gopro_frame = Frame(self)
        self.gopro_frame.grid(row=3, column=0, columnspan=2, sticky='w')

        self.add_gopro_button = Button(self, text="Add GoPro", command=self.add_gopro_block)
        self.add_gopro_button.grid(row=4, column=0, sticky='w')

        self.start_button = Button(self, text="Start Streaming", command=self.start_streaming)
        self.start_button.grid(row=5, column=0, sticky='w')
        self.start_button.config(state='disabled')  # Initially disable the start button

        self.stop_button = Button(self, text="Stop Streaming", command=self.stop_streaming)
        self.stop_button.grid(row=5, column=0, sticky='w')
        self.stop_button.grid_remove()  # Initially hide the stop button

        self.console_output = Text(self, height=10)
        self.console_output.grid(row=6, column=0, columnspan=2, sticky='w')

        self.gopro_blocks = []

        # Bind the window close event to the on_closing method
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_gopro_block(self):
        """Add a new GoPro block to the UI for entering GoPro details."""
        gopro_block = Frame(self.gopro_frame)
        gopro_block.pack(pady=5)

        gopro_name_label = Label(gopro_block, text="Stream Key:")
        gopro_name_label.pack(side='left')

        gopro_name_entry = Entry(gopro_block)
        gopro_name_entry.pack(side='left')

        gopro_target_label = Label(gopro_block, text="GoPro Target:")
        gopro_target_label.pack(side='left')

        gopro_target_entry = Entry(gopro_block)
        gopro_target_entry.pack(side='left')

        remove_button = Button(gopro_block, text="X", command=lambda: self.remove_gopro_block(gopro_block))
        remove_button.pack(side='left')

        self.gopro_blocks.append((gopro_block, gopro_name_entry, gopro_target_entry, remove_button))
        self.update_start_button_state()

    def remove_gopro_block(self, gopro_block):
        """Remove a GoPro block from the UI and the list of GoPro blocks."""
        for block in self.gopro_blocks:
            if block[0] == gopro_block:
                self.gopro_blocks.remove(block)
                break
        gopro_block.destroy()
        self.update_start_button_state()

    def update_start_button_state(self):
        """Enable or disable the start button based on the number of GoPro blocks and input fields."""
        if self.gopro_blocks and self.ssid_entry.get() and self.password_entry.get() and self.server_ip_entry.get():
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')

    def log(self, message):
        """Log messages to the console output text widget."""
        self.console_output.insert("end", message + "\n")
        self.console_output.see("end")

    async def setup_gopro(self, name: str, gopro_target: str, ssid: str, password: str) -> None:
        """Set up the GoPros to stream."""
        gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
        await gopro_obj.open(retries=100)

        await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        await asyncio.sleep(2)
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
        """Stop the live stream for a specific GoPro."""
        gopro_obj = WirelessGoPro(target=gopro_target, enable_wifi=False)
        await gopro_obj.open(retries=100)

        await gopro_obj.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        await gopro_obj.ble_command.release_network()
        self.log("Livestream has been stopped.")

    async def main(self, stream: bool = True) -> None:
        """Main function to handle starting or stopping streams for all GoPros."""
        ssid = self.ssid_entry.get()
        password = self.password_entry.get()

        # List of tasks for concurrent execution
        tasks = []
        for _, gopro_name_entry, gopro_target_entry, _ in self.gopro_blocks:
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
        self.start_button.grid_remove()  # Hide the start button
        self.stop_button.grid()  # Show the stop button
        self.add_gopro_button.config(state='disabled')  # Disable the add GoPro button
        for _, _, _, remove_button in self.gopro_blocks:
            remove_button.pack_forget()  # Hide the remove buttons

    def stream_gopros_concurrent(self):
        """Connect to all GoPros and start streaming concurrently."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main())
        loop.run_forever()  # Keep the loop running to avoid closing it prematurely

    def stop_streaming_concurrent(self, run_forever: bool = True):
        """Stop the streaming in a new thread to avoid blocking the Tkinter event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.main(stream=False))
        if run_forever:
            loop.run_forever()  # Keep the loop running to avoid closing it prematurely
        else:
            loop.close()

    def stop_streaming(self):
        """Stop the streaming in a new thread to avoid blocking the Tkinter event loop."""
        threading.Thread(target=self.stop_streaming_concurrent).start()
        self.stop_button.grid_remove()  # Hide the stop button
        self.start_button.grid()  # Show the start button
        self.add_gopro_button.config(state='normal')  # Enable the add GoPro button
        for _, _, _, remove_button in self.gopro_blocks:
            remove_button.pack(side='left')  # Show the remove buttons

    def on_closing(self):
        """Handle the window close event."""
        if self.gopro_blocks:
            self.stop_streaming_concurrent(run_forever=False)
        sys.exit()


if __name__ == "__main__":
    setup_logging(__name__, None)  # You can modify logging as needed
    app = GoProApp()
    app.mainloop()