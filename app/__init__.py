"""Local demo server monitor. Pages are read-only shells until later steps."""

from flask import Flask, render_template


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    @app.get("/")
    def home():
        return render_template("login.html", page="login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        # Shell only. Do not read the form body; sign-in comes in a later step.
        return render_template("login.html", page="login")

    @app.get("/servers")
    def servers():
        return render_template("servers.html", page="servers")

    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html", page="dashboard")

    return app
