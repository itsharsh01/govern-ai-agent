from __future__ import annotations

import socket
import subprocess
import sys


def _pid_listening_on_port(port: int) -> int | None:
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    needle = f":{port}"
    for line in result.stdout.splitlines():
        if "LISTENING" not in line or needle not in line:
            continue
        parts = line.split()
        if parts and parts[-1].isdigit():
            return int(parts[-1])
    return None


def assert_port_available(host: str, port: int) -> None:
    """Fail fast with a helpful message if the API port is already taken."""
    probe_host = host if host not in ("0.0.0.0", "::") else "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((probe_host, port))
    except OSError as exc:
        winerr = getattr(exc, "winerror", None)
        if exc.errno not in (98, 48) and winerr != 10048:
            raise
        pid = _pid_listening_on_port(port)
        pid_hint = f" (PID {pid})" if pid else ""
        kill_hint = f"\n  taskkill /PID {pid} /F" if pid else ""
        print(
            f"Cannot start API: port {port} on {host} is already in use{pid_hint}.\n"
            f"Stop the existing server{kill_hint}\n"
            f"  or set another port in .env, e.g. API_PORT=8801",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    finally:
        sock.close()
