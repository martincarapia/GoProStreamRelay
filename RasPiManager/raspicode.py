import json
import asyncio
import threading
import RPi.GPIO as GPIO
from DisplayDriver import lcd
from rich.console import Console
from gopro_manager import GoProManager
from open_gopro.logger import setup_logging

# Constants
BUTTON_PIN = 26  # Pin number where the button is connected

CONFIG_FILE = 'config.json'  # Path to the configuration file
console = Console()  # rich console printer

# Setup
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Set up the button pin as an input with an internal pull-down resistor

class GoProApp:
    def __init__(self, config):
        self.mylcd = lcd()
        self.button_state = False  # Initial state
        self.ssid = config['ssid']
        self.password = config['password']
        self.server_ip = config['server_ip']
        self.output_server = config['output_server']
        self.gopro_blocks = config['gopro_blocks']
        self.mymanager = GoProManager(self.log)

    def update_display(self):
        """Update the LCD display based on the button state."""
        if self.button_state:
            self.mylcd.lcd_scroll_text("Livestreaming Started...")
            self.mylcd.lcd_display_string("Livestreaming...", 1)
            self.mylcd.lcd_display_string("Press me to stop", 2)
        else:
            self.mylcd.lcd_scroll_text("Livestreaming Stopped...")
            self.mylcd.lcd_display_string("Press me to", 1)
            self.mylcd.lcd_display_string("start Livestreaming", 2)

    def to_streaming(self, stream: bool = True):
        """Start the streaming in a new thread to avoid blocking the main event loop."""
        threading.Thread(target=lambda: self._sequential_stream(stream)).start()

    def _sequential_stream(self, do_i_stream: bool = True):
        """Start or stop the streaming sequentially."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.main(do_i_stream))
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    def log(self, message):
        """Log messages to the console or a log file."""
        console.log(message)  # Using rich console for logging

    async def main(self, stream: bool = True) -> None:
        """Main function to handle starting or stopping streams for all GoPros."""
        for block in self.gopro_blocks:
            name = block['name']
            target = block['target']
            if stream:
                self.log(f"Setting up GoPro: {name} with target: {target}")
                try:
                    await self.mymanager.setup_gopro(name, target, self.ssid, self.password, self.server_ip)
                    self.log(f"Successfully set up GoPro: {name}")
                except Exception as e:
                    self.log(f"Failed to set up GoPro {name}: {e}")
            else:
                self.log(f"Stopping live stream for GoPro: {target}")
                try:
                    await self.mymanager.stop_live_stream(target)
                    self.log(f"Successfully stopped live stream for GoPro: {target}")
                except Exception as e:
                    self.log(f"Failed to stop live stream for GoPro {target}: {e}")

            # Wait in between bluetooth connections
            await asyncio.sleep(1) 

        # After all tasks are done running, request the server to run a specified python script
        if stream:
            # Collect input streams and output stream
            input_streams = [f"rtmp://{self.server_ip}/live/{block['name']}" for block in self.gopro_blocks]
            output_stream = self.output_server
            # Start stream script with arguments
            self.log(f"Starting stream script on server with input streams: {input_streams} and output stream: {output_stream}")
            self.mymanager.run_script_on_server('/Users/mieadmin/Documents/Code/LAB/StreamClient.py', 'start', self.server_ip, input_streams, output_stream)
        else:
            # Stop stream script
            self.log(f"Stopping stream script on server")
            self.mymanager.run_script_on_server('/Users/mieadmin/Documents/Code/LAB/StreamClient.py', 'stop', self.server_ip)

def load_config(file_path):
    """Load configuration from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

async def main():
    config = load_config(CONFIG_FILE)
    app = GoProApp(config)
    try:
        app.mylcd.lcd_display_string("Press me to", 1)
        app.mylcd.lcd_display_string("start Livestreaming", 2)
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                # Button was pressed
                app.button_state = not app.button_state  # Toggle state
                app.mylcd.lcd_clear()
                app.update_display()
                app.to_streaming(app.button_state)
            await asyncio.sleep(0.1)  # Use asyncio.sleep for non-blocking sleep
    except KeyboardInterrupt:
        pass
    finally:
        app.mylcd.lcd_clear()
        GPIO.cleanup()

if __name__ == "__main__":
    setup_logging(__name__, None)  # You can modify logging as needed
    asyncio.run(main())