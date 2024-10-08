# server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import subprocess

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        
        script_path = query_params.get('script_path', [None])[0]
        action = query_params.get('action', [None])[0]
        inputs = [query_params.get(f'input{i}', [None])[0] for i in range(len(query_params)) if f'input{i}' in query_params]
        output = query_params.get('output', [None])[0]

        if script_path and action:
            if action == 'start' and inputs and output:
                args = [script_path, action, '--inputs'] + inputs + ['--output', output]
            elif action == 'stop':
                args = [script_path, action]
            else:
                output = "Error: For 'start' action, inputs and output are required."
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(output.encode())
                return

            try:
                result = subprocess.run(['python3'] + args, capture_output=True, text=True)
                output = result.stdout
                self.send_response(200)
            except Exception as e:
                output = str(e)
                self.send_response(500)
        else:
            output = "Error: script_path and action are required."
            self.send_response(400)

        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(output.encode())

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()