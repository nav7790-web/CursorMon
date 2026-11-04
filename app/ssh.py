"""Open one SSH session and run the fixed snapshot command."""

import socket

from app.metrics import SNAPSHOT_COMMAND, AuthFailed, Unreachable

CONNECT_TIMEOUT = 5
COMMAND_TIMEOUT = 8


def ssh_runner(server):
    import paramiko

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    # Demo only: accept the host key on first connect. The command stays fixed.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect = {
        "hostname": server["host"],
        "port": int(server["port"]),
        "username": server["username"],
        "timeout": CONNECT_TIMEOUT,
        "banner_timeout": CONNECT_TIMEOUT,
        "auth_timeout": CONNECT_TIMEOUT,
        "look_for_keys": False,
        "allow_agent": False,
    }
    if server.get("auth") == "key":
        connect["key_filename"] = server["secret"]
    else:
        connect["password"] = server["secret"]
    try:
        client.connect(**connect)
        _stdin, stdout, stderr = client.exec_command(SNAPSHOT_COMMAND, timeout=COMMAND_TIMEOUT)
        output = stdout.read(200_000).decode("utf-8", "replace")
        error = stderr.read(20_000).decode("utf-8", "replace")
        code = stdout.channel.recv_exit_status()
        return code, output, error
    except paramiko.AuthenticationException as exc:
        raise AuthFailed from exc
    except FileNotFoundError as exc:
        raise AuthFailed from exc
    except (socket.timeout, TimeoutError, OSError, paramiko.SSHException) as exc:
        raise Unreachable from exc
    finally:
        client.close()
