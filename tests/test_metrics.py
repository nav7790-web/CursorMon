"""Parser and collector tests. No SSH connection is opened."""

import unittest

from app.metrics import SNAPSHOT_COMMAND, AuthFailed, Unreachable, collect_all, parse_snapshot

FIXTURE = """
               total        used        free      shared  buff/cache   available
Mem:     8000000000  2000000000  4000000000     10000  2000000000  5000000000
Swap:              0           0           0
---SPLIT---
top - 12:00:00 up 1 day,  1 user,  load average: 0.10, 0.20, 0.30
%Cpu(s): 10.0 us,  5.0 sy,  0.0 ni, 80.0 id,  5.0 wa,  0.0 hi,  0.0 si,  0.0 st
---SPLIT---
tcp   LISTEN 0      128          0.0.0.0:22        0.0.0.0:*
tcp   LISTEN 0      128             [::]:22           [::]:*
udp   UNCONN 0      0            0.0.0.0:68        0.0.0.0:*
---SPLIT---
1000 2000
1500 2600
"""


class ParserTests(unittest.TestCase):
    def test_command_is_fixed(self):
        self.assertIn("free -b", SNAPSHOT_COMMAND)
        self.assertIn("top -bn1", SNAPSHOT_COMMAND)
        self.assertIn("ss -lntuH", SNAPSHOT_COMMAND)
        self.assertNotIn("{host}", SNAPSHOT_COMMAND)
        self.assertNotIn("{username}", SNAPSHOT_COMMAND)

    def test_parse_snapshot(self):
        parsed = parse_snapshot(FIXTURE)
        self.assertEqual(parsed["cpu"], 20.0)
        self.assertEqual(parsed["memory_used"], 2000000000)
        self.assertEqual(parsed["memory_total"], 8000000000)
        self.assertEqual(parsed["net_in"], 500)
        self.assertEqual(parsed["net_out"], 600)
        self.assertEqual(parsed["ports"][0]["port"], "22")
        self.assertEqual(parsed["ports"][0]["protocol"], "tcp")
        self.assertEqual(parsed["ports"][0]["address"], "0.0.0.0")
        self.assertEqual(len(parsed["ports"]), 3)


class CollectorTests(unittest.TestCase):
    def test_one_failure_keeps_the_other_server(self):
        servers = [
            {"id": "a", "name": "Down", "host": "down.example", "port": 22, "secret": "hidden-down"},
            {"id": "b", "name": "Up", "host": "up.example", "port": 22, "secret": "hidden-up"},
        ]

        def runner(server):
            if server["host"] == "down.example":
                raise Unreachable()
            return 0, FIXTURE, ""

        cards = collect_all(servers, runner)
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0]["error"], "unreachable")
        self.assertFalse(cards[0]["ok"])
        self.assertTrue(cards[1]["ok"])
        self.assertEqual(cards[1]["cpu"], 20.0)
        self.assertEqual(cards[1]["name"], "Up")
        self.assertNotIn("secret", cards[0])
        self.assertNotIn("secret", cards[1])

    def test_auth_and_command_failures(self):
        def runner(server):
            if server["host"] == "bad-auth":
                raise AuthFailed()
            return 1, "", "failed"

        cards = collect_all(
            [
                {"name": "Auth", "host": "bad-auth", "port": 22},
                {"name": "Cmd", "host": "bad-cmd", "port": 22},
            ],
            runner,
        )
        self.assertEqual([card["error"] for card in cards], ["auth failed", "command failed"])
