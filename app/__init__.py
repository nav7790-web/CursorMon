"""Local demo server monitor. One process, loopback only."""

import os
import re
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

from app.auth import hash_password, password_matches
from app.metrics import collect_all
from app.ssh import ssh_runner
from app.store import ServerStore

ROOT = Path(__file__).resolve().parent.parent
ID_RE = re.compile(r"^[a-f0-9]{32}$")


def load_env_file(path):
    """Load KEY=value pairs that are not already set. Never log values."""
    file_path = Path(path)
    if not file_path.is_file():
        return
    for line in file_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _password_hash(password, password_hash):
    if password_hash:
        return password_hash
    if password is not None:
        return hash_password(password)
    env_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    if env_hash:
        return env_hash
    env_password = os.environ.get("ADMIN_PASSWORD")
    if not env_password:
        raise RuntimeError("Set ADMIN_PASSWORD or ADMIN_PASSWORD_HASH in the environment or .env")
    return hash_password(env_password)


def create_app(password=None, password_hash=None, server_path=None, runner=None, load_env=True):
    if load_env:
        load_env_file(ROOT / ".env")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    if not load_env:
        app.secret_key = "test-session-key"
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        SESSION_PERMANENT=False,
    )
    store = ServerStore(server_path or (ROOT / "data" / "servers.json"))
    collect = runner or ssh_runner
    stored_hash = _password_hash(password, password_hash)

    @app.context_processor
    def inject_user():
        return {"signed_in": session.get("user") == "admin"}

    @app.before_request
    def require_login():
        if request.endpoint in ("login", "static"):
            return None
        if session.get("user") != "admin":
            return redirect(url_for("login"))
        return None

    @app.get("/")
    def home():
        return redirect(url_for("dashboard"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user") == "admin":
            return redirect(url_for("dashboard"))
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            submitted = request.form.get("password", "")
            if password_matches(username, submitted, stored_hash):
                session.clear()
                session.permanent = False
                session["user"] = "admin"
                return redirect(url_for("dashboard"))
            error = "Invalid username or password."
        return render_template("login.html", page="login", error=error)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/servers", methods=["GET", "POST"])
    def servers():
        if request.method == "POST":
            message = store.add(request.form)
            if message:
                flash(message)
            return redirect(url_for("servers"))
        return render_template("servers.html", page="servers", servers=store.list_public())

    @app.post("/servers/<server_id>/remove")
    def remove_server(server_id):
        if not ID_RE.fullmatch(server_id):
            return redirect(url_for("servers"))
        store.remove(server_id)
        return redirect(url_for("servers"))

    @app.get("/dashboard")
    def dashboard():
        records = store.list_all()
        cards = collect_all(records, collect)
        collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for record, card in zip(records, cards):
            if card["ok"]:
                store.mark_success(record["id"], collected_at)
                card["last_success"] = collected_at
        return render_template("dashboard.html", page="dashboard", cards=cards)

    return app
