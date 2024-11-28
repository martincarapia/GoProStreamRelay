import sys
import os

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
import asyncio
import threading
import json
from pathlib import Path
from tkinter import Tk, Frame, Label, Entry, Button, Text, PhotoImage, filedialog
from rich.console import Console
from open_gopro.logger import setup_logging
from gopro_manager import GoProManager

console = Console()  # rich console printer

class GoProApp(Tk):
    """
    A Tkinter-based GUI application for setting up GoPro streaming.
    """
    def __init__(self):
        """
        Initialize the GoProApp GUI.
        """
        super().__init__()
        self.mymanager = GoProManager(self.log)
        self.title("GoPro Streaming Setup")
        self.geometry("700x500")
        self.gopro_blocks = []

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

        self.start_button = Button(self, text="Start Streaming", command=self.to_streaming)
        self.start_button.grid(row=5, column=0, sticky='w')
        self.start_button.config(state='disabled')  # Initially disable the start button

        self.stop_button = Button(self, text="Stop Streaming", command=lambda: self.to_streaming(False))
        self.stop_button.grid(row=5, column=0, sticky='w')
        self.stop_button.grid_remove()  # Initially hide the stop button

        self.save_button = Button(self, text="Save Config", command=self.save_config)
        self.save_button.grid(row=6, column=0, sticky='w')

        self.load_button = Button(self, text="Load Config", command=self.load_config)
        self.load_button.grid(row=6, column=1, sticky='w')

        self.console_output = Text(self, height=10)
        self.console_output.grid(row=7, column=0, columnspan=2, sticky='w')

        # Bind the window close event to the on_closing method
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Automatically load the last saved configuration
        self.load_last_config()

    def add_gopro_block(self, name: str = "", target: str = "") -> None:
        """
        Add a new GoPro block to the UI for entering GoPro details.

        :param name: The name of the GoPro stream.
        :param target: The target GoPro device.
        :return: None
        """
        gopro_block = Frame(self.gopro_frame)
        gopro_block.pack(pady=5)

        gopro_name_label = Label(gopro_block, text="Stream Key:")
        gopro_name_label.pack(side='left')

        gopro_name_entry = Entry(gopro_block)
        gopro_name_entry.pack(side='left')
        gopro_name_entry.insert(0, name)

        gopro_target_label = Label(gopro_block, text="GoPro Target:")
        gopro_target_label.pack(side='left')

        gopro_target_entry = Entry(gopro_block)
        gopro_target_entry.pack(side='left')
        gopro_target_entry.insert(0, target)

        remove_button = Button(gopro_block, text="X", command=lambda: self.remove_gopro_block(gopro_block))
        remove_button.pack(side='left')

        self.gopro_blocks.append((gopro_block, gopro_name_entry, gopro_target_entry, remove_button))
        self.update_start_button_state()

    def remove_gopro_block(self, gopro_block: Frame) -> None:
        """
        Remove a GoPro block from the UI and the list of GoPro blocks.

        :param gopro_block: The GoPro block to remove.
        :return: None
        """
        for block in self.gopro_blocks:
            if block[0] == gopro_block:
                self.gopro_blocks.remove(block)
                break
        gopro_block.destroy()
        self.update_start_button_state()

    def update_start_button_state(self) -> None:
        """
        Enable or disable the start button based on the number of GoPro blocks and input fields.

        :return: None
        """
        if self.gopro_blocks and self.ssid_entry.get() and self.password_entry.get() and self.server_ip_entry.get():
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')

    def hide_start_button(self) -> None:
        """
        Hide the start button and show the stop button.

        :return: None
        """
        self.start_button.grid_remove()  # Hide the start button
        self.stop_button.grid()  # Show the stop button
        self.add_gopro_button.config(state='disabled')  # Disable the add GoPro button
        for _, _, _, remove_button in self.gopro_blocks:
            remove_button.pack_forget()  # Hide the remove buttons

    def show_start_button(self) -> None:
        """
        Show the start button and hide the stop button.

        :return: None
        """
        self.stop_button.grid_remove()  # Hide the stop button
        self.start_button.grid()  # Show the start button
        self.add_gopro_button.config(state='normal')  # Enable the add GoPro button
        for _, _, _, remove_button in self.gopro_blocks:
            remove_button.pack(side='left')  # Show the remove buttons
    
    def to_streaming(self, stream: bool = True) -> None:
        """
        Start the streaming in a new thread to avoid blocking the Tkinter event loop.

        :param stream: Boolean indicating whether to start or stop streaming.
        :return: None
        """
        threading.Thread(target=lambda: self._concurrent_stream(stream)).start()
    
    def _concurrent_stream(self, do_i_stream: bool = True) -> None:
        """
        Start or stop the streaming concurrently.

        :param do_i_stream: Boolean indicating whether to start or stop streaming.
        :return: None
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main(do_i_stream))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()    

    def save_config(self) -> None:
        """
        Save the current configuration to a JSON file.

        :return: None
        """
        config = {
            'ssid': self.ssid_entry.get(),
            'password': self.password_entry.get(),
            'server_ip': self.server_ip_entry.get(),
            'gopros': [
                {'name': gopro_name_entry.get(), 'target': gopro_target_entry.get()}
                for _, gopro_name_entry, gopro_target_entry, _ in self.gopro_blocks
            ]
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(config, f)
            self.log(f"Configuration saved to {file_path}")
            # Save the path of the last configuration
            with open('last_config.json', 'w') as f:
                json.dump({'last_config': file_path}, f)

    def load_config(self, file_path: str = None) -> None:
        """
        Load a configuration from a JSON file.

        :param file_path: The path to the configuration file.
        :return: None
        """
        if not file_path:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                config = json.load(f)
            self.ssid_entry.delete(0, 'end')
            self.ssid_entry.insert(0, config['ssid'])
            self.password_entry.delete(0, 'end')
            self.password_entry.insert(0, config['password'])
            self.server_ip_entry.delete(0, 'end')
            self.server_ip_entry.insert(0, config['server_ip'])
            for gopro_block, _, _, _ in self.gopro_blocks:
                gopro_block.destroy()
            self.gopro_blocks.clear()
            for gopro in config['gopros']:
                self.add_gopro_block(gopro['name'], gopro['target'])
            self.log(f"Configuration loaded from {file_path}")

    def load_last_config(self) -> None:
        """
        Load the last saved configuration if it exists.

        :return: None
        """
        if Path('last_config.json').exists():
            with open('last_config.json', 'r') as f:
                last_config = json.load(f)
                self.load_config(last_config['last_config'])

    def on_closing(self) -> None:
        """
        Handle the window close event.

        :return: None
        """
        if self.gopro_blocks:
            self.to_streaming(False)
        sys.exit()

    def log(self, message: str) -> None:
        """
        Log messages to the console output text widget.

        :param message: The message to log.
        :return: None
        """
        self.console_output.insert("end", message + "\n")
        self.console_output.see("end")

    async def main(self, stream: bool = True) -> None:
        """
        Main function to handle starting or stopping streams for all GoPros.

        :param stream: Boolean indicating whether to start or stop streaming.
        :return: None
        """
        ssid = self.ssid_entry.get()
        password = self.password_entry.get()

        # List of tasks for concurrent execution
        tasks = []
        for block in self.gopro_blocks:
            if block is None:
                self.log("Error: gopro_block is None")
                continue
            _, gopro_name_entry, gopro_target_entry, _ = block
            if gopro_name_entry is None or gopro_target_entry is None:
                self.log("Error: gopro_name_entry or gopro_target_entry is None")
                continue
            name = gopro_name_entry.get()
            target = gopro_target_entry.get()
            if stream:
                self.hide_start_button()
                self.log(f"Setting up GoPro: {name} with target: {target}")
                tasks.append(self.mymanager.setup_gopro(name, target, ssid, password, self.server_ip_entry.get()))
            else:
                self.show_start_button()
                self.log(f"Stopping live stream for GoPro: {target}")
                tasks.append(self.mymanager.stop_live_stream(target))

        # Run all tasks concurrently and handle exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any exceptions that occurred
        for result in results:
            if isinstance(result, Exception):
                self.log(f"Task failed with exception: {result}")
        script_path = '/Users/mieadmin/Documents/Code/DynamicStreamManager/StreamClient.py'
        # After all tasks are done running, request the server to run a specified python script
        if stream:
            # Collect input streams and output stream
            input_streams = [f"rtmp://{self.server_ip_entry.get()}/live/{gopro_name_entry.get()}" for _, gopro_name_entry, _, _ in self.gopro_blocks]
            output_stream = f"rtmp://{self.server_ip_entry.get()}/live/output"
            # Start stream script with arguments
            self.log(f"Starting stream script on server with input streams: {input_streams} and output stream: {output_stream}")
            self.mymanager.run_script_on_server(script_path, 'start', self.server_ip_entry.get(), input_streams, output_stream)
        else:
            # Stop stream script
            self.log(f"Stopping stream script on server")
            self.mymanager.run_script_on_server(script_path, 'stop', self.server_ip_entry.get())

if __name__ == "__main__":
    setup_logging(__name__, None)  # You can modify logging as needed
    app = GoProApp()
    app.mainloop()