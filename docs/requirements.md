# Demo Server Monitoring — Requirements

## Overview

A small local web app for internal teams to view live Linux server health without signing in to each machine. The app runs on the same machine as Cursor and is for demonstration only.

## Problem

Operators currently open a shell on each server to check memory, CPU, network usage, and listening ports. That is slow when several teams need the same snapshot.

## Users

Internal L1, L2, and L3 staff in infrastructure and application development. Everyone sees the same read-only metrics. One shared admin account manages the server list.

## Goals

- Show current CPU, memory, network, and listening-port data for registered Linux servers.
- Keep the monitoring views read-only.
- Let the admin add and remove servers from the UI.
- Run locally with a short setup.

## Tech stack

- Python
- Flask for the web UI and server-side collection
- HTML, CSS, and a small amount of client script for a clear, readable layout
- Password stored only as a hash (Werkzeug or the stdlib `hashlib` is enough)
- Server list stored in a local file (SQLite or JSON)

## Authentication

- Sign-in is required before any page other than the login screen.
- Default username is `admin`.
- The password is set in a local env or config file and saved only as a hash. The app never stores or displays the plain password.
- One shared account. No self-registration, roles, or password-change page.
- Session ends on sign-out or browser close.

## Server inventory

The signed-in admin can add and remove Linux servers. Editing an existing server is not required for the demo.

Each server record includes:

| Field | Notes |
| --- | --- |
| Display name | Label shown in the UI |
| Hostname or IP | Target the app SSHs to |
| SSH port | Default 22 |
| SSH username | Account used for metric commands |
| SSH auth | Password or private key path, kept only on the app host |

Removing a server drops it from the list and from the dashboard. Metric screens do not change anything on the target host.

## Metrics

The app opens an SSH session from the Flask process and reads a current snapshot with standard Linux commands (`free`, `mpstat` or `top`, and `ss` or `netstat`). No agent is installed on the target.

For each server the UI shows:

- **CPU** — overall usage percent
- **Memory** — used and total
- **Network** — current throughput (bytes in and out per second)
- **Listening ports** — port, protocol, and bind address

Values are a point-in-time snapshot. The page refreshes on a fixed interval (about every 10 seconds) and offers a manual refresh. No history, charts, or alerts.

If SSH fails, that server card shows the error (unreachable, auth failed, or command failed) and the rest of the dashboard still loads.

## UI

- Login page, server list with add/remove, and a dashboard of one card per server.
- Monitoring data is read-only: no controls that restart services, kill processes, or run arbitrary commands.
- Layout stays usable on a laptop browser: clear labels, status of the last successful collection, and obvious empty states (no servers yet, server unreachable).

## Local demo constraints

- Single Flask process bound to localhost.
- No external database, queue, or identity provider.
- Target servers must already accept SSH from the app host; this demo does not provision accounts or firewall rules.
- Secrets (admin password hash, SSH secrets) stay in local files that are not committed.

## Out of scope

- Windows or other operating systems
- Historical graphs, retention, or export
- Alerting, tickets, or paging
- Multiple users, SSO, or fine-grained permissions
- Changing server configuration or running commands from the UI
- High availability, TLS termination, and multi-host deployment
