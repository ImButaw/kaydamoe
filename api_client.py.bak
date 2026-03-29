import requests

SERVER_URL = "http://127.0.0.1:8002"
TIMEOUT = 5


def set_server(ip, port=8002):
    global SERVER_URL
    SERVER_URL = f"http://{ip}:{port}"


def _get(path):
    r = requests.get(f"{SERVER_URL}{path}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path, data):
    r = requests.post(f"{SERVER_URL}{path}", json=data, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def ping():                    return _get("/ping")
def get_teams():               return _get("/teams")
def get_players(tid):          return _get(f"/teams/{tid}/players")
def get_games():               return _get("/games")
def get_game(gl):              return _get(f"/games/{gl}")
def get_next_label():
    try: return _get("/games/next-label")["label"]
    except: return "GAME-001"
def create_game(gl, hid, aid): return _post("/games", {"game_label": gl, "home_team_id": hid, "away_team_id": aid})
def get_stats(gl, tid):        return _get(f"/stats/{gl}/{tid}")
def update_stat(gl, pid, tid, col, amt):
    return _post("/stats/update", {"game_label": gl, "player_id": pid, "team_id": tid, "col": col, "amount": amt})
def get_score(gl):             return _get(f"/score/{gl}")
def get_active(gl, tid):
    try: return _get(f"/active-players/{gl}/{tid}")["player_ids"]
    except: return []
def set_active(gl, tid, pids): return _post("/active-players", {"game_label": gl, "team_id": tid, "player_ids": pids})
def login(u, p):               return _post("/auth/login", {"username": u, "password": p})
def signup(u, p):              return _post("/auth/signup", {"username": u, "password": p})
def create_team(name):         return _post("/teams", {"team_name": name})
def delete_team(tid):
    r = requests.delete(f"{SERVER_URL}/teams/{tid}", timeout=TIMEOUT)
    r.raise_for_status(); return r.json()
def create_player(tid, fn, ln, jersey=None):
    return _post("/players", {"team_id": tid, "first_name": fn, "last_name": ln, "jersey": jersey})
def delete_player(pid):
    r = requests.delete(f"{SERVER_URL}/players/{pid}", timeout=TIMEOUT)
    r.raise_for_status(); return r.json()
