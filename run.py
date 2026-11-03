"""Start the demo app on localhost only."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # One process, this machine only. Do not bind 0.0.0.0.
    app.run(host="127.0.0.1", port=5000, debug=False)
