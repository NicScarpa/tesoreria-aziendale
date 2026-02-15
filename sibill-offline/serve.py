#!/usr/bin/env python3
"""Local server for Sibill Offline Replay."""
import http.server
import os
import socket
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class DualStackHTTPServer(http.server.HTTPServer):
    """HTTPServer that binds to both IPv4 and IPv6 (dual-stack)."""
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


class SibillHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Serve index.html for SPA routes
        path = self.path.split("?")[0]
        full_path = os.path.join(DIRECTORY, path.lstrip("/"))

        if not os.path.exists(full_path) and not path.startswith("/api-responses/") and not path.startswith("/assets/"):
            # SPA fallback: serve app-shell.html for app routes, index.html for root
            shell = os.path.join(DIRECTORY, "app-shell.html")
            if os.path.exists(shell) and path != "/":
                self.path = "/app-shell.html"
            else:
                self.path = "/index.html"

        return super().do_GET()

    def end_headers(self):
        # Add CORS and Service Worker headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        if self.path == "/sw.js":
            self.send_header("Service-Worker-Allowed", "/")
        super().end_headers()

    def log_message(self, format, *args):
        # Color-code log output
        path = args[0].split(" ")[1] if args else ""
        if "/api-responses/" in path:
            print(f"\033[32m{format % args}\033[0m")
        elif "/assets/" in path:
            print(f"\033[36m{format % args}\033[0m")
        else:
            print(format % args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    try:
        httpd = DualStackHTTPServer(("::", port), SibillHandler)
    except OSError:
        # Fallback to IPv4 only if dual-stack not supported
        httpd = http.server.HTTPServer(("", port), SibillHandler)
    with httpd:
        print(f"\n  Sibill Offline Server")
        print(f"  http://localhost:{port}")
        print(f"  Directory: {DIRECTORY}")
        print(f"  Ctrl+C per fermare\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer fermato.")
