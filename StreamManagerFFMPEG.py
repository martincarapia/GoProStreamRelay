import subprocess
import signal
import math

class StreamManager:
    def __init__(self):
        self.ffmpeg_process = None

    def combine_rtmp_streams(self, input_urls, output_url):
        # Construct the ffmpeg command
        ffmpeg_command = ['ffmpeg']
        
        # Add input streams
        for url in input_urls:
            ffmpeg_command.extend(['-i', url])
        
        # Determine the grid size (e.g., 2x2, 3x3)
        num_inputs = len(input_urls)
        grid_size = math.ceil(math.sqrt(num_inputs))
        
        # Construct the filter_complex part
        filter_complex = []
        for i in range(num_inputs):
            filter_complex.append(f'[{i}:v]scale=iw/{grid_size}:ih/{grid_size}[v{i}];')
        
        # Stack the videos horizontally and vertically
        for row in range(grid_size):
            row_inputs = ''.join([f'[v{row * grid_size + col}]' for col in range(grid_size) if row * grid_size + col < num_inputs])
            if row_inputs:
                filter_complex.append(f'{row_inputs}hstack=inputs={min(grid_size, num_inputs - row * grid_size)}[row{row}];')
        
        # Combine all rows vertically
        row_inputs = ''.join([f'[row{row}]' for row in range(grid_size) if f'[row{row}]' in ''.join(filter_complex)])
        if row_inputs and len(row_inputs.split('[')) - 1 > 1:
            filter_complex.append(f'{row_inputs}vstack=inputs={len(row_inputs.split("[")) - 1}[outv]')
        else:
            filter_complex.append(f'{row_inputs}copy[outv]')
        
        # Add filter_complex to the ffmpeg command
        ffmpeg_command.extend([
            '-filter_complex', ''.join(filter_complex),
            '-map', '[outv]',
            '-c:v', 'libx264',
            '-f', 'flv',
            output_url
        ])
        
        # Start the ffmpeg process
        self.ffmpeg_process = subprocess.Popen(ffmpeg_command)

    def stop_ffmpeg_stream(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.send_signal(signal.SIGINT)
            self.ffmpeg_process = None