from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, hashlib, uvicorn, os

DB_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "BSS.db")
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8002

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def get_conn():
    conn = sqlite3.connect(os.path.abspath(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ── MODELS ─────────────────────────────────────────────
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


# ── HEALTH ─────────────────────────────────────────────
@app.get("/ping")
def ping():
    return {"message": "BSS LAN server is running"}


# ── AUTH ───────────────────────────────────────────────
def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

@app.post("/auth/login")
def login(data: LoginRequest):
    conn = get_conn()
    try:
        r = conn.execute("SELECT Username, PasswordHash FROM USERS WHERE Username=?",
                         (data.username.strip(),)).fetchone()
        if not r: raise HTTPException(401, "User not found.")
        if r["PasswordHash"] != _hash(data.password.strip()): raise HTTPException(401, "Wrong password.")
        return {"message": "ok", "username": r["Username"]}
    finally: conn.close()

@app.post("/auth/signup")
def signup(data: LoginRequest):
    u, p = data.username.strip(), data.password.strip()
    if len(u) < 3: raise HTTPException(400, "Username must be at least 3 characters.")
    missing = []
    if len(p) < 8: missing.append("8+ characters")
    if not any(c.isupper() for c in p): missing.append("1 capital letter")
    if not any(c.isdigit() for c in p): missing.append("1 number")
    if not any(not c.isalnum() for c in p): missing.append("1 special character")
    if missing: raise HTTPException(400, "Password needs: " + ", ".join(missing))
    conn = get_conn()
    try:
        conn.execute("INSERT INTO USERS (Username, PasswordHash) VALUES (?,?)", (u, _hash(p)))
        conn.commit()
        return {"message": "Account created."}
    except Exception as e: raise HTTPException(400, str(e))
    finally: conn.close()


# ── TEAMS ──────────────────────────────────────────────
@app.get("/teams")
def get_teams():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT ID as id, TeamName as team_name FROM TEAMS ORDER BY TeamName").fetchall()
        return [dict(r) for r in rows]
    finally: conn.close()

@app.post("/teams")
def create_team(data: TeamCreate):
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO TEAMS (TeamName) VALUES (?)", (data.team_name,))
        conn.commit()
        return {"message": "ok", "team": {"id": cur.lastrowid, "team_name": data.team_name}}
    except Exception as e: raise HTTPException(400, str(e))
    finally: conn.close()

@app.delete("/teams/{team_id}")
def delete_team(team_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM PLAYERS WHERE TeamID=?", (team_id,))
        conn.execute("DELETE FROM TEAMS WHERE ID=?", (team_id,))
        conn.commit()
        return {"message": "ok"}
    except Exception as e: raise HTTPException(400, str(e))
    finally: conn.close()

@app.get("/teams/{team_id}/players")
def get_players(team_id: int):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT playerID as id, Jersey as jersey, FirstName as first_name, LastName as last_name FROM PLAYERS WHERE TeamID=? ORDER BY playerID",
            (team_id,)).fetchall()
        return [dict(r) for r in rows]
    finally: conn.close()

@app.post("/players")
def create_player(data: PlayerCreate):
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO PLAYERS (TeamID, FirstName, LastName, Jersey) VALUES (?,?,?,?)",
                           (data.team_id, data.first_name, data.last_name, data.jersey))
        conn.commit()
        return {"message": "ok", "player_id": cur.lastrowid}
    except Exception as e: raise HTTPException(400, str(e))
    finally: conn.close()

@app.delete("/players/{player_id}")
def delete_player(player_id: int):
    conn = get_conn()
    try:
        conn.execute("DELETE FROM PLAYERS WHERE playerID=?", (player_id,))
        conn.commit()
        return {"message": "ok"}
    except Exception as e: raise HTTPException(400, str(e))
    finally: conn.close()


# ── GAMES ──────────────────────────────────────────────
@app.get("/games")
def get_games():
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT g.GameID, g.GameLabel, g.HomeTeamID, g.AwayTeamID,
                   h.TeamName as home_name, a.TeamName as away_name
            FROM GAMES g JOIN TEAMS h ON h.ID=g.HomeTeamID JOIN TEAMS a ON a.ID=g.AwayTeamID
            ORDER BY g.GameID DESC""").fetchall()
        return [dict(r) for r in rows]
    finally: conn.close()

@app.post("/games")
def create_game(data: GameCreate):
    if data.home_team_id == data.away_team_id:
        raise HTTPException(400, "Home and Away must be different.")
    conn = get_conn()
    try:
        conn.execute("INSERT INTO GAMES (GameLabel, HomeTeamID, AwayTeamID) VALUES (?,?,?)",
                     (data.game_label, data.home_team_id, data.away_team_id))
        conn.commit()
        return {"message": "ok", "game_label": data.game_label}
    except Exception as e: raise HTTPException(400, str(e))
    finally: conn.close()

@app.get("/games/next-label")
def next_label():
    conn = get_conn()
    try:
        r = conn.execute("SELECT GameLabel FROM GAMES WHERE GameLabel LIKE 'GAME-%' ORDER BY GameID DESC LIMIT 1").fetchone()
        if r and r[0]:
            return {"label": f"GAME-{int(r[0].split('-')[1])+1:03d}"}
        return {"label": "GAME-001"}
    except: return {"label": "GAME-001"}
    finally: conn.close()

@app.get("/games/{game_label}")
def get_game(game_label: str):
    conn = get_conn()
    try:
        r = conn.execute("""
            SELECT g.GameID, g.GameLabel, g.HomeTeamID, g.AwayTeamID,
                   h.TeamName as home_name, a.TeamName as away_name
            FROM GAMES g JOIN TEAMS h ON h.ID=g.HomeTeamID JOIN TEAMS a ON a.ID=g.AwayTeamID
            WHERE g.GameLabel=?""", (game_label,)).fetchone()
        if not r: raise HTTPException(404, "Game not found.")
        return dict(r)
    finally: conn.close()


# ── STATS ──────────────────────────────────────────────
ALLOWED = {"TwoPM","TwoPA","ThreePM","ThreePA","FTM","FTA","REB","AST","STL","BLK","TOV","PF"}

@app.get("/stats/{game_label}/{team_id}")
def get_stats(game_label: str, team_id: int):
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT p.playerID as player_id, p.Jersey as jersey,
                   p.FirstName as first_name, p.LastName as last_name,
                   COALESCE(s.TwoPM,0) as TwoPM, COALESCE(s.TwoPA,0) as TwoPA,
                   COALESCE(s.ThreePM,0) as ThreePM, COALESCE(s.ThreePA,0) as ThreePA,
                   COALESCE(s.FTM,0) as FTM, COALESCE(s.FTA,0) as FTA,
                   COALESCE(s.REB,0) as REB, COALESCE(s.AST,0) as AST,
                   COALESCE(s.STL,0) as STL, COALESCE(s.BLK,0) as BLK,
                   COALESCE(s.TOV,0) as TOV, COALESCE(s.PF,0) as PF
            FROM PLAYERS p LEFT JOIN PLAYER_STATS s ON s.PlayerID=p.playerID AND s.GameLabel=?
            WHERE p.TeamID=? ORDER BY p.playerID""", (game_label, team_id)).fetchall()
        return [dict(r) for r in rows]
    finally: conn.close()

@app.post("/stats/update")
def update_stat(data: StatDelta):
    if data.col not in ALLOWED: raise HTTPException(400, f"Invalid column: {data.col}")
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO PLAYER_STATS (GameLabel, PlayerID, TeamID) VALUES (?,?,?)",
                     (data.game_label, data.player_id, data.team_id))
        conn.execute(f"UPDATE PLAYER_STATS SET {data.col}=MAX(COALESCE({data.col},0)+?,0) WHERE GameLabel=? AND PlayerID=?",
                     (data.amount, data.game_label, data.player_id))
        conn.commit()
        return {"message": "ok"}
    finally: conn.close()

@app.get("/score/{game_label}")
def get_score(game_label: str):
    conn = get_conn()
    try:
        g = conn.execute("SELECT HomeTeamID, AwayTeamID FROM GAMES WHERE GameLabel=?", (game_label,)).fetchone()
        if not g: raise HTTPException(404, "Game not found.")
        def pts(tid):
            r = conn.execute("SELECT COALESCE(SUM(TwoPM*2+ThreePM*3+FTM),0) as p FROM PLAYER_STATS WHERE GameLabel=? AND TeamID=?",
                             (game_label, tid)).fetchone()
            return r["p"] if r else 0
        return {"game_label": game_label, "home_team_id": g["HomeTeamID"],
                "away_team_id": g["AwayTeamID"], "home_score": pts(g["HomeTeamID"]), "away_score": pts(g["AwayTeamID"])}
    finally: conn.close()


# ── ACTIVE PLAYERS ─────────────────────────────────────
@app.get("/active-players/{game_label}/{team_id}")
def get_active(game_label: str, team_id: int):
    conn = get_conn()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS ACTIVE_PLAYERS
                        (GameLabel TEXT, TeamID INTEGER, PlayerID INTEGER,
                         PRIMARY KEY (GameLabel, TeamID, PlayerID))""")
        rows = conn.execute("SELECT PlayerID as player_id FROM ACTIVE_PLAYERS WHERE GameLabel=? AND TeamID=?",
                            (game_label, team_id)).fetchall()
        if not rows:
            rows = conn.execute("SELECT playerID as player_id FROM PLAYERS WHERE TeamID=? ORDER BY playerID LIMIT 5",
                                (team_id,)).fetchall()
        return {"player_ids": [r["player_id"] for r in rows]}
    except: return {"player_ids": []}
    finally: conn.close()

@app.post("/active-players")
def set_active(data: ActivePlayers):
    conn = get_conn()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS ACTIVE_PLAYERS
                        (GameLabel TEXT, TeamID INTEGER, PlayerID INTEGER,
                         PRIMARY KEY (GameLabel, TeamID, PlayerID))""")
        conn.execute("DELETE FROM ACTIVE_PLAYERS WHERE GameLabel=? AND TeamID=?", (data.game_label, data.team_id))
        for pid in data.player_ids:
            conn.execute("INSERT INTO ACTIVE_PLAYERS (GameLabel, TeamID, PlayerID) VALUES (?,?,?)",
                         (data.game_label, data.team_id, pid))
        conn.commit()
        return {"message": "ok"}
    finally: conn.close()


if __name__ == "__main__":
    print(f"BSS LAN Server starting on port {SERVER_PORT}...")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
