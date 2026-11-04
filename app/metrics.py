"""Parse a fixed read-only snapshot. Nothing here opens a connection."""

import re

# One remote script. Host, user, and secrets are never interpolated into it.
SNAPSHOT_COMMAND = """free -b
echo '---SPLIT---'
top -bn1 | head -n 5
echo '---SPLIT---'
ss -lntuH || netstat -lntu
echo '---SPLIT---'
awk 'NR>2 && $1 !~ /lo:/ {rx+=$2; tx+=$10} END {printf "%d %d\\n", rx+0, tx+0}' /proc/net/dev
sleep 1
awk 'NR>2 && $1 !~ /lo:/ {rx+=$2; tx+=$10} END {printf "%d %d\\n", rx+0, tx+0}' /proc/net/dev
"""

_SS_LOCAL = re.compile(
    r"^(tcp|udp)\s+\S+\s+\d+\s+\d+\s+(\S+)\s+",
    re.IGNORECASE | re.MULTILINE,
)
_NETSTAT_LOCAL = re.compile(
    r"^(tcp|udp)\s+\d+\s+\d+\s+(\S+)\s+\S+\s+(LISTEN|UNCONN)",
    re.IGNORECASE | re.MULTILINE,
)
_CPU_IDLE = re.compile(r"([\d.]+)\s+id")


class Unreachable(Exception):
    """SSH could not reach the host."""


class AuthFailed(Exception):
    """SSH rejected the configured credentials."""


def format_bytes(size):
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def _split_addr(local):
    if local.startswith("["):
        host, _, port = local[1:].rpartition("]:")
        return host, port
    host, _, port = local.rpartition(":")
    return host, port


def _parse_memory(text):
    for line in text.splitlines():
        if line.startswith("Mem:"):
            cols = line.split()
            return int(cols[2]), int(cols[1])
    raise ValueError("memory")


def _parse_cpu(text):
    match = _CPU_IDLE.search(text)
    if not match:
        raise ValueError("cpu")
    idle = float(match.group(1))
    usage = min(100.0, max(0.0, 100.0 - idle))
    return round(usage, 1)


def _parse_ports(text):
    found = _SS_LOCAL.findall(text) or _NETSTAT_LOCAL.findall(text)
    ports = []
    for proto, local, *_rest in found:
        address, port = _split_addr(local)
        if not port.isdigit():
            continue
        ports.append({
            "protocol": proto.lower(),
            "port": port,
            "address": address,
        })
    return ports


def _parse_network(text):
    samples = []
    for line in text.splitlines():
        bits = line.split()
        if len(bits) == 2 and bits[0].isdigit() and bits[1].isdigit():
            samples.append((int(bits[0]), int(bits[1])))
    if len(samples) < 2:
        raise ValueError("network")
    first, second = samples[0], samples[1]
    return max(0, second[0] - first[0]), max(0, second[1] - first[1])


def parse_snapshot(text):
    parts = text.split("---SPLIT---")
    if len(parts) != 4:
        raise ValueError("snapshot")
    used, total = _parse_memory(parts[0])
    cpu = _parse_cpu(parts[1])
    ports = _parse_ports(parts[2])
    net_in, net_out = _parse_network(parts[3])
    return {
        "cpu": cpu,
        "memory_used": used,
        "memory_total": total,
        "net_in": net_in,
        "net_out": net_out,
        "ports": ports,
    }


def _failed(server, kind):
    return {
        "name": server.get("name") or server.get("host") or "Server",
        "host": server.get("host", ""),
        "port": server.get("port", ""),
        "ok": False,
        "error": kind,
        "cpu": None,
        "memory": None,
        "net_in": None,
        "net_out": None,
        "ports": [],
        "last_success": server.get("last_success"),
    }


def collect_one(server, runner):
    try:
        code, output, _err = runner(server)
    except AuthFailed:
        return _failed(server, "auth failed")
    except Unreachable:
        return _failed(server, "unreachable")
    except Exception:
        return _failed(server, "unreachable")
    if code != 0:
        return _failed(server, "command failed")
    try:
        parsed = parse_snapshot(output)
    except (ValueError, IndexError, TypeError):
        return _failed(server, "command failed")
    return {
        "name": server.get("name") or server.get("host") or "Server",
        "host": server.get("host", ""),
        "port": server.get("port", ""),
        "ok": True,
        "error": None,
        "cpu": parsed["cpu"],
        "memory": f"{format_bytes(parsed['memory_used'])} / {format_bytes(parsed['memory_total'])}",
        "net_in": f"{format_bytes(parsed['net_in'])}/s",
        "net_out": f"{format_bytes(parsed['net_out'])}/s",
        "ports": parsed["ports"],
        "last_success": None,
    }


def collect_all(servers, runner):
    return [collect_one(server, runner) for server in servers]
