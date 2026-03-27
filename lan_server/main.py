import hashlib
import json
import os
import socket
import sqlite3
import threading

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    import socketio
except ImportError:
    socketio = None

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "BSS.db")
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8002
DISCOVERY_PORT = 8003
DISCOVERY_QUERY = "BSS_DISCOVER"
DISCOVERY_SERVICE = "BSS_LAN_SERVER"

http_app = FastAPI()
http_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if socketio is not None:
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
    app = socketio.ASGIApp(sio, other_asgi_app=http_app)
else:
    sio = None
    app = http_app

_discovery_stop = threading.Event()
_discovery_thread = None
_discovery_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(os.path.abspath(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


class GameCreate(BaseModel):
    game_label: str
    home_team_id: int
    away_team_id: int


class StatDelta(BaseModel):
    game_label: str
    player_id: int
    team_id: int
    col: str
    amount: int


class ActivePlayers(BaseModel):
    game_label: str
    team_id: int
    player_ids: list[int]


class TeamCreate(BaseModel):
    team_name: str


class PlayerCreate(BaseModel):
    team_id: int
    first_name: str
    last_name: str
    jersey: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _resolve_server_ip(client_ip: str = "8.8.8.8") -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect((client_ip, 1))
        return probe.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        probe.close()


def _discovery_worker():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind((SERVER_HOST, DISCOVERY_PORT))
        sock.settimeout(1.0)

        while not _discovery_stop.is_set():
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            if not data:
                continue

            msg = data.decode("utf-8", errors="ignore").strip().upper()
            if msg != DISCOVERY_QUERY:
                continue

            payload = {
                "service": DISCOVERY_SERVICE,
                "ip": _resolve_server_ip(addr[0]),
                "port": SERVER_PORT,
            }
            sock.sendto(json.dumps(payload).encode("utf-8"), addr)
    finally:
        sock.close()


def _start_discovery_thread():
    global _discovery_thread
    with _discovery_lock:
        if _discovery_thread and _discovery_thread.is_alive():
            return
        _discovery_stop.clear()
        _discovery_thread = threading.Thread(target=_discovery_worker, daemon=True)
        _discovery_thread.start()


def _stop_discovery_thread():
    _discovery_stop.set()


def _compute_score(conn: sqlite3.Connection, game_label: str):
    game = conn.execute(
        "SELECT HomeTeamID, AwayTeamID FROM GAMES WHERE GameLabel=?",
        (game_label,),
    ).fetchone()
    if not game:
        return None

    def pts(team_id: int) -> int:
        row = conn.execute(
            "SELECT COALESCE(SUM(TwoPM*2+ThreePM*3+FTM),0) as p FROM PLAYER_STATS WHERE GameLabel=? AND TeamID=?",
            (game_label, team_id),
        ).fetchone()
        return row["p"] if row else 0

    return {
        "game_label": game_label,
        "home_team_id": game["HomeTeamID"],
        "away_team_id": game["AwayTeamID"],
        "home_score": pts(game["HomeTeamID"]),
        "away_score": pts(game["AwayTeamID"]),
    }


@http_app.on_event("startup")
def on_startup():
    _start_discovery_thread()


@http_app.on_event("shutdown")
def on_shutdown():
    _stop_discovery_thread()


if sio is not None:
    @sio.event
    async def connect(sid, environ, auth):
        return True

    @sio.event
    async def disconnect(sid):
        return None


@http_app.get("/ping")
def ping():
    return {
        "message": "BSS LAN server is running",
        "service": DISCOVERY_SERVICE,
        "discovery_port": DISCOVERY_PORT,
        "socket_port": SERVER_PORT,
        "socketio_enabled": sio is not None,
    }


@http_app.post("/auth/login")
def login(data: LoginRequest):
    conn = get_conn()
    try:
        r = conn.execute(
            "SELECT Username, PasswordHash FROM USERS WHERE Username=?",
            (data.username.strip(),),
        ).fetchone()
        if not r:
            raise HTTPException(401, "User not found.")
        if r["PasswordHash"] != _hash(data.password.strip()):
            raise HTTPException(401, "Wrong password.")
        return {"message": "ok", "username": r["Username"]}
    finally:
        conn.close()


@http_app.post("/auth/signup")
def signup(data: LoginRequest):
    username = data.username.strip()
    password = data.password.strip()

    if len(username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters.")

    missing = []
    if len(password) < 8:
        missing.append("8+ characters")
    if not any(c.isupper() for c in password):
        missing.append("1 capital letter")
    if not any(c.isdigit() for c in password):
        missing.append("1 number")
    if not any(not c.isalnum() for c in password):
        missing.append("1 special character")
    if missing:
        raise HTTPException(400, "Password needs: " + ", ".join(missing))

    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO USERS (Username, PasswordHash) VALUES (?,?)",
            (username, _hash(password)),
        )
        conn.commit()
        return {"message": "Account created."}
    except Exception as exc:
        raise HTTPException(400, str(exc))
    finally:
        conn.close()


@http_app.get("/teams")
def get_teams():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT ID as id, TeamName as team_name FROM TEAMS ORDER BY TeamName"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@http_app.post("/teams")
def create_team(data: TeamCreate):
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO TEAMS (TeamName) VALUES (?)", (data.team_name,))
        conn.commit()
        return {"message": "ok", "team": {"id": cur.lastrowid, "team_name": data.team_name}}
    except Exception as exc:
        raise HTTPException(400, str(exc))
    finally:
        conn.close()


@http_app.delete("/teams/{team_id}")
def delete_team(team_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM PLAYERS WHERE TeamID=?", (team_id,))
        conn.execute("DELETE FROM TEAMS WHERE ID=?", (team_id,))
        conn.commit()
        return {"message": "ok"}
    except Exception as exc:
        raise HTTPException(400, str(exc))
    finally:
        conn.close()


@http_app.get("/teams/{team_id}/players")
def get_players(team_id: int):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT playerID as id, Jersey as jersey, FirstName as first_name, LastName as last_name FROM PLAYERS WHERE TeamID=? ORDER BY playerID",
            (team_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@http_app.post("/players")
def create_player(data: PlayerCreate):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO PLAYERS (TeamID, FirstName, LastName, Jersey) VALUES (?,?,?,?)",
            (data.team_id, data.first_name, data.last_name, data.jersey),
        )
        conn.commit()
        return {"message": "ok", "player_id": cur.lastrowid}
    except Exception as exc:
        raise HTTPException(400, str(exc))
    finally:
        conn.close()


@http_app.delete("/players/{player_id}")
def delete_player(player_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM PLAYERS WHERE playerID=?", (player_id,))
        conn.commit()
        return {"message": "ok"}
    except Exception as exc:
        raise HTTPException(400, str(exc))
    finally:
        conn.close()


@http_app.get("/games")
def get_games():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT g.GameID, g.GameLabel, g.HomeTeamID, g.AwayTeamID,
                   h.TeamName as home_name, a.TeamName as away_name
            FROM GAMES g
            JOIN TEAMS h ON h.ID=g.HomeTeamID
            JOIN TEAMS a ON a.ID=g.AwayTeamID
            ORDER BY g.GameID DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@http_app.post("/games")
def create_game(data: GameCreate):
    if data.home_team_id == data.away_team_id:
        raise HTTPException(400, "Home and Away must be different.")

    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO GAMES (GameLabel, HomeTeamID, AwayTeamID) VALUES (?,?,?)",
            (data.game_label, data.home_team_id, data.away_team_id),
        )
        conn.commit()
        return {"message": "ok", "game_label": data.game_label}
    except Exception as exc:
        raise HTTPException(400, str(exc))
    finally:
        conn.close()


@http_app.get("/games/next-label")
def next_label():
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT GameLabel FROM GAMES WHERE GameLabel LIKE 'GAME-%' ORDER BY GameID DESC LIMIT 1"
        ).fetchone()
        if row and row[0]:
            return {"label": f"GAME-{int(row[0].split('-')[1]) + 1:03d}"}
        return {"label": "GAME-001"}
    except Exception:
        return {"label": "GAME-001"}
    finally:
        conn.close()


@http_app.get("/games/{game_label}")
def get_game(game_label: str):
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT g.GameID, g.GameLabel, g.HomeTeamID, g.AwayTeamID,
                   h.TeamName as home_name, a.TeamName as away_name
            FROM GAMES g
            JOIN TEAMS h ON h.ID=g.HomeTeamID
            JOIN TEAMS a ON a.ID=g.AwayTeamID
            WHERE g.GameLabel=?
            """,
            (game_label,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Game not found.")
        return dict(row)
    finally:
        conn.close()


ALLOWED = {"TwoPM", "TwoPA", "ThreePM", "ThreePA", "FTM", "FTA", "REB", "AST", "STL", "BLK", "TOV", "PF"}


@http_app.get("/stats/{game_label}/{team_id}")
def get_stats(game_label: str, team_id: int):
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT p.playerID as player_id, p.Jersey as jersey,
                   p.FirstName as first_name, p.LastName as last_name,
                   COALESCE(s.TwoPM,0) as TwoPM, COALESCE(s.TwoPA,0) as TwoPA,
                   COALESCE(s.ThreePM,0) as ThreePM, COALESCE(s.ThreePA,0) as ThreePA,
                   COALESCE(s.FTM,0) as FTM, COALESCE(s.FTA,0) as FTA,
                   COALESCE(s.REB,0) as REB, COALESCE(s.AST,0) as AST,
                   COALESCE(s.STL,0) as STL, COALESCE(s.BLK,0) as BLK,
                   COALESCE(s.TOV,0) as TOV, COALESCE(s.PF,0) as PF
            FROM PLAYERS p
            LEFT JOIN PLAYER_STATS s ON s.PlayerID=p.playerID AND s.GameLabel=?
            WHERE p.TeamID=?
            ORDER BY p.playerID
            """,
            (game_label, team_id),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@http_app.post("/stats/update")
async def update_stat(data: StatDelta):
    if data.col not in ALLOWED:
        raise HTTPException(400, f"Invalid column: {data.col}")

    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO PLAYER_STATS (GameLabel, PlayerID, TeamID) VALUES (?,?,?)",
            (data.game_label, data.player_id, data.team_id),
        )
        conn.execute(
            f"UPDATE PLAYER_STATS SET {data.col}=MAX(COALESCE({data.col},0)+?,0) WHERE GameLabel=? AND PlayerID=?",
            (data.amount, data.game_label, data.player_id),
        )
        conn.commit()

        stats_payload = {
            "game_label": data.game_label,
            "team_id": data.team_id,
            "player_id": data.player_id,
            "col": data.col,
            "amount": data.amount,
        }
        if sio is not None:
            await sio.emit("stats_update", stats_payload)

        score_payload = _compute_score(conn, data.game_label)
        if sio is not None and score_payload is not None:
            await sio.emit("score_update", score_payload)

        return {"message": "ok"}
    finally:
        conn.close()


@http_app.get("/score/{game_label}")
def get_score(game_label: str):
    conn = get_conn()
    try:
        payload = _compute_score(conn, game_label)
        if payload is None:
            raise HTTPException(404, "Game not found.")
        return payload
    finally:
        conn.close()


@http_app.get("/active-players/{game_label}/{team_id}")
def get_active(game_label: str, team_id: int):
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ACTIVE_PLAYERS
            (GameLabel TEXT, TeamID INTEGER, PlayerID INTEGER,
             PRIMARY KEY (GameLabel, TeamID, PlayerID))
            """
        )
        rows = conn.execute(
            "SELECT PlayerID as player_id FROM ACTIVE_PLAYERS WHERE GameLabel=? AND TeamID=?",
            (game_label, team_id),
        ).fetchall()
        if not rows:
            rows = conn.execute(
                "SELECT playerID as player_id FROM PLAYERS WHERE TeamID=? ORDER BY playerID LIMIT 5",
                (team_id,),
            ).fetchall()
        return {"player_ids": [r["player_id"] for r in rows]}
    except Exception:
        return {"player_ids": []}
    finally:
        conn.close()


@http_app.post("/active-players")
async def set_active(data: ActivePlayers):
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ACTIVE_PLAYERS
            (GameLabel TEXT, TeamID INTEGER, PlayerID INTEGER,
             PRIMARY KEY (GameLabel, TeamID, PlayerID))
            """
        )
        conn.execute(
            "DELETE FROM ACTIVE_PLAYERS WHERE GameLabel=? AND TeamID=?",
            (data.game_label, data.team_id),
        )
        for player_id in data.player_ids:
            conn.execute(
                "INSERT INTO ACTIVE_PLAYERS (GameLabel, TeamID, PlayerID) VALUES (?,?,?)",
                (data.game_label, data.team_id, player_id),
            )
        conn.commit()

        if sio is not None:
            await sio.emit(
                "active_players_update",
                {
                    "game_label": data.game_label,
                    "team_id": data.team_id,
                    "player_ids": data.player_ids,
                },
            )
        return {"message": "ok"}
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"BSS LAN Server starting on port {SERVER_PORT}...")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
