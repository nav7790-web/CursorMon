# TODO — Demo Server Monitoring

Local Flask demo on this machine. Do one checkbox at a time. Bind to localhost only. Do not commit secrets.

## 1. Project initialization and basic UI

- [x] Add a Python project skeleton: `requirements.txt` (Flask), `app/` package, `templates/`, `static/`, and a `run` entry that starts one process on `127.0.0.1`.
  - **Security:** Listen on localhost only. Add `.gitignore` for `.env`, `*.db`, `data/`, SSH keys, and `__pycache__`.
  - **Docs:** `README.md` with venv create, install, and run commands.

- [x] Add a shared layout and simple CSS that stays readable in a laptop browser.
  - **Security:** Static assets only. No inline secrets and no user-supplied HTML.
  - **Docs:** Note the layout files in the README.

- [x] Add three empty pages: login, server list, and dashboard (one card placeholder, empty state “no servers yet”).
  - **Security:** Read-only shells. No buttons that run commands, restart services, or kill processes.
  - **Docs:** List the three pages and empty states in the README.

## 2. Sign-in and unit tests

- [x] Load the admin password from a local env file, store only a hash (Werkzeug or `hashlib`), username fixed as `admin`.
  - **Security:** Never write or log the plain password. Keep `.env` out of git. No self-registration and no password-change page.
  - **Docs:** Document `ADMIN_PASSWORD` (or the hash env) and that the default user is `admin`.

- [x] Sign-in and sign-out with a session that ends on sign-out or when the browser closes. All pages except login require a session.
  - **Security:** `HttpOnly` and `SameSite` session cookie. Generic error on bad login. Redirect unsigned users to login.
  - **Docs:** Document the login and logout flow in the README.

- [x] Unit tests for hash check, successful login, rejected login, logout, and a protected page without a session.
  - **Security:** Tests use a fake password in memory only. Do not print secrets or read a real `.env`.
  - **Docs:** Document `python -m unittest` (or pytest) in the README.

## 3. Server list

- [x] Store servers in a local JSON file or SQLite (display name, host, SSH port default 22, SSH user, password or key path).
  - **Security:** File stays on this host and is gitignored. Do not return SSH secrets in page HTML or logs.
  - **Docs:** Document the data file path and fields in the README.

- [x] Add-server form and remove action. No edit flow.
  - **Security:** Validate name, host, port (1–65535), and username. Reject empty secrets. Removing a server only deletes the local record.
  - **Docs:** Document add and remove in the README.

- [x] Unit tests for add, duplicate handling, invalid port, and remove.
  - **Security:** Tests use a temp file. No real SSH credentials.
  - **Docs:** Add these tests to the test command note in the README.

## 4. Metrics dashboard

- [x] SSH from the Flask process and run only fixed commands (`free`, `mpstat` or `top`, `ss` or `netstat`). Parse CPU percent, used/total memory, bytes in/out per second, and listening port, protocol, and bind address.
  - **Security:** No user-supplied commands. Timeouts on connect and command. Do not log passwords or key material. Do not change anything on the target.
  - **Docs:** Document the command set and that targets must already accept SSH.

- [x] One dashboard card per server: snapshot values, last success time, and a per-card error (unreachable, auth failed, or command failed) so other cards still render.
  - **Security:** Escape all server-provided text. Metrics stay read-only.
  - **Docs:** Document card fields and the three error states in the README.

- [x] Auto-refresh about every 10 seconds and a manual refresh control. Empty state when the list has no servers.
  - **Security:** Refresh only re-reads metrics. No extra actions on the host.
  - **Docs:** Document the interval and manual refresh in the README.

- [x] Unit tests for parsers and for a failed collection that does not drop other servers. Mock SSH; do not open a real connection.
  - **Security:** Fixtures contain sample command output only.
  - **Docs:** Note that metric tests do not need a live server.

## 5. CI

- [x] GitHub Actions workflow that installs dependencies and runs the unit tests on push and pull request.
  - **Security:** No secrets in the workflow. No deploy job. Tests stay offline.
  - **Docs:** Add a CI section to the README (workflow file path and what it runs).

## 6. Local check

- [x] Run the app on localhost, sign in, add a server, confirm the dashboard (or a clear SSH error), remove the server, and sign out.
  - **Security:** Confirm the process is bound to `127.0.0.1` and that `.env` and the server file are untracked.
  - **Docs:** Add a short manual check list to the README.
