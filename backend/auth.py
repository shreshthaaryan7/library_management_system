from functools import wraps
from flask import flash, redirect, session, url_for, request
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db

def create_admin(username, password):
    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")
    db = get_db()
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
        (username.strip(), generate_password_hash(password)),
    )
    db.commit()

def verify_user(username, password):
    user = get_db().execute(
        "SELECT * FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("main.login"))
        if session.get("role") != "admin":
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for("main.dashboard"))
        return view(*args, **kwargs)
    return wrapped
