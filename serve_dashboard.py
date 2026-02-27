#!/usr/bin/env python3
import http.server
import socketserver
import subprocess
import os

PORT = 8010
WORKSPACE_DIR = "/Users/tengda/Antigravity"
UPDATE_SCRIPT = os.path.join(WORKSPACE_DIR, "update_dashboard.py")

class DashboardUpdateHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/update':
            try:
                print("Update triggered from UI. Running update_dashboard.py...")
                # Run the update script
                result = subprocess.run(
                    ["python3", UPDATE_SCRIPT],
                    cwd=WORKSPACE_DIR,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("Update successful.")
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except subprocess.CalledProcessError as e:
                print(f"Update failed: {e.stderr}")
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "Failed to update dashboard"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    Handler = DashboardUpdateHandler
    print(f"Starting dashboard automation server on port {PORT}...")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Waiting for UI triggers. Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()
