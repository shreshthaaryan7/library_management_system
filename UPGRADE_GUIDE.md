# Libra Advanced Edition — Upgrade Guide

## What's new

- Reservation queue for book requests, with pending duplicate checks and fulfil/cancel actions.
- Dashboard category and monthly-circulation charts built with the existing vanilla JavaScript and Canvas.
- Dashboard warnings for low-stock titles and pending reservations.
- CSV export for the complete loan history.
- Admin-only audit trail for state-changing HTTP requests. It stores actor, route, method, timestamp and status only; it does not store form bodies or passwords.
- Additive SQLite schema changes: `reservations` and `audit_logs` are created if missing.

## Keep your existing records

1. Stop the running Flask server with `Ctrl+C`.
2. Make a copy of `backend/instance/library.db` before changing project files.
3. Extract this advanced ZIP into a **new folder**. Do not overwrite the old project.
4. Install the same dependencies listed in `backend/requirements.txt` in your virtual environment.
5. Run `python backend/app.py`. The application runs `CREATE TABLE IF NOT EXISTS` statements when it starts, which creates the two new tables without dropping existing books, members, users, or loans.
6. Sign in with your existing admin account. Your existing credentials should remain in the original database; this new project folder starts with a fresh database unless you copy your database backup into its `backend/instance/` folder.

## Run on Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python backend\app.py
```

Open `http://127.0.0.1:5000`.

## Validation note

Python files compile and the SQL schema executes successfully. The full Flask unit test suite should be run on your own machine after installing requirements:

```powershell
python -m unittest discover -s backend -p "tests.py" -v
```

This is an educational project. Before public production deployment, add CSRF tokens to every state-changing form and perform a security review.
