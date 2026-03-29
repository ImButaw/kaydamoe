import sqlite3
import customtkinter as ctk
import os
import api_client

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BSS.db")

TEAMS_TABLE   = "TEAMS"
PLAYERS_TABLE = "PLAYERS"
STATS_TABLE   = "PLAYER_STATS"

# â”€â”€ THEME â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BG        = "#080810"
SURFACE   = "#0E0E1A"
SURFACE2  = "#14142A"
SURFACE3  = "#1C1C33"
SURFACE4  = "#22223C"
ACCENT    = "#F0C040"
ACCENT2   = "#C99A28"
ACCENT_DIM= "#3A2E08"
TEXT      = "#F4F1EC"
SUBTEXT   = "#6A6880"
MUTED     = "#3A3850"
BORDER    = "#1E1E30"
BORDER2   = "#2A2A42"
GREEN     = "#3DE8A0"
GREEN_DIM = "#0A2E1E"
RED_C     = "#E84455"
RED_DIM   = "#2E0A12"
ACTIVE_BG = "#0E1E16"
BLUE      = "#4A9EFF"

FONT_HEAD = "Helvetica"
FONT_MONO = "Courier"


def open_live_stats(parent, home_id, away_id, game_label, controlled_team_id=None):
    conn = None
    use_remote = True
    socket_connected = {"ok": False}

    try:
        api_client.ping()
    except Exception:
        use_remote = False

    if not use_remote:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")

        def table_exists(name):
            r = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
            ).fetchone()
            return r is not None

        missing = [t for t in [TEAMS_TABLE, PLAYERS_TABLE, STATS_TABLE] if not table_exists(t)]
        if missing:
            err = ctk.CTkToplevel(parent)
            err.title("Missing Tables")
            err.geometry("500x200")
            err.configure(fg_color=BG)
            ctk.CTkLabel(err, text=f"Missing tables: {', '.join(missing)}",
                         text_color=RED_C, font=ctk.CTkFont(size=16)).pack(pady=30)
            ctk.CTkButton(err, text="Close", command=lambda: (conn.close(), err.destroy()),
                          fg_color=SURFACE2).pack()
            return

    # â”€â”€ FULLSCREEN WINDOW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    win = ctk.CTkToplevel(parent)
    win.title(f"Live Scoring â€” {game_label}")
    win.configure(fg_color=BG)
    win.transient(parent)

    # Windows: state(zoomed) maximizes but keeps taskbar; combine with geometry for true fullscreen
    def _go_fullscreen():
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{sw}x{sh}+0+0")
        try:
            win.state("zoomed")
        except Exception:
            pass
        win.lift()
        win.focus_force()
        win.grab_set()

    win.after(80, _go_fullscreen)

    win.grid_rowconfigure(0, weight=0)
    win.grid_rowconfigure(1, weight=1)
    win.grid_columnconfigure(0, weight=20)
    win.grid_columnconfigure(1, weight=45)
    win.grid_columnconfigure(2, weight=35)

    # â”€â”€ TOP BAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    topbar = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0, height=64)
    topbar.grid(row=0, column=0, columnspan=3, sticky="ew")
    topbar.grid_propagate(False)
    topbar.grid_columnconfigure(2, weight=1)

    ctk.CTkFrame(topbar, fg_color=ACCENT, width=5, corner_radius=0).grid(
        row=0, column=0, sticky="ns")

    live_frame = ctk.CTkFrame(topbar, fg_color=RED_C, corner_radius=6, width=60, height=28)
    live_frame.grid(row=0, column=1, padx=(14, 10))
    live_frame.grid_propagate(False)
    ctk.CTkLabel(live_frame, text="â— LIVE",
                 font=ctk.CTkFont(family=FONT_HEAD, size=11, weight="bold"),
                 text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(topbar, text=game_label.upper(),
                 font=ctk.CTkFont(family=FONT_HEAD, size=19, weight="bold"),
                 text_color=TEXT).grid(row=0, column=2, sticky="w")

    team_name_var = ctk.StringVar(value="â€”")
    ctk.CTkLabel(topbar, textvariable=team_name_var,
                 font=ctk.CTkFont(size=13), text_color=SUBTEXT).grid(
        row=0, column=3, sticky="e", padx=(0, 12))

    team_var = ctk.StringVar(value="")
    team_option = ctk.CTkOptionMenu(
        topbar, variable=team_var, values=["(loading...)"],
        fg_color=SURFACE3, button_color=SURFACE4,
        button_hover_color=BORDER2, text_color=TEXT,
        dropdown_fg_color=SURFACE2, dropdown_text_color=TEXT,
        width=240, height=36, corner_radius=8
    )
    team_option.grid(row=0, column=4, sticky="e", padx=(0, 12))

    ctk.CTkLabel(topbar, text="ESC  exit fullscreen",
                 font=ctk.CTkFont(size=10), text_color=MUTED).grid(
        row=0, column=5, sticky="e", padx=(0, 16))

    win.bind("<Escape>", lambda e: win.state("normal"))

    # â”€â”€ LEFT PANEL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    left = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0)
    left.grid(row=1, column=0, sticky="nsew", padx=(0, 1))
    left.grid_columnconfigure(0, weight=1)
    left.grid_rowconfigure(3, weight=1)

    def section_header(parent, text, row, icon=""):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=14, pady=(14, 5))
        ctk.CTkFrame(f, fg_color=ACCENT, width=3, height=14, corner_radius=2).pack(
            side="left", padx=(0, 8))
        ctk.CTkLabel(f, text=(icon + "  " if icon else "") + text.upper(),
                     font=ctk.CTkFont(family=FONT_HEAD, size=10, weight="bold"),
                     text_color=SUBTEXT).pack(side="left")

    section_header(left, "Activity Log", 0, "â–¸")

    log_box = ctk.CTkTextbox(left, height=120, fg_color=SURFACE2,
                              text_color=SUBTEXT,
                              font=ctk.CTkFont(family=FONT_MONO, size=11),
                              corner_radius=10, border_width=1, border_color=BORDER2,
                              scrollbar_button_color=BORDER2)
    log_box.grid(row=1, column=0, padx=14, pady=(0, 6), sticky="ew")
    log_box.configure(state="disabled")

    section_header(left, "Active Players", 2, "â–¸")

    players_list = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                           scrollbar_button_color=BORDER2)
    players_list.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 6))
    players_list.grid_columnconfigure(0, weight=1)

    action_frame = ctk.CTkFrame(left, fg_color="transparent")
    action_frame.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 14))
    action_frame.grid_columnconfigure(0, weight=1)

    sub_btn = ctk.CTkButton(
        action_frame, text="â‡„  SUBSTITUTE", height=38, corner_radius=10,
        fg_color=SURFACE3, hover_color=SURFACE4,
        text_color=BLUE, border_width=1, border_color=BLUE,
        font=ctk.CTkFont(family=FONT_HEAD, size=12, weight="bold"))
    sub_btn.grid(row=0, column=0, sticky="ew", pady=3)

    undo_btn = ctk.CTkButton(
        action_frame, text="â†©  UNDO LAST", height=38, corner_radius=10,
        fg_color=SURFACE3, hover_color=SURFACE4,
        text_color=SUBTEXT, border_width=1, border_color=BORDER2,
        font=ctk.CTkFont(family=FONT_HEAD, size=12))
    undo_btn.grid(row=1, column=0, sticky="ew", pady=3)

    finish_btn = ctk.CTkButton(
        action_frame, text="â¹  FINISH GAME", height=38, corner_radius=10,
        fg_color=RED_DIM, hover_color=RED_C,
        text_color=RED_C, border_width=1, border_color=RED_C,
        font=ctk.CTkFont(family=FONT_HEAD, size=12, weight="bold"))
    finish_btn.grid(row=2, column=0, sticky="ew", pady=3)

    # â”€â”€ MIDDLE PANEL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    mid = ctk.CTkFrame(win, fg_color=BG, corner_radius=0)
    mid.grid(row=1, column=1, sticky="nsew", padx=1)
    mid.grid_columnconfigure(0, weight=1)
    mid.grid_rowconfigure(0, weight=0)
    mid.grid_rowconfigure(1, weight=1)

    sel_bar = ctk.CTkFrame(mid, fg_color=SURFACE2, corner_radius=12, height=64,
                            border_width=1, border_color=BORDER2)
    sel_bar.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
    sel_bar.grid_propagate(False)
    sel_bar.grid_columnconfigure(0, weight=1)

    sel_info = ctk.StringVar(value="Select a player to begin")
    ctk.CTkLabel(sel_bar, textvariable=sel_info,
                 font=ctk.CTkFont(family=FONT_HEAD, size=17, weight="bold"),
                 text_color=TEXT).grid(row=0, column=0, sticky="w", padx=18)

    sel_pts_var = ctk.StringVar(value="")
    ctk.CTkLabel(sel_bar, textvariable=sel_pts_var,
                 font=ctk.CTkFont(family=FONT_HEAD, size=22, weight="bold"),
                 text_color=ACCENT).grid(row=0, column=1, sticky="e", padx=18)

    btns_outer = ctk.CTkFrame(mid, fg_color="transparent")
    btns_outer.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
    btns_outer.grid_columnconfigure(0, weight=1)
    btns_outer.grid_columnconfigure(1, weight=1)
    for i in range(6):
        btns_outer.grid_rowconfigure(i, weight=1)

    def stat_btn(parent, label, sublabel, command, row, col, highlight=False, danger=False):
        if highlight:
            fg, border_c, txt, sub, hover = ACCENT_DIM, ACCENT, ACCENT, ACCENT2, "#2E2408"
        elif danger:
            fg, border_c, txt, sub, hover = RED_DIM, RED_C, RED_C, RED_C, "#3E0A14"
        else:
            fg, border_c, txt, sub, hover = SURFACE2, BORDER2, TEXT, SUBTEXT, SURFACE3

        b = ctk.CTkButton(
            parent,
            text=f"{label}\n{sublabel}",
            font=ctk.CTkFont(family=FONT_HEAD, size=15, weight="bold"),
            text_color=txt,
            fg_color=fg, hover_color=hover,
            corner_radius=14,
            border_width=1, border_color=border_c,
            command=command,
            anchor="center",
        )
        b.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        return b

    # â”€â”€ RIGHT PANEL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    right = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=0)
    right.grid(row=1, column=2, sticky="nsew", padx=(1, 0))
    right.grid_rowconfigure(1, weight=1)
    right.grid_columnconfigure(0, weight=1)

    tab_bar = ctk.CTkFrame(right, fg_color=SURFACE2, corner_radius=10,
                            border_width=1, border_color=BORDER2)
    tab_bar.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 0))
    tab_bar.grid_columnconfigure((0, 1, 2), weight=1)

    right_mode = ctk.StringVar(value="SELECTED")
    tab_btns = {}

    def make_tab(text, mode, col):
        def click():
            right_mode.set(mode)
            for btn, m in tab_btns.items():
                active = (m == mode)
                btn.configure(
                    fg_color=ACCENT if active else "transparent",
                    text_color="#080810" if active else SUBTEXT)
            refresh_right_panel()

        b = ctk.CTkButton(tab_bar, text=text, height=34, corner_radius=8,
                          fg_color=ACCENT if mode == "SELECTED" else "transparent",
                          hover_color=SURFACE3,
                          text_color="#080810" if mode == "SELECTED" else SUBTEXT,
                          font=ctk.CTkFont(family=FONT_HEAD, size=11, weight="bold"),
                          command=click)
        b.grid(row=0, column=col, sticky="ew", padx=3, pady=3)
        return b

    t1 = make_tab("SELECTED", "SELECTED", 0)
    t2 = make_tab("STAT SHEET", "BOX", 1)
    t3 = make_tab("SUMMARY", "SUMMARY", 2)
    tab_btns[t1] = "SELECTED"
    tab_btns[t2] = "BOX"
    tab_btns[t3] = "SUMMARY"

    right_body = ctk.CTkScrollableFrame(right, fg_color="transparent",
                                         scrollbar_button_color=BORDER2)
    right_body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(8, 8))
    right_body.grid_columnconfigure(0, weight=1)

    # â”€â”€ STATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    state = {"team_id": None, "team_name": "", "player_id": None, "player_name": ""}
    active_ids = {"ids": []}
    action_stack = []

    # â”€â”€ HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def add_log(text):
        log_box.configure(state="normal")
        log_box.insert("end", text + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")

    def fetch_teams():
        nonlocal use_remote
        if use_remote:
            try:
                rows = [
                    t for t in api_client.get_teams()
                    if t["id"] in {home_id, away_id}
                ]
                if controlled_team_id is not None:
                    rows = [t for t in rows if t["id"] == controlled_team_id]
                rows.sort(key=lambda r: r["team_name"])
                return [{"id": r["id"], "name": r["team_name"]} for r in rows]
            except Exception:
                use_remote = False

        rows = conn.execute(
            f"SELECT ID AS id, TeamName AS name FROM {TEAMS_TABLE} WHERE ID IN (?,?) ORDER BY TeamName",
            (home_id, away_id),
        ).fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def fetch_players(team_id):
        nonlocal use_remote
        if use_remote:
            try:
                rows = api_client.get_players(team_id)
                return [
                    {
                        "id": r["id"],
                        "jersey": r.get("jersey"),
                        "first_name": r["first_name"],
                        "last_name": r["last_name"],
                    }
                    for r in rows
                ]
            except Exception:
                use_remote = False

        rows = conn.execute(
            f"""SELECT playerID AS id, Jersey AS jersey,
                       FirstName AS first_name, LastName AS last_name
                FROM {PLAYERS_TABLE} WHERE TeamID=? ORDER BY playerID ASC""",
            (team_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "jersey": r["jersey"],
                "first_name": r["first_name"],
                "last_name": r["last_name"],
            }
            for r in rows
        ]

    def game_label_now():
        return game_label

    def ensure_stat_row(gl, player_id, team_id):
        if use_remote:
            return

        conn.execute(
            f"INSERT OR IGNORE INTO {STATS_TABLE} (GameLabel, PlayerID, TeamID) VALUES (?,?,?)",
            (gl, player_id, team_id),
        )
        conn.commit()

    def apply_delta(gl, player_id, team_id, col, amount):
        nonlocal use_remote
        allowed = {"TwoPM","TwoPA","ThreePM","ThreePA","FTM","FTA","REB","AST","STL","BLK","TOV","PF"}
        if col not in allowed:
            return
        if use_remote:
            try:
                api_client.update_stat(gl, player_id, team_id, col, amount)
                return
            except Exception:
                use_remote = False

        conn.execute(
            f"UPDATE {STATS_TABLE} SET {col}=MAX(COALESCE({col},0)+?,0) WHERE GameLabel=? AND PlayerID=?",
            (amount, gl, player_id),
        )
        conn.commit()

    def pct(made, att):
        return f"{(made/att)*100:.0f}%" if att else "â€”"

    def query_box(gl, team_id):
        nonlocal use_remote
        if use_remote:
            try:
                rows = api_client.get_stats(gl, team_id)
                rows.sort(key=lambda r: r["player_id"])
                return rows
            except Exception:
                use_remote = False

        rows = conn.execute(f"""
            SELECT p.playerID AS player_id, p.Jersey AS jersey,
                   p.LastName AS last_name, p.FirstName AS first_name,
                   COALESCE(s.TwoPM,0) AS TwoPM, COALESCE(s.TwoPA,0) AS TwoPA,
                   COALESCE(s.ThreePM,0) AS ThreePM, COALESCE(s.ThreePA,0) AS ThreePA,
                   COALESCE(s.FTM,0) AS FTM, COALESCE(s.FTA,0) AS FTA,
                   COALESCE(s.REB,0) AS REB, COALESCE(s.AST,0) AS AST,
                   COALESCE(s.STL,0) AS STL, COALESCE(s.BLK,0) AS BLK,
                   COALESCE(s.TOV,0) AS TOV, COALESCE(s.PF,0) AS PF
            FROM {PLAYERS_TABLE} p
            LEFT JOIN {STATS_TABLE} s ON s.PlayerID=p.playerID AND s.GameLabel=?
            WHERE p.TeamID=? ORDER BY p.playerID ASC
        """, (gl, team_id)).fetchall()
        return [dict(r) for r in rows]

    # â”€â”€ RIGHT PANEL REFRESH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def refresh_right_panel():
        for w in right_body.winfo_children():
            w.destroy()

        if not state["team_id"]:
            ctk.CTkLabel(right_body, text="Select a team.", text_color=SUBTEXT).pack(pady=20)
            return

        gl = game_label_now()
        rows = query_box(gl, state["team_id"])
        mode = right_mode.get()

        if mode == "SELECTED":
            if not state["player_id"]:
                ctk.CTkLabel(right_body, text="No player selected.",
                             text_color=SUBTEXT).pack(pady=20)
                return

            sel = next((r for r in rows if r["player_id"] == state["player_id"]), None)
            if not sel:
                sel = {"TwoPM":0,"TwoPA":0,"ThreePM":0,"ThreePA":0,
                       "FTM":0,"FTA":0,"REB":0,"AST":0,"STL":0,"BLK":0,"TOV":0,"PF":0}

            two_m, two_a = sel["TwoPM"], sel["TwoPA"]
            th_m, th_a   = sel["ThreePM"], sel["ThreePA"]
            ft_m, ft_a   = sel["FTM"], sel["FTA"]
            pts = two_m*2 + th_m*3 + ft_m

            ph = ctk.CTkFrame(right_body, fg_color=SURFACE2, corner_radius=12,
                              border_width=1, border_color=BORDER2)
            ph.pack(fill="x", pady=(4, 8), padx=4)
            ph.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(ph, text=state["player_name"].upper(),
                         font=ctk.CTkFont(family=FONT_HEAD, size=13, weight="bold"),
                         text_color=SUBTEXT).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(ph, text=f"{pts}",
                         font=ctk.CTkFont(family=FONT_HEAD, size=42, weight="bold"),
                         text_color=ACCENT).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 2))
            ctk.CTkLabel(ph, text="PTS",
                         font=ctk.CTkFont(size=11),
                         text_color=SUBTEXT).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))

            def stat_row(label, val, sub=""):
                f = ctk.CTkFrame(right_body, fg_color=SURFACE2, corner_radius=8, height=42,
                                 border_width=1, border_color=BORDER)
                f.pack(fill="x", pady=2, padx=4)
                f.grid_propagate(False)
                f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10),
                             text_color=SUBTEXT, width=46).grid(row=0, column=0, padx=12, sticky="w")
                ctk.CTkLabel(f, text=str(val),
                             font=ctk.CTkFont(family=FONT_HEAD, size=14, weight="bold"),
                             text_color=TEXT).grid(row=0, column=1, sticky="w")
                if sub:
                    ctk.CTkLabel(f, text=sub, font=ctk.CTkFont(size=11),
                                 text_color=ACCENT2).grid(row=0, column=2, padx=12, sticky="e")

            stat_row("FG",  f"{two_m+th_m}/{two_a+th_a}", pct(two_m+th_m, two_a+th_a))
            stat_row("2PT", f"{two_m}/{two_a}", pct(two_m, two_a))
            stat_row("3PT", f"{th_m}/{th_a}", pct(th_m, th_a))
            stat_row("FT",  f"{ft_m}/{ft_a}", pct(ft_m, ft_a))
            stat_row("REB", sel["REB"])
            stat_row("AST", sel["AST"])
            stat_row("STL", sel["STL"])
            stat_row("BLK", sel["BLK"])
            stat_row("TO",  sel["TOV"])
            stat_row("PF",  sel["PF"])

        elif mode == "BOX":
            headers = ["Player","#","2M","2A","3M","3A","FM","FA","RB","AS","ST","BK","TO","PF","PTS"]
            col_w   = [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

            hf = ctk.CTkFrame(right_body, fg_color=ACCENT, corner_radius=8)
            hf.pack(fill="x", padx=4, pady=(4, 0))
            for ci, (h, w) in enumerate(zip(headers, col_w)):
                hf.grid_columnconfigure(ci, weight=w)
                ctk.CTkLabel(hf, text=h,
                             font=ctk.CTkFont(family=FONT_HEAD, size=9, weight="bold"),
                             text_color="#080810", width=8).grid(
                    row=0, column=ci, padx=1, pady=6, sticky="ew")

            t2m=t2a=t3m=t3a=tftm=tfta=treb=tast=tstl=tblk=ttov=tpf=tpts=0

            for idx, r in enumerate(rows):
                tm, ta = r["TwoPM"], r["TwoPA"]
                hm, ha = r["ThreePM"], r["ThreePA"]
                fm, fa = r["FTM"], r["FTA"]
                pts = tm*2 + hm*3 + fm
                t2m+=tm;t2a+=ta;t3m+=hm;t3a+=ha
                tftm+=fm;tfta+=fa;treb+=r["REB"];tast+=r["AST"]
                tstl+=r["STL"];tblk+=r["BLK"];ttov+=r["TOV"];tpf+=r["PF"];tpts+=pts

                is_active = r["player_id"] in active_ids["ids"]
                bg = ACTIVE_BG if is_active else (SURFACE2 if idx%2==0 else SURFACE3)
                rf = ctk.CTkFrame(right_body, fg_color=bg, corner_radius=0)
                rf.pack(fill="x", padx=4, pady=0)
                for ci, w in enumerate(col_w):
                    rf.grid_columnconfigure(ci, weight=w)

                name = f"{r['last_name']}, {r['first_name']}"
                jersey = "" if r["jersey"] is None else str(r["jersey"])
                vals = [name,jersey,tm,ta,hm,ha,fm,fa,r["REB"],r["AST"],r["STL"],r["BLK"],r["TOV"],r["PF"],pts]
                for ci, (v, w) in enumerate(zip(vals, col_w)):
                    ctk.CTkLabel(rf, text=str(v),
                                 font=ctk.CTkFont(size=9),
                                 text_color=GREEN if is_active else TEXT,
                                 width=8).grid(row=0, column=ci, padx=1, pady=4, sticky="ew")

            tf = ctk.CTkFrame(right_body, fg_color=SURFACE4, corner_radius=0,
                              border_width=1, border_color=BORDER2)
            tf.pack(fill="x", padx=4, pady=(0, 4))
            for ci, w in enumerate(col_w):
                tf.grid_columnconfigure(ci, weight=w)
            tots = ["TOTAL","",t2m,t2a,t3m,t3a,tftm,tfta,treb,tast,tstl,tblk,ttov,tpf,tpts]
            for ci, (v, w) in enumerate(zip(tots, col_w)):
                ctk.CTkLabel(tf, text=str(v),
                             font=ctk.CTkFont(family=FONT_HEAD, size=9, weight="bold"),
                             text_color=ACCENT, width=8).grid(
                    row=0, column=ci, padx=1, pady=6, sticky="ew")

        else:  # SUMMARY
            t = {k:0 for k in ["pts","reb","ast","stl","blk","tov","pf",
                                "fg_m","fg_a","two_m","two_a","th_m","th_a","ft_m","ft_a"]}
            for r in rows:
                t["two_m"]+=r["TwoPM"];t["two_a"]+=r["TwoPA"]
                t["th_m"]+=r["ThreePM"];t["th_a"]+=r["ThreePA"]
                t["ft_m"]+=r["FTM"];t["ft_a"]+=r["FTA"]
                t["fg_m"]+=r["TwoPM"]+r["ThreePM"];t["fg_a"]+=r["TwoPA"]+r["ThreePA"]
                t["pts"]+=r["TwoPM"]*2+r["ThreePM"]*3+r["FTM"]
                t["reb"]+=r["REB"];t["ast"]+=r["AST"];t["stl"]+=r["STL"]
                t["blk"]+=r["BLK"];t["tov"]+=r["TOV"];t["pf"]+=r["PF"]

            ph = ctk.CTkFrame(right_body, fg_color=ACCENT_DIM, corner_radius=12,
                              border_width=1, border_color=ACCENT2)
            ph.pack(fill="x", padx=4, pady=(4, 12))
            ctk.CTkLabel(ph, text="TEAM TOTAL",
                         font=ctk.CTkFont(family=FONT_HEAD, size=10, weight="bold"),
                         text_color=ACCENT2).pack(anchor="w", padx=14, pady=(12, 0))
            ctk.CTkLabel(ph, text=str(t["pts"]),
                         font=ctk.CTkFont(family=FONT_HEAD, size=48, weight="bold"),
                         text_color=ACCENT).pack(anchor="w", padx=14, pady=(0, 2))
            ctk.CTkLabel(ph, text="POINTS",
                         font=ctk.CTkFont(size=10), text_color=ACCENT2).pack(
                anchor="w", padx=14, pady=(0, 12))

            def sum_row(label, val, pct_val=""):
                f = ctk.CTkFrame(right_body, fg_color=SURFACE2, corner_radius=8, height=42,
                                 border_width=1, border_color=BORDER)
                f.pack(fill="x", pady=2, padx=4)
                f.grid_propagate(False)
                f.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10),
                             text_color=SUBTEXT, width=46).grid(row=0, column=0, padx=12, sticky="w")
                ctk.CTkLabel(f, text=str(val),
                             font=ctk.CTkFont(family=FONT_HEAD, size=14, weight="bold"),
                             text_color=TEXT).grid(row=0, column=1, sticky="w")
                if pct_val:
                    ctk.CTkLabel(f, text=pct_val, font=ctk.CTkFont(size=11),
                                 text_color=ACCENT2).grid(row=0, column=2, padx=12, sticky="e")

            sum_row("FG",  f"{t['fg_m']}/{t['fg_a']}", pct(t['fg_m'],t['fg_a']))
            sum_row("2PT", f"{t['two_m']}/{t['two_a']}", pct(t['two_m'],t['two_a']))
            sum_row("3PT", f"{t['th_m']}/{t['th_a']}", pct(t['th_m'],t['th_a']))
            sum_row("FT",  f"{t['ft_m']}/{t['ft_a']}", pct(t['ft_m'],t['ft_a']))
            sum_row("REB", t["reb"])
            sum_row("AST", t["ast"])
            sum_row("STL", t["stl"])
            sum_row("BLK", t["blk"])
            sum_row("TO",  t["tov"])
            sum_row("PF",  t["pf"])

    # â”€â”€ PLAYERS LIST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def select_player(pid, display_name):
        state["player_id"] = pid
        state["player_name"] = display_name
        sel_info.set(display_name)
        add_log(f"â— {display_name}")
        gl = game_label_now()
        if gl and state["team_id"]:
            try:
                ensure_stat_row(gl, pid, state["team_id"])
                rows = query_box(gl, state["team_id"])
                sel = next((r for r in rows if r["player_id"] == pid), None)
                if sel:
                    pts = sel["TwoPM"]*2 + sel["ThreePM"]*3 + sel["FTM"]
                    sel_pts_var.set(f"{pts} PTS")
            except:
                pass
        refresh_right_panel()

    def refresh_players_list():
        for w in players_list.winfo_children():
            w.destroy()
        state["player_id"] = None
        state["player_name"] = ""
        sel_info.set("Select a player to begin")
        sel_pts_var.set("")

        if not state["team_id"]:
            return

        rows = fetch_players(state["team_id"])
        if not active_ids["ids"]:
            if use_remote:
                try:
                    active_ids["ids"] = api_client.get_active(game_label_now(), state["team_id"])
                except Exception:
                    active_ids["ids"] = []

        if not active_ids["ids"]:
            active_ids["ids"] = [p["id"] for p in rows[:5]]
            if use_remote and active_ids["ids"]:
                try:
                    api_client.set_active(game_label_now(), state["team_id"], active_ids["ids"])
                except Exception:
                    pass

        active_rows = [p for p in rows if p["id"] in active_ids["ids"]]
        for r, p in enumerate(active_rows):
            pid = p["id"]
            jersey = str(p["jersey"]) if p["jersey"] else "â€”"
            name = f"{p['last_name']}, {p['first_name']}"

            btn_frame = ctk.CTkFrame(players_list, fg_color=SURFACE2, corner_radius=10,
                                     border_width=1, border_color=BORDER2)
            btn_frame.grid(row=r, column=0, sticky="ew", pady=3)
            btn_frame.grid_columnconfigure(1, weight=1)

            j_badge = ctk.CTkFrame(btn_frame, fg_color=ACCENT_DIM, corner_radius=6,
                                   width=38, height=32)
            j_badge.grid(row=0, column=0, padx=8, pady=8)
            j_badge.grid_propagate(False)
            ctk.CTkLabel(j_badge, text=f"#{jersey}",
                         font=ctk.CTkFont(family=FONT_HEAD, size=11, weight="bold"),
                         text_color=ACCENT).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkButton(btn_frame, text=name, anchor="w",
                          fg_color="transparent", hover_color=SURFACE3,
                          text_color=TEXT, font=ctk.CTkFont(size=13),
                          command=lambda _pid=pid, _n=name: select_player(_pid, _n)
                          ).grid(row=0, column=1, sticky="ew", padx=(0, 6))

        refresh_right_panel()

    # â”€â”€ SUBSTITUTE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def open_sub_popup():
        if not state["team_id"]:
            return
        rows = fetch_players(state["team_id"])
        bench = [p for p in rows if p["id"] not in active_ids["ids"]]
        active = [p for p in rows if p["id"] in active_ids["ids"]]

        pop = ctk.CTkToplevel(win)
        pop.title("Substitute")
        pop.geometry("540x600")
        pop.configure(fg_color=BG)
        pop.resizable(False, False)
        pop.transient(win)
        pop.grab_set()

        ctk.CTkFrame(pop, fg_color=ACCENT, height=3, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(pop, text="SUBSTITUTION",
                     font=ctk.CTkFont(family=FONT_HEAD, size=22, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=24, pady=(16, 2))
        ctk.CTkLabel(pop, text="Select player coming IN, then player going OUT",
                     font=ctk.CTkFont(size=12), text_color=SUBTEXT).pack(anchor="w", padx=24)

        sel_in_var = ctk.StringVar(value="IN: â€”")
        sel_out_var = ctk.StringVar(value="OUT: â€”")
        chosen_in  = {"pid": None, "name": ""}
        chosen_out = {"pid": None, "name": ""}

        status = ctk.CTkFrame(pop, fg_color=SURFACE2, corner_radius=10,
                              border_width=1, border_color=BORDER2)
        status.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(status, textvariable=sel_in_var,
                     font=ctk.CTkFont(family=FONT_HEAD, size=13, weight="bold"),
                     text_color=GREEN).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(status, textvariable=sel_out_var,
                     font=ctk.CTkFont(family=FONT_HEAD, size=13, weight="bold"),
                     text_color=RED_C).pack(anchor="w", padx=12, pady=(2, 8))

        cols = ctk.CTkFrame(pop, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=24, pady=8)
        cols.grid_columnconfigure(0, weight=1)
        cols.grid_columnconfigure(1, weight=1)

        bench_f = ctk.CTkScrollableFrame(cols, label_text="BENCH  â†’  IN",
                                          fg_color=SURFACE2, corner_radius=10,
                                          label_text_color=GREEN,
                                          scrollbar_button_color=BORDER2)
        bench_f.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        active_f = ctk.CTkScrollableFrame(cols, label_text="ACTIVE  â†’  OUT",
                                           fg_color=SURFACE2, corner_radius=10,
                                           label_text_color=RED_C,
                                           scrollbar_button_color=BORDER2)
        active_f.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        def make_disp(p):
            j = str(p["jersey"]) if p["jersey"] else "â€”"
            return f"#{j}  {p['last_name']}, {p['first_name']}"

        for p in bench:
            d = make_disp(p)
            ctk.CTkButton(bench_f, text=d, anchor="w", height=36,
                          fg_color="transparent", hover_color=GREEN_DIM,
                          text_color=TEXT, font=ctk.CTkFont(size=12),
                          command=lambda _pid=p["id"], _d=d: (
                              chosen_in.update({"pid": _pid, "name": _d}),
                              sel_in_var.set(f"IN: {_d}")
                          )).pack(fill="x", pady=2)

        for p in active:
            d = make_disp(p)
            ctk.CTkButton(active_f, text=d, anchor="w", height=36,
                          fg_color="transparent", hover_color=RED_DIM,
                          text_color=TEXT, font=ctk.CTkFont(size=12),
                          command=lambda _pid=p["id"], _d=d: (
                              chosen_out.update({"pid": _pid, "name": _d}),
                              sel_out_var.set(f"OUT: {_d}")
                          )).pack(fill="x", pady=2)

        msg_var = ctk.StringVar(value="")
        ctk.CTkLabel(pop, textvariable=msg_var, text_color=RED_C,
                     font=ctk.CTkFont(size=12)).pack(pady=4)

        def apply_sub():
            if not chosen_in["pid"] or not chosen_out["pid"]:
                msg_var.set("Select both IN and OUT players.")
                return
            active_ids["ids"] = [
                chosen_in["pid"] if x == chosen_out["pid"] else x
                for x in active_ids["ids"]]
            if use_remote:
                try:
                    api_client.set_active(game_label_now(), state["team_id"], active_ids["ids"])
                except Exception:
                    pass
            add_log(f"SUB â–¶ IN {chosen_in['name']} | OUT {chosen_out['name']}")
            pop.destroy()
            refresh_players_list()

        ctk.CTkButton(pop, text="APPLY SUBSTITUTION", height=46,
                      fg_color=ACCENT, hover_color=ACCENT2,
                      text_color="#080810",
                      font=ctk.CTkFont(family=FONT_HEAD, weight="bold", size=14),
                      corner_radius=10, command=apply_sub).pack(
            fill="x", padx=24, pady=(0, 18))

    sub_btn.configure(command=open_sub_popup)

    # â”€â”€ TEAM CHANGE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def on_team_change(choice):
        active_ids["ids"] = []
        if "(ID:" in choice:
            tid = int(choice.split("(ID:")[1].replace(")", "").strip())
            tname = choice.split("(ID:")[0].strip()
            state["team_id"] = tid
            state["team_name"] = tname
            team_name_var.set(tname)
            add_log(f"â–¶ {tname}")
            refresh_players_list()

    team_option.configure(command=lambda c: on_team_change(c))

    def load_teams():
        teams = fetch_teams()
        if not teams:
            team_option.configure(values=["(no teams)"])
            return
        values = [f"{t['name']} (ID: {t['id']})" for t in teams]
        team_option.configure(values=values)
        if controlled_team_id is not None:
            default = next((v for v in values if f"(ID: {controlled_team_id})" in v), values[0])
            team_option.configure(state="disabled")
        else:
            default = next((v for v in values if f"(ID: {home_id})" in v), values[0])
            team_option.configure(state="normal")
        team_var.set(default)
        on_team_change(default)

    # â”€â”€ STAT ACTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def require_ready():
        return state["team_id"] and state["player_id"]

    def do_action(name, deltas):
        if not require_ready():
            add_log("âš  Select a player first.")
            return
        if controlled_team_id is not None and state["team_id"] != controlled_team_id:
            add_log("âš  You can only update your assigned team.")
            return
        gl = game_label_now()
        try:
            ensure_stat_row(gl, state["player_id"], state["team_id"])
            for col, amt in deltas:
                apply_delta(gl, state["player_id"], state["team_id"], col, amt)
        except Exception as e:
            add_log(f"âš  Update failed: {e}")
            return
        action_stack.append({
            "gl": gl, "player_id": state["player_id"],
            "team_id": state["team_id"],
            "player_name": state["player_name"], "deltas": deltas})
        try:
            rows = query_box(gl, state["team_id"])
            sel = next((r for r in rows if r["player_id"] == state["player_id"]), None)
            if sel:
                pts = sel["TwoPM"]*2 + sel["ThreePM"]*3 + sel["FTM"]
                sel_pts_var.set(f"{pts} PTS")
        except:
            pass
        add_log(f"âœ“ {name}: {state['player_name']}")
        refresh_right_panel()

    def undo_last():
        if not action_stack:
            add_log("Nothing to undo.")
            return
        last = action_stack.pop()
        try:
            for col, amt in last["deltas"]:
                apply_delta(last["gl"], last["player_id"], last["team_id"], col, -amt)
        except Exception as e:
            add_log(f"âš  Undo failed: {e}")
            return
        add_log(f"â†© UNDO: {last['player_name']}")
        refresh_right_panel()

    undo_btn.configure(command=undo_last)
    finish_btn.configure(command=lambda: on_close())

    stat_btn(btns_outer, "2PT MADE", "+2 pts",  lambda: do_action("2PT MADE", [("TwoPM",1),("TwoPA",1)]), 0, 0, highlight=True)
    stat_btn(btns_outer, "2PT MISS", "attempt", lambda: do_action("2PT MISS", [("TwoPA",1)]),             0, 1)
    stat_btn(btns_outer, "3PT MADE", "+3 pts",  lambda: do_action("3PT MADE", [("ThreePM",1),("ThreePA",1)]), 1, 0, highlight=True)
    stat_btn(btns_outer, "3PT MISS", "attempt", lambda: do_action("3PT MISS", [("ThreePA",1)]),           1, 1)
    stat_btn(btns_outer, "FT MADE",  "+1 pt",   lambda: do_action("FT MADE",  [("FTM",1),("FTA",1)]),    2, 0, highlight=True)
    stat_btn(btns_outer, "FT MISS",  "attempt", lambda: do_action("FT MISS",  [("FTA",1)]),               2, 1)
    stat_btn(btns_outer, "REBOUND",  "+1 REB",  lambda: do_action("REB",      [("REB",1)]),               3, 0)
    stat_btn(btns_outer, "ASSIST",   "+1 AST",  lambda: do_action("AST",      [("AST",1)]),               3, 1)
    stat_btn(btns_outer, "STEAL",    "+1 STL",  lambda: do_action("STL",      [("STL",1)]),               4, 0)
    stat_btn(btns_outer, "BLOCK",    "+1 BLK",  lambda: do_action("BLK",      [("BLK",1)]),               4, 1)
    stat_btn(btns_outer, "TURNOVER", "+1 TO",   lambda: do_action("TO",       [("TOV",1)]),               5, 0)
    stat_btn(btns_outer, "FOUL",     "+1 PF",   lambda: do_action("FOUL",     [("PF",1)]),                5, 1, danger=True)

    def setup_socket_sync():
        if not use_remote:
            return

        def handle_stats_update(payload):
            if payload.get("game_label") != game_label_now():
                return
            win.after(0, refresh_right_panel)

        def handle_score_update(payload):
            if payload.get("game_label") != game_label_now():
                return
            win.after(0, refresh_right_panel)

        def handle_active_players(payload):
            if payload.get("game_label") != game_label_now():
                return
            if state["team_id"] != payload.get("team_id"):
                return

            def _apply():
                active_ids["ids"] = payload.get("player_ids", []) or []
                refresh_players_list()

            win.after(0, _apply)

        try:
            api_client.clear_socket_handlers()
            api_client.on_stats_update(handle_stats_update)
            api_client.on_score_update(handle_score_update)
            api_client.on_active_players_update(handle_active_players)
            api_client.connect_socket()
            socket_connected["ok"] = True
            add_log("LAN live sync connected")
        except Exception as e:
            add_log(f"LAN sync unavailable: {e}")

    add_log(f"Game {game_label} started")
    load_teams()
    setup_socket_sync()

    def on_close():
        try:
            if socket_connected["ok"]:
                api_client.disconnect_socket()
                api_client.clear_socket_handlers()
        except:
            pass
        try:
            if conn is not None:
                conn.close()
        except:
            pass
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

