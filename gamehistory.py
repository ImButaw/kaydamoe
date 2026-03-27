# gamehistory.py
import sqlite3
import customtkinter as ctk
from tkinter import filedialog
import os

import api_client
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BSS.db")


def open_game_history(parent, prepared_by="Unknown"):
    conn = None
    use_remote = True
    teams_cache = {}
    try:
        api_client.ping()
        teams_cache = {t["id"]: t["team_name"] for t in api_client.get_teams()}
    except Exception:
        use_remote = False

    win = ctk.CTkToplevel(parent)
    win.title("Game History")
    win.geometry("1250x720")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    win.grid_columnconfigure(0, weight=2)  # list
    win.grid_columnconfigure(1, weight=3)  # details
    win.grid_rowconfigure(0, weight=1)

    left = ctk.CTkFrame(win)
    left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
    left.grid_columnconfigure(0, weight=1)
    left.grid_rowconfigure(1, weight=1)

    right = ctk.CTkFrame(win)
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
    right.grid_columnconfigure(0, weight=1)
    right.grid_rowconfigure(2, weight=1)

    ctk.CTkLabel(left, text="GAME HISTORY", font=ctk.CTkFont(size=24, weight="bold")).grid(
        row=0, column=0, padx=12, pady=(12, 8), sticky="w"
    )

    games_list = ctk.CTkScrollableFrame(left)
    games_list.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    games_list.grid_columnconfigure(0, weight=1)

    # right header
    header = ctk.CTkFrame(right)
    header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
    header.grid_columnconfigure(0, weight=1)

    title_var = ctk.StringVar(value="Select a game and click SEE")
    ctk.CTkLabel(header, textvariable=title_var, font=ctk.CTkFont(size=18, weight="bold")).grid(
        row=0, column=0, padx=12, pady=12, sticky="w"
    )

    # export row
    actions = ctk.CTkFrame(right)
    actions.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
    actions.grid_columnconfigure(0, weight=1)

    export_btn = ctk.CTkButton(actions, text="EXPORT PDF (STAT SHEET)", height=42, state="disabled")
    export_btn.grid(row=0, column=0, sticky="ew", padx=6, pady=6)

    # details body
    details = ctk.CTkScrollableFrame(right)
    details.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
    details.grid_columnconfigure(0, weight=1)

    selected_game = {"row": None}  # store selected game row

    # ---------------- DB helpers ----------------
    def conn():
        c = sqlite3.connect(DB_PATH)
        c.row_factory = sqlite3.Row
        return c

    def get_games():
        nonlocal use_remote
        if use_remote:
            try:
                return api_client.get_games()
            except Exception:
                use_remote = False

        c = conn()
        rows = c.execute("""
            SELECT GameID, GameLabel, HomeTeamID, AwayTeamID
            FROM GAMES
            ORDER BY GameID DESC
        """).fetchall()
        c.close()
        return rows

    def team_name(team_id):
        nonlocal use_remote
        if use_remote:
            name = teams_cache.get(team_id)
            if name is not None:
                return name
            try:
                teams = api_client.get_teams()
                teams_cache.update({t["id"]: t["team_name"] for t in teams})
                return teams_cache.get(team_id, f"Team {team_id}")
            except Exception:
                use_remote = False

        c = conn()
        r = c.execute("SELECT TeamName FROM TEAMS WHERE ID=?", (team_id,)).fetchone()
        c.close()
        return r["TeamName"] if r else f"Team {team_id}"

    def fetch_team_box(game_label, team_id):
        nonlocal use_remote
        if use_remote:
            try:
                return api_client.get_stats(game_label, team_id)
            except Exception:
                use_remote = False

        c = conn()
        rows = c.execute("""
            SELECT
                p.LastName AS last_name,
                p.FirstName AS first_name,
                p.Jersey AS jersey,

                COALESCE(s.TwoPM,0) AS TwoPM,
                COALESCE(s.TwoPA,0) AS TwoPA,
                COALESCE(s.ThreePM,0) AS ThreePM,
                COALESCE(s.ThreePA,0) AS ThreePA,
                COALESCE(s.FTM,0) AS FTM,
                COALESCE(s.FTA,0) AS FTA,
                COALESCE(s.REB,0) AS REB,
                COALESCE(s.AST,0) AS AST,
                COALESCE(s.STL,0) AS STL,
                COALESCE(s.BLK,0) AS BLK,
                COALESCE(s.TOV,0) AS TOV,
                COALESCE(s.PF,0)  AS PF
            FROM PLAYERS p
            LEFT JOIN PLAYER_STATS s
              ON s.PlayerID = p.playerID
             AND s.GameLabel = ?
            WHERE p.TeamID = ?
            ORDER BY CAST(p.Jersey AS INTEGER) IS NULL,
                     CAST(p.Jersey AS INTEGER),
                     p.LastName, p.FirstName
        """, (game_label, team_id)).fetchall()
        c.close()
        return rows

    def pct(m, a):
        if a == 0:
            return ""
        return f"{(m/a)*100:.0f}%"

    # ---------------- UI render ----------------
    def clear_details():
        for w in details.winfo_children():
            w.destroy()

    def render_team_sheet(parent_frame, label_text, rows):
        card = ctk.CTkFrame(parent_frame)
        card.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(card, text=label_text, font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 8), sticky="w"
        )

        headers = ["PLAYER", "FG", "FG%", "2PT", "2PT%", "3PT", "3PT%", "FT", "FT%", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"]

        grid = ctk.CTkFrame(card)
        grid.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
        for i in range(len(headers)):
            grid.grid_columnconfigure(i, weight=1)

        for i, h in enumerate(headers):
            ctk.CTkLabel(grid, text=h, font=ctk.CTkFont(size=12, weight="bold")).grid(
                row=0, column=i, padx=4, pady=(6, 8), sticky="w"
            )

        total_pts = total_reb = total_ast = total_stl = total_blk = total_to = total_pf = 0
        total_fg_m = total_fg_a = 0
        total_two_m = total_two_a = 0
        total_th_m = total_th_a = 0
        total_ft_m = total_ft_a = 0

        rrow = 1
        for x in rows:
            two_m, two_a = x["TwoPM"], x["TwoPA"]
            th_m, th_a = x["ThreePM"], x["ThreePA"]
            ft_m, ft_a = x["FTM"], x["FTA"]
            fg_m = two_m + th_m
            fg_a = two_a + th_a
            pts = two_m*2 + th_m*3 + ft_m

            jersey = "" if x["jersey"] is None else str(x["jersey"])
            name = f"{jersey} {x['last_name']}, {x['first_name']}".strip()

            vals = [
                name,
                f"{fg_m}/{fg_a}", pct(fg_m, fg_a),
                f"{two_m}/{two_a}", pct(two_m, two_a),
                f"{th_m}/{th_a}", pct(th_m, th_a),
                f"{ft_m}/{ft_a}", pct(ft_m, ft_a),
                str(x["REB"]), str(x["AST"]), str(x["STL"]), str(x["BLK"]),
                str(x["TOV"]), str(x["PF"]), str(pts)
            ]

            for i, v in enumerate(vals):
                ctk.CTkLabel(grid, text=v).grid(row=rrow, column=i, padx=4, pady=3, sticky="w")

            total_pts += pts
            total_reb += x["REB"]; total_ast += x["AST"]; total_stl += x["STL"]
            total_blk += x["BLK"]; total_to += x["TOV"]; total_pf += x["PF"]
            total_fg_m += fg_m; total_fg_a += fg_a
            total_two_m += two_m; total_two_a += two_a
            total_th_m += th_m; total_th_a += th_a
            total_ft_m += ft_m; total_ft_a += ft_a

            rrow += 1

        # totals line
        totals_text = (
            f"TOTALS | PTS {total_pts} | FG {total_fg_m}/{total_fg_a} {pct(total_fg_m,total_fg_a)} | "
            f"2PT {total_two_m}/{total_two_a} {pct(total_two_m,total_two_a)} | "
            f"3PT {total_th_m}/{total_th_a} {pct(total_th_m,total_th_a)} | "
            f"FT {total_ft_m}/{total_ft_a} {pct(total_ft_m,total_ft_a)} | "
            f"REB {total_reb} AST {total_ast} STL {total_stl} BLK {total_blk} TO {total_to} PF {total_pf}"
        )
        ctk.CTkLabel(card, text=totals_text, font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, padx=12, pady=(0, 12), sticky="w"
        )

    def show_game(game_row):
        selected_game["row"] = game_row
        export_btn.configure(state="normal")

        clear_details()

        gl = game_row["GameLabel"]
        home_id = game_row["HomeTeamID"]
        away_id = game_row["AwayTeamID"]

        home_name = team_name(home_id)
        away_name = team_name(away_id)

        title_var.set(f"Game: {gl}   |   HOME: {home_name}   vs   AWAY: {away_name}")

        home_rows = fetch_team_box(gl, home_id)
        away_rows = fetch_team_box(gl, away_id)

        render_team_sheet(details, f"HOME TEAM: {home_name}", home_rows)
        render_team_sheet(details, f"AWAY TEAM: {away_name}", away_rows)

    # ---------------- PDF export ----------------
    def build_pdf_table_rows(rows):
        data = [["PLAYER", "FG", "FG%", "2PT", "2PT%", "3PT", "3PT%", "FT", "FT%", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"]]

        total_pts = total_reb = total_ast = total_stl = total_blk = total_to = total_pf = 0
        total_fg_m = total_fg_a = 0
        total_two_m = total_two_a = 0
        total_th_m = total_th_a = 0
        total_ft_m = total_ft_a = 0

        for x in rows:
            two_m, two_a = x["TwoPM"], x["TwoPA"]
            th_m, th_a = x["ThreePM"], x["ThreePA"]
            ft_m, ft_a = x["FTM"], x["FTA"]
            fg_m = two_m + th_m
            fg_a = two_a + th_a
            pts = two_m*2 + th_m*3 + ft_m

            jersey = "" if x["jersey"] is None else str(x["jersey"])
            name = f"{jersey} {x['last_name']}, {x['first_name']}".strip()

            row = [
                name,
                f"{fg_m}/{fg_a}", pct(fg_m, fg_a),
                f"{two_m}/{two_a}", pct(two_m, two_a),
                f"{th_m}/{th_a}", pct(th_m, th_a),
                f"{ft_m}/{ft_a}", pct(ft_m, ft_a),
                str(x["REB"]), str(x["AST"]), str(x["STL"]), str(x["BLK"]),
                str(x["TOV"]), str(x["PF"]), str(pts)
            ]
            data.append(row)

            total_pts += pts
            total_reb += x["REB"]; total_ast += x["AST"]; total_stl += x["STL"]
            total_blk += x["BLK"]; total_to += x["TOV"]; total_pf += x["PF"]
            total_fg_m += fg_m; total_fg_a += fg_a
            total_two_m += two_m; total_two_a += two_a
            total_th_m += th_m; total_th_a += th_a
            total_ft_m += ft_m; total_ft_a += ft_a

        totals = (
            f"TOTALS: PTS {total_pts} | FG {total_fg_m}/{total_fg_a} {pct(total_fg_m,total_fg_a)} | "
            f"2PT {total_two_m}/{total_two_a} {pct(total_two_m,total_two_a)} | "
            f"3PT {total_th_m}/{total_th_a} {pct(total_th_m,total_th_a)} | "
            f"FT {total_ft_m}/{total_ft_a} {pct(total_ft_m,total_ft_a)} | "
            f"REB {total_reb} AST {total_ast} STL {total_stl} BLK {total_blk} TO {total_to} PF {total_pf}"
        )
        return data, totals

    def export_pdf():
        g = selected_game["row"]
        if not g:
            return

        gl = g["GameLabel"]
        home_id = g["HomeTeamID"]
        away_id = g["AwayTeamID"]
        home_name = team_name(home_id)
        away_name = team_name(away_id)

        # choose save path
        default_name = f"{gl}_STAT_SHEET.pdf"
        out_path = filedialog.asksaveasfilename(
            parent=win,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_name,
            title="Save Stat Sheet PDF"
        )
        if not out_path:
            return

        home_rows = fetch_team_box(gl, home_id)
        away_rows = fetch_team_box(gl, away_id)

        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(out_path, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)

        story = []
        story.append(Paragraph(f"<b>Stat Sheet</b> - {gl}", styles["Title"]))
        story.append(Paragraph(f"<b>HOME:</b> {home_name} &nbsp;&nbsp;&nbsp; <b>AWAY:</b> {away_name}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # HOME
        story.append(Paragraph(f"<b>HOME TEAM: {home_name}</b>", styles["Heading2"]))
        data, totals = build_pdf_table_rows(home_rows)
        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 6))
        story.append(Paragraph(totals, styles["Normal"]))
        story.append(Spacer(1, 18))

        # AWAY
        story.append(Paragraph(f"<b>AWAY TEAM: {away_name}</b>", styles["Heading2"]))
        data2, totals2 = build_pdf_table_rows(away_rows)
        t2 = Table(data2, repeatRows=1)
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(t2)
        story.append(Spacer(1, 6))
        story.append(Paragraph(totals2, styles["Normal"]))

        doc.build(story)

        # small success popup
        ok = ctk.CTkToplevel(win)
        ok.title("Exported")
        ok.geometry("420x180")
        ok.resizable(False, False)
        ok.transient(win)
        ok.grab_set()
        ctk.CTkLabel(ok, text="PDF Exported!", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(18, 10))
        ctk.CTkLabel(ok, text=out_path, wraplength=380).pack(pady=8)
        ctk.CTkButton(ok, text="Close", command=ok.destroy).pack(pady=12)

    export_btn.configure(command=export_pdf)

    # ---------------- populate list ----------------
    def load_list():
        for w in games_list.winfo_children():
            w.destroy()

        rows = get_games()
        if not rows:
            ctk.CTkLabel(games_list, text="No games found.").grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        for i, g in enumerate(rows):
            rowf = ctk.CTkFrame(games_list)
            rowf.grid(row=i, column=0, sticky="ew", padx=6, pady=6)
            rowf.grid_columnconfigure(0, weight=1)

            gl = g["GameLabel"]
            home_id = g["HomeTeamID"]
            away_id = g["AwayTeamID"]

            summary = f"{gl}  |  HOME ID: {home_id}  |  AWAY ID: {away_id}"
            ctk.CTkLabel(rowf, text=summary, font=ctk.CTkFont(size=14)).grid(
                row=0, column=0, padx=10, pady=10, sticky="w"
            )

            ctk.CTkButton(rowf, text="SEE", width=90, command=lambda _g=g: show_game(_g)).grid(
                row=0, column=1, padx=10, pady=10, sticky="e"
            )

    load_list()