"""
Lightweight Web Server and Interactive Dashboard Runner.
Uses pure Python standard library (http.server) - Zero external dependencies.
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/dashboard.html"
        return super().do_GET()

def run():
    os.chdir(DIRECTORY)
    server_address = ("", PORT)
    with socketserver.TCPServer(server_address, CustomHandler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print("=" * 70)
        print("  PAYROLL VALIDATOR INTERACTIVE WEB DASHBOARD RUNNING")
        print("=" * 70)
        print(f"[*] Access the Dashboard Link: {url}")
        print("[*] Press Ctrl+C in this terminal to stop the server.")
        print("=" * 70)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run()

