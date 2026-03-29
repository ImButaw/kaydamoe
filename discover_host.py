import json
import socket
import time

DISCOVERY_PORT = 8003
DISCOVERY_QUERY = "BSS_DISCOVER"
DISCOVERY_SERVICE = "BSS_LAN_SERVER"


def _discovery_targets():
    targets = {
        ("255.255.255.255", DISCOVERY_PORT),
        ("127.0.0.1", DISCOVERY_PORT),
    }

    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        local_ip = probe.getsockname()[0]
        parts = local_ip.split(".")
        if len(parts) == 4:
            parts[-1] = "255"
            targets.add((".".join(parts), DISCOVERY_PORT))
    except Exception:
        pass
    finally:
        probe.close()

    return list(targets)


def discover_host(timeout=1.0, attempts=3):
    payload = DISCOVERY_QUERY.encode("utf-8")
    targets = _discovery_targets()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)

        for _ in range(max(1, attempts)):
            for target in targets:
                try:
                    sock.sendto(payload, target)
                except Exception:
                    pass
            deadline = time.time() + timeout

            while time.time() < deadline:
                try:
                    data, addr = sock.recvfrom(1024)
                except socket.timeout:
                    break

                host_ip = None
                host_port = 8002

                try:
                    message = json.loads(data.decode("utf-8", errors="ignore"))
                    if message.get("service") != DISCOVERY_SERVICE:
                        continue
                    host_ip = message.get("ip") or addr[0]
                    host_port = int(message.get("port") or host_port)
                except Exception:
                    continue

                return host_ip

        return None
    finally:
        sock.close()
