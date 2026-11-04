# Server Monitor

Local demo that shows Linux server health in a browser on this machine. It listens on `127.0.0.1` only.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `ADMIN_PASSWORD` to a password for this machine. The app hashes it at startup and does not write the plain password. You can set `ADMIN_PASSWORD_HASH` instead of `ADMIN_PASSWORD`. The only username is `admin`.

Optional: set `SECRET_KEY` in `.env` so sessions stay valid across restarts. Leave it unset and a new key is used each start.

```bash
python run.py
```

Open http://127.0.0.1:5000/

## Sign in

1. Open `/login`.
2. Sign in as `admin` with the password from `.env`.
3. A failed attempt shows "Invalid username or password."
4. Sign out from the header. The session cookie is `HttpOnly` and `SameSite=Lax`, and it ends when the browser closes.

Every page except the login screen requires that session. There is no registration page and no password-change page.

## Layout

- `templates/base.html` — shared page chrome (header and nav)
- `static/style.css` — the only stylesheet
- `templates/login.html` — sign-in
- `templates/servers.html` — server list, add form, and remove
- `templates/dashboard.html` — one card per server, plus a reload script

Jinja escapes server-provided text. Pages do not include SSH passwords or key paths.

## Servers

Inventory is stored in `data/servers.json` on this machine (mode `0600`). That directory is gitignored.

| Field | Notes |
| --- | --- |
| Display name | Label in the UI |
| Hostname or IP | SSH target |
| SSH port | 1–65535, default 22 |
| SSH username | Account used for the snapshot |
| Authentication | `password` or `key` |
| Secret | Password or private key path. Stored in the JSON file only. |

Adding the same host and port again is rejected. Remove deletes that local record and nothing on the target.

## Metrics

The app opens SSH from this process and runs one fixed read-only script:

- `free -b` — used and total memory
- `top -bn1` — overall CPU percent
- `ss -lntuH` (or `netstat -lntu`) — listening port, protocol, and bind address
- two reads of `/proc/net/dev`, one second apart — bytes in and out per second

The target must already accept SSH. Connect and command timeouts are 5 and 8 seconds. A card shows one of three errors and the other cards still render: **unreachable**, **auth failed**, or **command failed**.

The dashboard reloads about every 10 seconds. **Refresh** loads the same page again. Nothing on the dashboard restarts a service, stops a process, or runs a command you type.

## Tests

Tests use a password in memory and a temporary inventory file. Metric tests use sample command output and do not need a live server.

```bash
python -m unittest discover -s tests
```

## CI

`.github/workflows/test.yml` installs dependencies and runs the unit tests on push and pull request. It does not deploy and it does not use secrets.

## Manual check

1. Start `python run.py` and confirm it is bound to `127.0.0.1`.
2. Sign in as `admin`.
3. Add a server.
4. Open the dashboard and confirm metrics, or a clear SSH error on that card.
5. Remove the server.
6. Sign out.
7. Confirm `.env` and `data/servers.json` are untracked (`git status`).
