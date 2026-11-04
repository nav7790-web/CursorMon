"""Local server inventory. SSH secrets stay in the data file and off the page."""

import json
import os
import re
import uuid
from pathlib import Path

HOST_RE = re.compile(r"^[A-Za-z0-9._:-]{1,253}$")
USER_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
NAME_MAX = 80


def _clean(value):
    return "" if value is None else str(value).strip()


def validate_server(fields):
    name = _clean(fields.get("name"))
    host = _clean(fields.get("host"))
    username = _clean(fields.get("username"))
    auth = _clean(fields.get("auth")) or "password"
    secret = _clean(fields.get("secret"))
    port_raw = _clean(fields.get("port")) or "22"

    if not name or len(name) > NAME_MAX or any(ch in name for ch in "\r\n\t"):
        return None, "Enter a display name."
    if not HOST_RE.fullmatch(host):
        return None, "Enter a hostname or IP address."
    if not port_raw.isdigit():
        return None, "Port must be between 1 and 65535."
    port = int(port_raw)
    if port < 1 or port > 65535:
        return None, "Port must be between 1 and 65535."
    if not USER_RE.fullmatch(username):
        return None, "Enter an SSH username."
    if auth not in ("password", "key"):
        return None, "Choose password or private key authentication."
    if not secret or any(ch in secret for ch in "\r\n"):
        return None, "Enter a password or private key path."

    return {
        "name": name,
        "host": host,
        "port": port,
        "username": username,
        "auth": auth,
        "secret": secret,
    }, None


def public_server(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "host": row["host"],
        "port": row["port"],
        "username": row["username"],
        "auth": row["auth"],
        "last_success": row.get("last_success"),
    }


class ServerStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self):
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("server file must be a list")
        return data

    def _write(self, rows):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(rows, indent=2)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(payload, encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(self.path)
        os.chmod(self.path, 0o600)

    def list_public(self):
        return [public_server(row) for row in self._read()]

    def list_all(self):
        return self._read()

    def add(self, fields):
        record, error = validate_server(fields)
        if error:
            return error
        rows = self._read()
        for row in rows:
            if row["host"].lower() == record["host"].lower() and int(row["port"]) == record["port"]:
                return "A server with that host and port is already listed."
        record["id"] = uuid.uuid4().hex
        record["last_success"] = None
        rows.append(record)
        self._write(rows)
        return None

    def remove(self, server_id):
        rows = [row for row in self._read() if row.get("id") != server_id]
        self._write(rows)

    def mark_success(self, server_id, when):
        rows = self._read()
        for row in rows:
            if row.get("id") == server_id:
                row["last_success"] = when
        self._write(rows)
