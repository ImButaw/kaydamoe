import customtkinter as ctk
from tkinter import messagebox

from api_client import (
    get_teams,
    create_team,
    delete_team,
    get_players,
    create_player,
    delete_player,
)


def open_setup_teams(parent):
    setupwin = ctk.CTkToplevel(parent)
    setupwin.title("Setup Teams")
    setupwin.geometry("980x600")
    setupwin.resizable(False, False)
    setupwin.transient(parent)
    setupwin.grab_set()

    setupwin.grid_rowconfigure(0, weight=1)
    setupwin.grid_columnconfigure(0, weight=3)
    setupwin.grid_columnconfigure(1, weight=7)

    # ================= LEFT FRAME (TEAMS) =================
    leftframe = ctk.CTkFrame(setupwin)
    leftframe.grid(row=0, column=0, sticky="nsew", padx=(15, 6), pady=15)
    leftframe.grid_columnconfigure(0, weight=1)
    leftframe.grid_rowconfigure(2, weight=1)

    lefttop = ctk.CTkFrame(leftframe)
    lefttop.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    lefttop.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(lefttop, text="Team name").grid(row=0, column=0, sticky="w", pady=(6, 2))

    teamname_var = ctk.StringVar()
    team_entry = ctk.CTkEntry(lefttop, textvariable=teamname_var, placeholder_text="Enter team name")
    team_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 8))

    add_team_btn = ctk.CTkButton(lefttop, text="Add Team")
    add_team_btn.grid(row=1, column=1, pady=(0, 8))

    status_var = ctk.StringVar(value="")
    status_lbl = ctk.CTkLabel(leftframe, textvariable=status_var, text_color="#cc4444")
    status_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

    teams_list = ctk.CTkScrollableFrame(leftframe, label_text="Teams")
    teams_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
    teams_list.grid_columnconfigure(0, weight=1)

    # ================= RIGHT FRAME (PLAYERS) =================
    rightframe = ctk.CTkFrame(setupwin)
    rightframe.grid(row=0, column=1, sticky="nsew", padx=(6, 15), pady=15)
    rightframe.grid_columnconfigure(0, weight=1)
    rightframe.grid_rowconfigure(0, weight=0)
    rightframe.grid_rowconfigure(1, weight=0)
    rightframe.grid_rowconfigure(2, weight=1)
    rightframe.grid_rowconfigure(3, weight=0)

    selected_team = {"id": None, "name": ""}

    team_title_var = ctk.StringVar(value="Select a team")
    ctk.CTkLabel(
        rightframe,
        textvariable=team_title_var,
        font=ctk.CTkFont(size=22, weight="bold")
    ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

    addp = ctk.CTkFrame(rightframe)
    addp.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
    addp.grid_columnconfigure(0, weight=2)
    addp.grid_columnconfigure(1, weight=2)
    addp.grid_columnconfigure(2, weight=1)

    last_var = ctk.StringVar()
    first_var = ctk.StringVar()
    jersey_var = ctk.StringVar()

    ctk.CTkLabel(addp, text="Last name").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(8, 2))
    ctk.CTkLabel(addp, text="First name").grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(8, 2))
    ctk.CTkLabel(addp, text="Jersey no.").grid(row=0, column=2, sticky="w", pady=(8, 2))

    ctk.CTkEntry(addp, textvariable=last_var, placeholder_text="Last name").grid(
        row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 10)
    )
    ctk.CTkEntry(addp, textvariable=first_var, placeholder_text="First name").grid(
        row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 10)
    )
    ctk.CTkEntry(addp, textvariable=jersey_var, placeholder_text="Jersey no.", width=100).grid(
        row=1, column=2, sticky="ew", pady=(0, 10)
    )

    add_player_btn = ctk.CTkButton(addp, text="Add Player")
    add_player_btn.grid(row=1, column=3, padx=8, pady=(0, 10))

    players_list = ctk.CTkScrollableFrame(rightframe, label_text="Players")
    players_list.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))
    players_list.grid_columnconfigure(0, weight=0)
    players_list.grid_columnconfigure(1, weight=1)
    players_list.grid_columnconfigure(2, weight=0)

    rightbottom = ctk.CTkFrame(rightframe)
    rightbottom.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
    rightbottom.grid_columnconfigure(0, weight=1)

    remove_team_btn = ctk.CTkButton(rightbottom, text="REMOVE SELECTED TEAM")
    remove_team_btn.grid(row=0, column=0, sticky="ew", padx=6, pady=10)

    def set_status(message="", is_error=True):
        status_var.set(message)
        status_lbl.configure(text_color="#cc4444" if is_error else "#228B22")

    def refresh_teams(auto_select_id=None):
        for w in teams_list.winfo_children():
            w.destroy()

        try:
            rows = get_teams()
        except Exception as e:
            set_status(f"Failed to load teams: {e}")
            return

        set_status("", is_error=False)

        for r, t in enumerate(rows):
            tid = t["id"]
            tname = t["team_name"]

            ctk.CTkButton(
                teams_list,
                text=tname,
                height=40,
                command=lambda _id=tid, _name=tname: select_team(_id, _name)
            ).grid(row=r, column=0, sticky="ew", padx=6, pady=4)

        if auto_select_id is not None:
            for t in rows:
                if t["id"] == auto_select_id:
                    select_team(t["id"], t["team_name"])
                    break

    def refresh_players():
        for w in players_list.winfo_children():
            w.destroy()

        if not selected_team["id"]:
            return

        try:
            rows = get_players(selected_team["id"])
        except Exception as e:
            set_status(f"Failed to load players: {e}")
            return

        ctk.CTkLabel(players_list, text="No.", width=60).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ctk.CTkLabel(players_list, text="Player").grid(row=0, column=1, padx=6, pady=6, sticky="w")

        rr = 1
        for p in rows:
            pid = p["id"]
            jersey = "" if p["jersey"] is None else str(p["jersey"])
            name = f"{p['last_name']}, {p['first_name']}"

            ctk.CTkLabel(players_list, text=jersey, width=60).grid(row=rr, column=0, padx=6, pady=4, sticky="w")
            ctk.CTkLabel(players_list, text=name).grid(row=rr, column=1, padx=6, pady=4, sticky="w")

            ctk.CTkButton(
                players_list,
                text="Remove",
                width=90,
                command=lambda _pid=pid: on_remove_player(_pid)
            ).grid(row=rr, column=2, padx=6, pady=4, sticky="e")

            rr += 1

    def select_team(team_id, team_name):
        selected_team["id"] = team_id
        selected_team["name"] = team_name
        team_title_var.set(team_name)
        refresh_players()

    def on_add_team():
        name = teamname_var.get().strip()

        if not name:
            set_status("Team name is required.")
            return

        try:
            result = create_team(name)
            new_team_id = result["team"]["id"]
            teamname_var.set("")
            set_status("Team added successfully.", is_error=False)
            refresh_teams(auto_select_id=new_team_id)
        except Exception as e:
            set_status(f"Add team failed: {e}")

    def on_add_player():
        if not selected_team["id"]:
            set_status("Select a team first.")
            return

        ln = last_var.get().strip()
        fn = first_var.get().strip()
        jr = jersey_var.get().strip()

        if not ln or not fn:
            set_status("First name and last name are required.")
            return

        jersey = int(jr) if jr.isdigit() else None

        try:
            create_player(
                selected_team["id"],
                first_name=fn,
                last_name=ln,
                jersey=jersey
            )
            last_var.set("")
            first_var.set("")
            jersey_var.set("")
            set_status("Player added successfully.", is_error=False)
            refresh_players()
        except Exception as e:
            set_status(f"Add player failed: {e}")

    def on_remove_player(player_id):
        if not messagebox.askyesno("Confirm", "Remove this player?"):
            return

        try:
            delete_player(player_id)
            set_status("Player removed successfully.", is_error=False)
            refresh_players()
        except Exception as e:
            set_status(f"Remove player failed: {e}")

    def remove_selected_team():
        if not selected_team["id"]:
            set_status("Select a team first.")
            return

        if not messagebox.askyesno(
            "Confirm",
            f"Remove team '{selected_team['name']}' and all its players?"
        ):
            return

        try:
            delete_team(selected_team["id"])
            selected_team["id"] = None
            selected_team["name"] = ""
            team_title_var.set("Select a team")
            set_status("Team removed successfully.", is_error=False)
            refresh_players()
            refresh_teams()
        except Exception as e:
            set_status(f"Remove team failed: {e}")

    add_team_btn.configure(command=on_add_team)
    add_player_btn.configure(command=on_add_player)
    remove_team_btn.configure(command=remove_selected_team)

    setupwin.protocol("WM_DELETE_WINDOW", setupwin.destroy)

    refresh_teams()