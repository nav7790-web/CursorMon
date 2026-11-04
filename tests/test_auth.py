"""Sign-in tests. The password exists only in memory."""

import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.auth import hash_password, verify_password

PASSWORD = "test-password"


def build_app(directory):
    return create_app(
        password=PASSWORD,
        server_path=Path(directory) / "servers.json",
        load_env=False,
        runner=lambda _server: (_ for _ in ()).throw(AssertionError("ssh should not run")),
    )


class HashTests(unittest.TestCase):
    def test_hash_round_trip(self):
        stored = hash_password(PASSWORD)
        self.assertNotIn(PASSWORD, stored)
        self.assertTrue(verify_password(PASSWORD, stored))
        self.assertFalse(verify_password("wrong", stored))
        self.assertFalse(verify_password("", stored))


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = build_app(self.tmp.name)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_protected_page_redirects_when_signed_out(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/login"))

    def test_rejected_login(self):
        response = self.client.post("/login", data={"username": "admin", "password": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password.", response.data)
        self.assertNotIn(b"nope", response.data)
        follow = self.client.get("/servers")
        self.assertEqual(follow.status_code, 302)

    def test_successful_login_logout_and_cookie_flags(self):
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 302)
        cookie = response.headers["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertNotIn("Max-Age", cookie)
        page = self.client.get("/dashboard")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"No servers yet.", page.data)

        signed_out = self.client.post("/logout")
        self.assertEqual(signed_out.status_code, 302)
        blocked = self.client.get("/servers")
        self.assertEqual(blocked.status_code, 302)
        self.assertTrue(blocked.headers["Location"].endswith("/login"))
