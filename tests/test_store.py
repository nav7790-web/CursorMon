"""Server inventory tests. Credentials stay in a temp file."""

import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.store import ServerStore

SECRET = "not-a-real-ssh-secret"


def sample(**overrides):
    fields = {
        "name": "Web",
        "host": "10.0.0.8",
        "port": "22",
        "username": "monitor",
        "auth": "password",
        "secret": SECRET,
    }
    fields.update(overrides)
    return fields


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "servers.json"
        self.store = ServerStore(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_and_remove(self):
        self.assertIsNone(self.store.add(sample()))
        public = self.store.list_public()
        self.assertEqual(len(public), 1)
        self.assertNotIn("secret", public[0])
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved[0]["secret"], SECRET)
        self.store.remove(public[0]["id"])
        self.assertEqual(self.store.list_public(), [])

    def test_duplicate_host_and_port(self):
        self.assertIsNone(self.store.add(sample()))
        error = self.store.add(sample(name="Other"))
        self.assertIn("already listed", error)
        self.assertEqual(len(self.store.list_public()), 1)

    def test_invalid_port(self):
        for port in ("0", "65536", "ssh"):
            error = self.store.add(sample(port=port))
            self.assertEqual(error, "Port must be between 1 and 65535.")
        self.assertEqual(self.store.list_public(), [])

    def test_empty_secret_is_rejected(self):
        error = self.store.add(sample(secret="  "))
        self.assertEqual(error, "Enter a password or private key path.")
        self.assertEqual(self.store.list_public(), [])


class ServerPageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "servers.json"
        self.app = create_app(
            password="test-password",
            server_path=self.path,
            load_env=False,
            runner=lambda _server: (_ for _ in ()).throw(AssertionError("ssh should not run")),
        )
        self.client = self.app.test_client()
        self.client.post("/login", data={"username": "admin", "password": "test-password"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_page_does_not_show_secret(self):
        response = self.client.post(
            "/servers",
            data=sample(),
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Web", response.data)
        self.assertNotIn(SECRET.encode(), response.data)
