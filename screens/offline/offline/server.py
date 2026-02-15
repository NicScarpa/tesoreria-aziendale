#!/usr/bin/env python3
"""Server HTTP con SPA fallback — serve index.html per tutte le route non-file."""
import http.server
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Se il path corrisponde a un file reale, servilo
        file_path = os.path.join(DIRECTORY, self.path.lstrip('/'))
        if os.path.isfile(file_path):
            return super().do_GET()

        # Altrimenti, serve index.html (SPA routing)
        self.path = '/index.html'
        return super().do_GET()


if __name__ == '__main__':
    with http.server.HTTPServer(('', PORT), SPAHandler) as httpd:
        print(f'Sibill Offline — http://localhost:{PORT}')
        print('Premi Ctrl+C per fermare')
        httpd.serve_forever()
