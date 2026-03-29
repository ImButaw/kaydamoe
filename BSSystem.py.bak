from customtkinter import *
import customtkinter as ctk
from PIL import Image
import os, threading, subprocess, socket, time

import api_client
import gamehistory
import setupteams
import startgame_popup
import livestats
import auth

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG       = "#0A0A0F"
SURFACE  = "#111118"
SURFACE2 = "#1A1A24"
ACCENT   = "#E8C547"
ACCENT2  = "#C9A830"
TEXT     = "#F0EDE6"
SUBTEXT  = "#7A7880"
BORDER   = "#2A2A38"
GREEN    = "#47E8A0"
RED_C    = "#E85555"

current_user = {"username": None}
lan_mode     = {"mode": None}


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def start_lan_server():
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lan_server", "main.py")
    subprocess.Popen(
        ["python", server_path],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )
    time.sleep(2)


def on_login_success(username):
    current_user["username"] = username
    show_lan_choice()


def show_lan_choice():
    dialog = CTkToplevel(mainmenu)
    dialog.title("LAN Setup")
    dialog.geometry("500x520")
    dialog.resizable(False, False)
    dialog.configure(fg_color=BG)
    dialog.transient(mainmenu)
    dialog.grab_set()

    CTkFrame(dialog, fg_color=ACCENT, height=3, corner_radius=0).pack(fill="x")

    hdr = CTkFrame(dialog, fg_color=SURFACE, corner_radius=0)
    hdr.pack(fill="x")
    CTkLabel(hdr, text="LAN SETUP",
             font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 4))
    CTkLabel(hdr, text="Choose your role for this session",
             font=ctk.CTkFont(size=13), text_color=SUBTEXT).pack(anchor="w", padx=24, pady=(0, 16))
    CTkFrame(hdr, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

    body = CTkFrame(dialog, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)
    body.grid_columnconfigure(0, weight=1)

    status_var = ctk.StringVar(value="")
    status_lbl = CTkLabel(body, textvariable=status_var,
                          font=ctk.CTkFont(size=12), text_color=SUBTEXT)
    status_lbl.grid(row=4, column=0, pady=4)

    # HOST card
    host_card = CTkFrame(body, fg_color=SURFACE2, corner_radius=12, border_width=1, border_color=ACCENT)
    host_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    host_card.grid_columnconfigure(0, weight=1)

    CTkLabel(host_card, text="HOST",
             font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT).grid(
        row=0, column=0, sticky="w", padx=20, pady=(16, 2))
    CTkLabel(host_card, text="Start the LAN server on this device.\nYou will control the HOME team.",
             font=ctk.CTkFont(size=12), text_color=SUBTEXT, justify="left").grid(
        row=1, column=0, sticky="w", padx=20, pady=(0, 4))
    CTkLabel(host_card, text=f"Your IP: {get_local_ip()}",
             font=ctk.CTkFont(size=12, weight="bold"), text_color=GREEN).grid(
        row=2, column=0, sticky="w", padx=20, pady=(0, 12))

    def do_host():
        status_var.set("Starting server, please wait...")
        dialog.update()
        def run():
            try:
                start_lan_server()
                api_client.set_server("127.0.0.1")
                api_client.ping()
                lan_mode["mode"] = "host"
                dialog.after(0, lambda: (dialog.destroy(), show_main_buttons()))
            except Exception as e:
                dialog.after(0, lambda: status_var.set(f"Server error: {e}"))
        threading.Thread(target=run, daemon=True).start()

    CTkButton(host_card, text="HOST THIS DEVICE ▶", height=40,
              fg_color=ACCENT, hover_color=ACCENT2, text_color="#0A0A0F",
              font=ctk.CTkFont(weight="bold"), corner_radius=8, command=do_host).grid(
        row=3, column=0, sticky="ew", padx=20, pady=(0, 16))

    # JOIN card
    join_card = CTkFrame(body, fg_color=SURFACE2, corner_radius=12, border_width=1, border_color=BORDER)
    join_card.grid(row=1, column=0, sticky="ew")
    join_card.grid_columnconfigure(0, weight=1)

    CTkLabel(join_card, text="JOIN",
             font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT).grid(
        row=0, column=0, sticky="w", padx=20, pady=(16, 2))
    CTkLabel(join_card, text="Connect to the host device.\nYou will control the AWAY team.",
             font=ctk.CTkFont(size=12), text_color=SUBTEXT, justify="left").grid(
        row=1, column=0, sticky="w", padx=20, pady=(0, 8))

    ip_var = ctk.StringVar(value="192.168.1.1")
    CTkEntry(join_card, textvariable=ip_var, placeholder_text="Host IP (e.g. 192.168.1.1)",
             fg_color=SURFACE, border_color=BORDER, text_color=TEXT,
             height=38, corner_radius=8).grid(
        row=2, column=0, sticky="ew", padx=20, pady=(0, 8))

    def do_join():
        ip = ip_var.get().strip()
        if not ip:
            status_var.set("Enter the host IP address.")
            return
        status_var.set(f"Connecting to {ip}...")
        dialog.update()
        def run():
            try:
                api_client.set_server(ip)
                api_client.ping()
                lan_mode["mode"] = "join"
                dialog.after(0, lambda: (dialog.destroy(), show_main_buttons()))
            except Exception as e:
                dialog.after(0, lambda: status_var.set(f"Cannot connect: {e}"))
        threading.Thread(target=run, daemon=True).start()

    CTkButton(join_card, text="CONNECT & JOIN", height=40,
              fg_color=SURFACE, hover_color=SURFACE2, text_color=TEXT,
              border_width=1, border_color=BORDER,
              font=ctk.CTkFont(weight="bold"), corner_radius=8, command=do_join).grid(
        row=3, column=0, sticky="ew", padx=20, pady=(0, 16))


def show_main_buttons():
    for w in btn_area.winfo_children():
        w.destroy()

    is_host = lan_mode["mode"] == "host"

    def make_btn(label, sublabel, icon, command, row, col, accent=False):
        fg    = ACCENT   if accent else SURFACE2
        txt   = "#0A0A0F" if accent else TEXT
        hover = ACCENT2  if accent else "#222230"
        CTkButton(
            btn_area,
            text=f"{icon}  {label}\n{sublabel}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=txt, fg_color=fg, hover_color=hover,
            corner_radius=12, border_width=1,
            border_color=ACCENT if accent else BORDER,
            command=command, anchor="center",
        ).grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

    if is_host:
        make_btn("START GAME", "Host a new match", "▶",
                 lambda: startgame_popup.open_start_game(mainmenu, on_start_host), 0, 0, accent=True)
        make_btn("SETUP TEAMS", "Manage rosters", "👥",
                 lambda: setupteams.open_setup_teams(mainmenu), 0, 1)
        make_btn("GAME HISTORY", "View past games", "📋",
                 lambda: gamehistory.open_game_history(mainmenu, current_user["username"] or "Unknown"), 1, 0)
        make_btn("EXIT", "Close application", "✕", mainmenu.destroy, 1, 1)
    else:
        make_btn("JOIN GAME", "Connect to host's game", "🔗",
                 open_join_game, 0, 0, accent=True)
        make_btn("GAME HISTORY", "View past games", "📋",
                 lambda: gamehistory.open_game_history(mainmenu, current_user["username"] or "Unknown"), 0, 1)
        make_btn("EXIT", "Close application", "✕", mainmenu.destroy, 1, 0)

    mode_txt = f"{'HOST' if is_host else 'JOIN'} — {'Server: ' + get_local_ip() + ':8002' if is_host else api_client.SERVER_URL}"
    CTkLabel(right, text=mode_txt, font=ctk.CTkFont(size=11),
             text_color=ACCENT if is_host else GREEN).grid(row=2, column=0, pady=(0, 10))


def on_start_host(home_id, away_id, game_label):
    livestats.open_live_stats(mainmenu, home_id, away_id, game_label)


def open_join_game():
    try:
        games = api_client.get_games()
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Connection Error", f"Cannot reach host.\n{e}")
        return

    if not games:
        from tkinter import messagebox
        messagebox.showinfo("No Games", "No games yet. Ask the host to start a game first.")
        return

    pop = CTkToplevel(mainmenu)
    pop.title("Join Game")
    pop.geometry("480x360")
    pop.configure(fg_color=BG)
    pop.resizable(False, False)
    pop.transient(mainmenu)
    pop.grab_set()

    CTkFrame(pop, fg_color=ACCENT, height=3, corner_radius=0).pack(fill="x")
    hdr = CTkFrame(pop, fg_color=SURFACE, corner_radius=0)
    hdr.pack(fill="x")
    CTkLabel(hdr, text="JOIN GAME", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT).pack(
        anchor="w", padx=24, pady=(16, 4))
    CTkLabel(hdr, text="You will join as the AWAY team",
             font=ctk.CTkFont(size=12), text_color=SUBTEXT).pack(anchor="w", padx=24, pady=(0, 16))
    CTkFrame(hdr, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

    body = CTkFrame(pop, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)
    body.grid_columnconfigure(0, weight=1)

    CTkLabel(body, text="SELECT GAME", font=ctk.CTkFont(size=10, weight="bold"),
             text_color=SUBTEXT).grid(row=0, column=0, sticky="w", pady=(0, 6))

    game_values = [f"{g['game_label']}  |  {g['home_name']} vs {g['away_name']}" for g in games]
    game_var = ctk.StringVar(value=game_values[0])
    CTkOptionMenu(body, variable=game_var, values=game_values,
                  fg_color=SURFACE2, button_color=SURFACE2, button_hover_color=BORDER,
                  text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
                  height=40, corner_radius=8).grid(row=1, column=0, sticky="ew", pady=(0, 8))

    msg_var = ctk.StringVar(value="")
    CTkLabel(body, textvariable=msg_var, text_color=RED_C,
             font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w")

    CTkFrame(pop, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")
    btn_row = CTkFrame(pop, fg_color=SURFACE, corner_radius=0)
    btn_row.pack(fill="x")
    btn_row.grid_columnconfigure(0, weight=1)
    btn_row.grid_columnconfigure(1, weight=1)

    def join_clicked():
        label = game_var.get().split("|")[0].strip()
        game = next((g for g in games if g["game_label"] == label), None)
        if not game:
            msg_var.set("Game not found.")
            return
        pop.destroy()
        livestats.open_live_stats(mainmenu, game["home_team_id"], game["away_team_id"],
                                  game["game_label"], game["away_team_id"])

    CTkButton(btn_row, text="CANCEL", height=48, fg_color="transparent",
              hover_color=SURFACE2, text_color=SUBTEXT, corner_radius=0,
              command=pop.destroy).grid(row=0, column=0, sticky="ew")
    CTkButton(btn_row, text="JOIN AS AWAY 🔗", height=48,
              fg_color=ACCENT, hover_color=ACCENT2, text_color="#0A0A0F",
              font=ctk.CTkFont(weight="bold"), corner_radius=0,
              command=join_clicked).grid(row=0, column=1, sticky="ew")


# ── WINDOW ─────────────────────────────────────────────
mainmenu = CTk()
mainmenu.title("BSS — Valley High Academy")
mainmenu.geometry("1366x768")
mainmenu.resizable(False, False)
mainmenu.configure(fg_color=BG)
mainmenu.grid_rowconfigure(0, weight=1)
mainmenu.grid_columnconfigure(0, weight=30)
mainmenu.grid_columnconfigure(1, weight=70)

left = CTkFrame(mainmenu, fg_color=SURFACE, corner_radius=0)
left.grid(row=0, column=0, sticky="nsew")
left.grid_columnconfigure(0, weight=1)
left.grid_rowconfigure(3, weight=1)

CTkFrame(left, fg_color=ACCENT, height=3, corner_radius=0).grid(row=0, column=0, sticky="ew")

base_dir  = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_dir, "assets", "vhalogo.jpg")
logo_container = CTkFrame(left, fg_color="transparent")
logo_container.grid(row=1, column=0, pady=(40, 20))

if os.path.exists(logo_path):
    logo_img = Image.open(logo_path)
    logo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(180, 180))
    CTkLabel(logo_container, image=logo, text="").pack()
    logo_container.logo = logo
else:
    CTkLabel(logo_container, text="🏀", font=("Arial", 60)).pack()

CTkLabel(left, text="VALLEY HIGH ACADEMY",
         font=ctk.CTkFont(size=14, weight="bold"), text_color=ACCENT).grid(row=2, column=0, pady=(0, 4))
CTkLabel(left, text="Basketball Scoring System",
         font=ctk.CTkFont(size=12), text_color=SUBTEXT).grid(row=3, column=0, sticky="n")
CTkFrame(left, fg_color=BORDER, height=1, corner_radius=0).grid(row=4, column=0, sticky="ew", pady=(0, 20))
CTkLabel(left, text="© 2026 VHA Athletics",
         font=ctk.CTkFont(size=11), text_color="#3A3A4A").grid(row=5, column=0, pady=(0, 20))

right = CTkFrame(mainmenu, fg_color=BG, corner_radius=0)
right.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
right.grid_columnconfigure(0, weight=1)
right.grid_rowconfigure(1, weight=1)

header = CTkFrame(right, fg_color="transparent")
header.grid(row=0, column=0, sticky="ew", padx=50, pady=(50, 0))
CTkLabel(header, text="BASKETBALL",
         font=ctk.CTkFont(size=48, weight="bold"), text_color=TEXT).pack(anchor="w")
title_row = CTkFrame(header, fg_color="transparent")
title_row.pack(fill="x")
CTkLabel(title_row, text="SCORING",
         font=ctk.CTkFont(size=48, weight="bold"), text_color=ACCENT).pack(side="left")
CTkLabel(title_row, text=" SYSTEM",
         font=ctk.CTkFont(size=48, weight="bold"), text_color=TEXT).pack(side="left")
CTkFrame(header, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x", pady=(16, 0))

btn_area = CTkFrame(right, fg_color="transparent")
btn_area.grid(row=1, column=0, sticky="nsew", padx=50, pady=30)
btn_area.grid_columnconfigure(0, weight=1)
btn_area.grid_columnconfigure(1, weight=1)
btn_area.grid_rowconfigure(0, weight=1)
btn_area.grid_rowconfigure(1, weight=1)

CTkLabel(btn_area, text="Please log in to continue...",
         font=ctk.CTkFont(size=16), text_color=SUBTEXT).grid(row=0, column=0, columnspan=2)

auth.open_auth(mainmenu, on_login_success)
mainmenu.mainloop()
