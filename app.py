"""Small authenticated API used only to verify the deployment platform."""
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

VERSION = '1.0.1'


def handler(token):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'PlatformCheck'
        sys_version = ''

        def reply(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/health':
                return self.reply(200, {'status': 'ok'})
            if not hmac.compare_digest(self.headers.get('Authorization', ''), f'Bearer {token}'):
                return self.reply(401, {'error': 'unauthorized'})
            if path in ('/', '/version'):
                return self.reply(200, {'service': 'platform-check', 'version': VERSION})
            return self.reply(404, {'error': 'not_found'})

        def log_request(self, code='-', size='-'):
            print(json.dumps({'method': self.command, 'path': urlsplit(self.path).path,
                              'status': code}), flush=True)

        def log_message(self, *_):
            pass
    return Handler


if __name__ == '__main__':
    token = os.environ.get('API_TOKEN', '')
    if len(token) < 32:
        raise SystemExit('Set API_TOKEN to at least 32 characters before starting.')
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), handler(token)).serve_forever()
