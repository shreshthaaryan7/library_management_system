import os
from datetime import date
from pathlib import Path
from flask import Flask, render_template, request, session, g
from werkzeug.middleware.proxy_fix import ProxyFix
from database import init_db, register_db_hooks
from routes import bp

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

app = Flask(
    __name__,
    template_folder=str(PROJECT_DIR / "frontend" / "templates"),
    static_folder=str(PROJECT_DIR / "frontend" / "static"),
    static_url_path="/static",
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-before-deployment")
app.config["DATABASE_PATH"] = os.environ.get(
    "DATABASE_PATH", str(BASE_DIR / "instance" / "library.db")
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"

if os.environ.get("TRUST_PROXY") == "1":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.register_blueprint(bp)
register_db_hooks(app)

@app.before_request
def capture_audit_actor():
    g.audit_actor = session.get("username", "anonymous")

@app.after_request
def write_audit_log(response):
    # Record route metadata only; never store request bodies or credentials.
    if request.endpoint and request.endpoint != "static" and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        try:
            from database import get_db
            db = get_db()
            db.execute("INSERT INTO audit_logs(actor, action, path, method, status_code) VALUES(?,?,?,?,?)",
                       (getattr(g, "audit_actor", "anonymous"), request.endpoint, request.path[:300], request.method, response.status_code))
            db.commit()
        except Exception:
            app.logger.exception("Could not write audit event")
    return response

@app.context_processor
def inject_app_name():
    return {"app_name": "Library Management System", "current_date": date.today().strftime("%d %b %Y")}

@app.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
