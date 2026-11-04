import json
import secrets
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from app import handler, VERSION


class APIContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.token = secrets.token_urlsafe(32)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler(cls.token))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_health_without_credentials(self):
        with urllib.request.urlopen(self.base + '/health') as r:
            self.assertEqual(json.load(r), {'status': 'ok'})

    def test_missing_and_wrong_credentials_are_rejected(self):
        for auth in (None, 'Bearer wrong'):
            with self.subTest(auth=auth):
                headers = {'Authorization': auth} if auth else {}
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(urllib.request.Request(self.base + '/version', headers=headers))
                self.assertEqual(caught.exception.code, 401)
                caught.exception.close()

    def test_authenticated_version(self):
        request = urllib.request.Request(self.base + '/version', headers={'Authorization': f'Bearer {self.token}'})
        with urllib.request.urlopen(request) as r:
            self.assertEqual(json.load(r)['version'], VERSION)


if __name__ == '__main__':
    unittest.main()
