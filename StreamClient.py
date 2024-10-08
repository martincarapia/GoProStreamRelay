import argparse
import StreamManagerFFMPEG

def main():
    parser = argparse.ArgumentParser(description='Manage RTMP streams.')
    parser.add_argument('action', choices=['start', 'stop'], help='Action to perform: start or stop the stream.')
    parser.add_argument('--inputs', nargs='+', help='List of RTMP input streams.')
    parser.add_argument('--output', help='RTMP output stream.')

    args = parser.parse_args()

    stream_manager = StreamManagerFFMPEG.StreamManager()

    if args.action == 'start':
        if not args.inputs or not args.output:
            print("Error: --inputs and --output are required for starting the stream.")
            return
        input_streams = args.inputs
        output_stream = args.output
        print(f"Output stream has started.")
        stream_manager.combine_rtmp_streams(input_streams, output_stream)
    elif args.action == 'stop':
        stream_manager.stop_ffmpeg_stream()
        print(f"Output stream has been stopped.")

if __name__ == '__main__':
    main()