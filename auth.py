import customtkinter as ctk
import api_client
import hashlib
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BSS.db")


def _get_local_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS USERS (Username TEXT PRIMARY KEY, PasswordHash TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def local_login(username: str, password: str):
    conn = _get_local_conn()
    try:
        row = conn.execute(
            "SELECT PasswordHash FROM USERS WHERE Username=?",
            (username,),
        ).fetchone()
        if not row:
            raise Exception("User not found.")
        if row["PasswordHash"] != _hash_password(password):
            raise Exception("Wrong password.")
        return True
    finally:
        conn.close()


def local_signup(username: str, password: str):
    conn = _get_local_conn()
    try:
        existing = conn.execute(
            "SELECT 1 FROM USERS WHERE Username=?",
            (username,),
        ).fetchone()
        if existing:
            raise Exception("Username already exists.")
        conn.execute(
            "INSERT INTO USERS (Username, PasswordHash) VALUES (?,?)",
            (username, _hash_password(password)),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def _password_requirements(pw: str):
    missing = []
    if len(pw) < 8:
        missing.append("At least 8 characters")
    if not any(ch.isupper() for ch in pw):
        missing.append("At least 1 capital letter")
    if not any(ch.isdigit() for ch in pw):
        missing.append("At least 1 number")
    if not any(not ch.isalnum() for ch in pw):
        missing.append("At least 1 special character")
    return missing


def open_auth(parent, on_success):
    win = ctk.CTkToplevel(parent)
    win.title("Login")
    win.geometry("520x430")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    def close_all():
        try:
            win.grab_release()
        except Exception:
            pass
        parent.destroy()

    win.protocol("WM_DELETE_WINDOW", close_all)
    win.grid_columnconfigure(0, weight=1)

    title = ctk.CTkLabel(win, text="LOGIN", font=ctk.CTkFont(size=26, weight="bold"))
    title.grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")

    box = ctk.CTkFrame(win)
    box.grid(row=1, column=0, padx=20, pady=(4, 4), sticky="ew")
    box.grid_columnconfigure(0, weight=1)

    username_var = ctk.StringVar()
    password_var = ctk.StringVar()
    mode = ctk.StringVar(value="login")
    msg_var = ctk.StringVar(value="")
    requirements_var = ctk.StringVar(value="")

    ctk.CTkLabel(box, text="Username").grid(
        row=0, column=0, padx=14, pady=(14, 4), sticky="w")
    username_entry = ctk.CTkEntry(box, textvariable=username_var, placeholder_text="e.g. scorer1")
    username_entry.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="ew")

    ctk.CTkLabel(box, text="Password").grid(
        row=2, column=0, padx=14, pady=(0, 4), sticky="w")
    password_entry = ctk.CTkEntry(box, textvariable=password_var, show="*", placeholder_text="password")
    password_entry.grid(row=3, column=0, padx=14, pady=(0, 6), sticky="ew")

    requirements_lbl = ctk.CTkLabel(box, textvariable=requirements_var,
                                    text_color="#d9a441", justify="left")
    requirements_lbl.grid(row=4, column=0, padx=14, pady=(0, 4), sticky="w")

    msg = ctk.CTkLabel(box, textvariable=msg_var, text_color="#cc4444", justify="left")
    msg.grid(row=5, column=0, padx=14, pady=(0, 4), sticky="w")

    def update_password_requirements():
        if mode.get() != "signup":
            requirements_var.set("")
            return
        pw = password_var.get()
        missing = _password_requirements(pw)
        if not pw:
            requirements_var.set(
                "Password must have:\n- At least 8 characters\n"
                "- At least 1 capital letter\n- At least 1 number\n"
                "- At least 1 special character"
            )
        elif missing:
            requirements_var.set("Missing:\n- " + "\n- ".join(missing))
        else:
            requirements_var.set("Password is valid.")

    def set_mode(m):
        mode.set(m)
        msg_var.set("")
        username_var.set("")
        password_var.set("")
        if m == "login":
            win.title("Login")
            title.configure(text="LOGIN")
            action_btn.configure(text="LOGIN")
            switch_btn.configure(text="Don't have an account? Sign up",
                                 command=lambda: set_mode("signup"))
            requirements_var.set("")
        else:
            win.title("Sign Up")
            title.configure(text="SIGN UP")
            action_btn.configure(text="CREATE ACCOUNT")
            switch_btn.configure(text="Already have an account? Login",
                                 command=lambda: set_mode("login"))
            update_password_requirements()
        username_entry.focus()

    switch_btn = ctk.CTkButton(
        box, text="Don't have an account? Sign up",
        fg_color="transparent", hover=False, text_color="#4ea3ff",
        command=lambda: set_mode("signup")
    )
    switch_btn.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="w")

    btns = ctk.CTkFrame(win)
    btns.grid(row=2, column=0, padx=20, pady=(2, 12), sticky="ew")
    btns.grid_columnconfigure(0, weight=1)
    btns.grid_columnconfigure(1, weight=1)

    def do_login():
        u = username_var.get().strip()
        p = password_var.get().strip()
        if not u or not p:
            msg_var.set("Username and password required.")
            return
        try:
            local_login(u, p)
        except Exception as e:
            msg_var.set(str(e))
            return
        msg_var.set("")
        try:
            win.grab_release()
        except Exception:
            pass
        win.destroy()
        on_success(u)

    def do_signup():
        u = username_var.get().strip()
        p = password_var.get().strip()
        if len(u) < 3:
            msg_var.set("Username must be at least 3 characters.")
            return
        missing = _password_requirements(p)
        if missing:
            msg_var.set("Password requirements not met.")
            requirements_var.set("Missing:\n- " + "\n- ".join(missing))
            return
        try:
            local_signup(u, p)
        except Exception as e:
            msg_var.set(str(e))
            return
        msg_var.set("Account created. You can login now.")
        requirements_var.set("")
        set_mode("login")

    def action():
        if mode.get() == "login":
            do_login()
        else:
            do_signup()

    action_btn = ctk.CTkButton(btns, text="LOGIN", height=44, command=action)
    action_btn.grid(row=0, column=0, padx=(0, 8), pady=10, sticky="ew")

    cancel_btn = ctk.CTkButton(btns, text="CANCEL", height=44, command=close_all)
    cancel_btn.grid(row=0, column=1, padx=(8, 0), pady=10, sticky="ew")

    password_entry.bind("<KeyRelease>", lambda e: update_password_requirements())
    win.bind("<Return>", lambda e: action())
    username_entry.focus()
