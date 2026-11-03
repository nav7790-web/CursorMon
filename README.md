# Server Monitor

Local demo that shows Linux server health in a browser on this machine. It listens on `127.0.0.1` only.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000/

## Layout

- `templates/base.html` — shared page chrome (header and nav)
- `static/style.css` — the only stylesheet
- `templates/login.html` — sign-in shell
- `templates/servers.html` — server list
- `templates/dashboard.html` — dashboard

Styles and pages are static files. The app does not inject secrets or user-supplied HTML.

## Pages

| Page | Path | What you see |
| --- | --- | --- |
| Login | `/login` | Username `admin` and a disabled password field. Sign-in is not active yet. |
| Servers | `/servers` | Empty state: **No servers yet.** |
| Dashboard | `/dashboard` | Empty state: **No servers yet.** One placeholder card with blank CPU, memory, network, and port fields. |

There are no controls that restart services, stop processes, or run commands.
