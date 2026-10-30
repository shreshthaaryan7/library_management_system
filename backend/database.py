import sqlite3
from pathlib import Path
from flask import current_app, g

def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE_PATH"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(str(db_path), timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db_path = Path(current_app.config["DATABASE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path))
    db.execute("PRAGMA foreign_keys = ON")
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    db.executescript(schema)
    db.commit()
    db.close()

def register_db_hooks(app):
    app.teardown_appcontext(close_db)
