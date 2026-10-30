import getpass
from app import app
from database import get_db
from auth import create_admin

with app.app_context():
    username = input("Choose admin username: ").strip()
    password = getpass.getpass("Choose admin password (minimum 10 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    try:
        create_admin(username, password)
        print("Admin account created. Keep your credentials safe.")
    except Exception as exc:
        raise SystemExit(f"Could not create admin: {exc}")
