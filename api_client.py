import json
import socket
import threading
import time

import requests

try:
    import socketio
except ImportError:
    socketio = None

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8002
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
TIMEOUT = 5

DISCOVERY_PORT = 8003
DISCOVERY_QUERY = "BSS_DISCOVER"
DISCOVERY_SERVICE = "BSS_LAN_SERVER"

_socket_lock = threading.Lock()
_socket_client = None
_socket_target_url = None
_stats_callbacks = []
_score_callbacks = []
_active_players_callbacks = []


def set_server(ip, port=8002):
    global SERVER_IP, SERVER_PORT, SERVER_URL
    SERVER_IP = ip
    SERVER_PORT = int(port)
    SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"


def _get(path):
    r = requests.get(f"{SERVER_URL}{path}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path, data):
    r = requests.post(f"{SERVER_URL}{path}", json=data, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _notify(callbacks, payload):
    for cb in list(callbacks):
        try:
            cb(payload)
        except Exception:
            pass


def _ensure_socket_client():
    global _socket_client

    if _socket_client is not None:
        return _socket_client

    if socketio is None:
        raise RuntimeError(
            "Socket.IO client is not available. Install python-socketio to use LAN live sync."
        )

    client = socketio.Client(reconnection=True, logger=False, engineio_logger=False)

    @client.on("stats_update")
    def _on_stats_update(payload):
        _notify(_stats_callbacks, payload or {})

    @client.on("score_update")
    def _on_score_update(payload):
        _notify(_score_callbacks, payload or {})

    @client.on("active_players_update")
    def _on_active_players_update(payload):
        _notify(_active_players_callbacks, payload or {})

    _socket_client = client
    return _socket_client


def connect_socket(ip=None, port=8002):
    global _socket_target_url

    if ip:
        set_server(ip, port)

    try:
        health = ping()
        if health.get("socketio_enabled") is False:
            raise RuntimeError(
                "Host is running without Socket.IO. Install python-socketio on the host environment."
            )
    except RuntimeError:
        raise
    except Exception:
        pass

    with _socket_lock:
        client = _ensure_socket_client()
        if client.connected and _socket_target_url != SERVER_URL:
            client.disconnect()
        if client.connected:
            return True
        client.connect(SERVER_URL, transports=["websocket", "polling"], wait_timeout=TIMEOUT)
        _socket_target_url = SERVER_URL
        return True


def disconnect_socket():
    global _socket_target_url

    with _socket_lock:
        if _socket_client and _socket_client.connected:
            _socket_client.disconnect()
        _socket_target_url = None


def clear_socket_handlers():
    _stats_callbacks.clear()
    _score_callbacks.clear()
    _active_players_callbacks.clear()


def on_stats_update(callback):
    if callback not in _stats_callbacks:
        _stats_callbacks.append(callback)


def on_score_update(callback):
    if callback not in _score_callbacks:
        _score_callbacks.append(callback)


def on_active_players_update(callback):
    if callback not in _active_players_callbacks:
        _active_players_callbacks.append(callback)


def _discovery_targets():
    targets = {
        ("255.255.255.255", DISCOVERY_PORT),
        (SERVER_IP, DISCOVERY_PORT),
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
                host_port = SERVER_PORT

                try:
                    message = json.loads(data.decode("utf-8", errors="ignore"))
                    if message.get("service") != DISCOVERY_SERVICE:
                        continue
                    host_ip = message.get("ip") or addr[0]
                    host_port = int(message.get("port") or SERVER_PORT)
                except Exception:
                    continue

                set_server(host_ip, host_port)
                return host_ip

        return None
    finally:
        sock.close()


def ping():
    return _get("/ping")


def get_teams():
    return _get("/teams")


def get_players(tid):
    return _get(f"/teams/{tid}/players")


def get_games():
    return _get("/games")


def get_game(gl):
    return _get(f"/games/{gl}")


def get_next_label():
    try:
        return _get("/games/next-label")["label"]
    except Exception:
        return "GAME-001"


def create_game(gl, hid, aid):
    return _post("/games", {"game_label": gl, "home_team_id": hid, "away_team_id": aid})


def get_stats(gl, tid):
    return _get(f"/stats/{gl}/{tid}")


def update_stat(gl, pid, tid, col, amt):
    return _post(
        "/stats/update",
        {"game_label": gl, "player_id": pid, "team_id": tid, "col": col, "amount": amt},
    )


def get_score(gl):
    return _get(f"/score/{gl}")


def get_active(gl, tid):
    try:
        return _get(f"/active-players/{gl}/{tid}")["player_ids"]
    except Exception:
        return []


def set_active(gl, tid, pids):
    return _post("/active-players", {"game_label": gl, "team_id": tid, "player_ids": pids})


def login(u, p):
    return _post("/auth/login", {"username": u, "password": p})


def signup(u, p):
    return _post("/auth/signup", {"username": u, "password": p})


def create_team(name):
    return _post("/teams", {"team_name": name})


def delete_team(tid):
    r = requests.delete(f"{SERVER_URL}/teams/{tid}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def create_player(tid, first_name, last_name, jersey=None):
    return _post(
        "/players",
        {"team_id": tid, "first_name": first_name, "last_name": last_name, "jersey": jersey},
    )


def delete_player(pid):
    r = requests.delete(f"{SERVER_URL}/players/{pid}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()
