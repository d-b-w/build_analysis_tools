"""
Open a trace in perfetto webui

Usage:

    python3 open_perfetto_webui.py seam_trace.json
    cat seam_trace.json | python3 open_perfetto_webui.py 

"""
import http.server
import subprocess

_URL = 'https://ui.perfetto.dev/#!/?url=http://127.0.0.1:9001/trace.json'


def open_perfetto_webui(data):
    """
    Serve a json trace from memory and then close the server.
    Opens the web browser to view the trace in perfetto webui.
    """
    server_address = ('', 9001)
    
    class ServeOneThing(http.server.BaseHTTPRequestHandler):
        sent = False
        
        def log_message(self, format, *args):
            # Override to suppress logging
            pass
        
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Access-Control-Allow-Origin', '*')  # For CORS
            self.end_headers()
            self.wfile.write(data)
            ServeOneThing.sent = True

        def do_OPTIONS(self):
            self.send_response(200)
        def do_POST(self):
            self.send_response(200)
    
    try:
        httpd = http.server.HTTPServer(server_address, ServeOneThing)
        p = subprocess.Popen(['open', _URL])
        while not ServeOneThing.sent:
            httpd.handle_request()
        p.wait()
        httpd.server_close()
    except Exception as e:
        print(f"Error starting server: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Open a trace in perfetto webui")
    parser.add_argument('input', nargs='?', default='-', type=argparse.FileType('rb'))
    opts = parser.parse_args()
    with opts.input:
        data = opts.input.read()
    open_perfetto_webui(data)


if __name__ == '__main__':
    main()