import customtkinter as ctk
import api_client

BG      = "#0A0A0F"
SURFACE = "#111118"
SURFACE2= "#1A1A24"
ACCENT  = "#E8C547"
ACCENT2 = "#C9A830"
TEXT    = "#F0EDE6"
SUBTEXT = "#7A7880"
BORDER  = "#2A2A38"
ERROR   = "#E85555"


def open_start_game(parent, on_start):
    try:
        teams = api_client.get_teams()
        values = [f"{t['team_name']} (ID: {t['id']})" for t in teams]
    except Exception as e:
        values = ["(server error)"]

    if not values:
        values = ["(no teams found)"]

    pop = ctk.CTkToplevel(parent)
    pop.title("Start Game")
    pop.geometry("500x480")
    pop.resizable(False, False)
    pop.transient(parent)
    pop.grab_set()
    pop.configure(fg_color=BG)
    pop.grid_columnconfigure(0, weight=1)

    ctk.CTkFrame(pop, fg_color=ACCENT, height=3, corner_radius=0).grid(row=0, column=0, sticky="ew")

    hdr = ctk.CTkFrame(pop, fg_color=SURFACE, corner_radius=0)
    hdr.grid(row=1, column=0, sticky="ew")
    hdr.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(hdr, text="NEW GAME",
                 font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT).grid(
        row=0, column=0, sticky="w", padx=28, pady=(20, 4))
    ctk.CTkLabel(hdr, text="Configure matchup details",
                 font=ctk.CTkFont(size=13), text_color=SUBTEXT).grid(
        row=1, column=0, sticky="w", padx=28, pady=(0, 16))
    ctk.CTkFrame(hdr, fg_color=BORDER, height=1, corner_radius=0).grid(row=2, column=0, sticky="ew")

    form = ctk.CTkFrame(pop, fg_color="transparent")
    form.grid(row=2, column=0, sticky="nsew", padx=28, pady=20)
    form.grid_columnconfigure(0, weight=1)
    pop.grid_rowconfigure(2, weight=1)

    def field_label(text, row):
        ctk.CTkLabel(form, text=text.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=SUBTEXT).grid(row=row, column=0, sticky="w", pady=(0, 4))

    def field_entry(var, row, placeholder=""):
        e = ctk.CTkEntry(form, textvariable=var, placeholder_text=placeholder,
                         fg_color=SURFACE2, border_color=BORDER,
                         text_color=TEXT, placeholder_text_color=SUBTEXT,
                         height=40, corner_radius=8)
        e.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        return e

    def field_option(var, vals, row):
        o = ctk.CTkOptionMenu(form, variable=var, values=vals,
                              fg_color=SURFACE2, button_color=SURFACE2,
                              button_hover_color=BORDER, text_color=TEXT,
                              dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
                              dropdown_hover_color=SURFACE2,
                              corner_radius=8, height=40)
        o.grid(row=row, column=0, sticky="ew", pady=(0, 16))

    game_var = ctk.StringVar(value=api_client.get_next_label())
    home_var = ctk.StringVar(value=values[0])
    away_var = ctk.StringVar(value=values[0] if len(values) == 1 else values[1])

    field_label("Game Label", 0)
    game_entry = field_entry(game_var, 1, "e.g. GAME-001")
    field_label("Home Team (Host controls)", 2)
    field_option(home_var, values, 3)
    field_label("Away Team (Join controls)", 4)
    field_option(away_var, values, 5)

    msg_var = ctk.StringVar(value="")
    ctk.CTkLabel(form, textvariable=msg_var, font=ctk.CTkFont(size=12),
                 text_color=ERROR).grid(row=6, column=0, sticky="w")

    ctk.CTkFrame(pop, fg_color=BORDER, height=1, corner_radius=0).grid(row=3, column=0, sticky="ew")
    btns = ctk.CTkFrame(pop, fg_color=SURFACE, corner_radius=0)
    btns.grid(row=4, column=0, sticky="ew")
    btns.grid_columnconfigure(0, weight=1)
    btns.grid_columnconfigure(1, weight=1)

    def parse_id(t):
        return int(t.split("(ID:")[1].replace(")", "").strip())

    def start_clicked():
        gl = game_var.get().strip()
        if not gl:
            msg_var.set("Game label is required.")
            return
        if "(server error)" in home_var.get() or "(no teams found)" in home_var.get():
            msg_var.set("No teams found. Setup teams first.")
            return
        home_id = parse_id(home_var.get())
        away_id = parse_id(away_var.get())
        if home_id == away_id:
            msg_var.set("Home and Away must be different.")
            return
        try:
            api_client.create_game(gl, home_id, away_id)
        except Exception as e:
            msg_var.set(f"Error: {e}")
            return
        pop.destroy()
        on_start(home_id, away_id, gl)

    ctk.CTkButton(btns, text="CANCEL", height=50, fg_color="transparent",
                  hover_color=SURFACE2, text_color=SUBTEXT, corner_radius=0,
                  command=pop.destroy).grid(row=0, column=0, sticky="ew")
    ctk.CTkButton(btns, text="START GAME ▶", height=50, fg_color=ACCENT,
                  hover_color=ACCENT2, text_color="#0A0A0F",
                  font=ctk.CTkFont(weight="bold"), corner_radius=0,
                  command=start_clicked).grid(row=0, column=1, sticky="ew")

    game_entry.focus()
    pop.bind("<Return>", lambda e: start_clicked())
