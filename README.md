<<<<<<< HEAD
# Library Management System — Libra

A beginner-friendly full-stack library management web application built with Python, Flask, SQLite, HTML, CSS, and vanilla JavaScript.

## Features

- Responsive admin workspace and dashboard with real database statistics
- Secure password hashing and session-based login
- Book catalog: create, search, edit, archive and delete
- Member registration, editing, activation/deactivation, and borrowing history
- Issue/return workflows with transactional inventory updates
- Overdue status and fine calculation (₹2 per overdue day; 14-day loan)
- Popular books and overdue reports
- CSV exports for the catalog and complete loan history
- Reservation queue with duplicate-pending protection and fulfil/cancel workflow
- Live dashboard insight charts rendered with vanilla JavaScript Canvas (no chart library)
- Low-stock and pending-reservation indicators
- Admin-only audit trail for state-changing requests (never stores passwords or form bodies)
- Basic automated tests and friendly error pages

## Technology

- Python 3.11 or newer
- Flask
- SQLite
- HTML, CSS, JavaScript
- Werkzeug password hashing
- Gunicorn for production WSGI serving

## Folder structure

```text
library-management-system/
├── frontend/
│   ├── templates/
│   └── static/
├── backend/
│   ├── app.py
│   ├── auth.py
│   ├── create_admin.py
│   ├── database.py
│   ├── models.py
│   ├── routes.py
│   ├── schema.sql
│   ├── services.py
│   ├── tests.py
│   ├── validators.py
│   ├── requirements.txt
│   └── instance/
├── .env.example
├── .gitignore
├── Procfile
└── README.md
```

## Run on Windows with VS Code

Open PowerShell in the extracted project root.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Create an administrator account:

```powershell
python backend\create_admin.py
```

Choose a username and a password of at least 10 characters when prompted. Do not share these credentials.

Start the application:

```powershell
python backend\app.py
```

Open http://127.0.0.1:5000 in your browser.

If PowerShell blocks activation, use this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run tests

From the project root, after installing requirements:

```powershell
python -m unittest discover -s backend -p "tests.py" -v
```

## Database

The app creates its SQLite schema automatically. By default the database is stored at `backend/instance/library.db`. Set `DATABASE_PATH` to a persistent writable location when deploying.

Back up the database before upgrades or destructive maintenance. Demo data is not automatically inserted.

## GitHub

Create a new empty repository on GitHub, then run these commands from the project root:

```powershell
git init
git add .
git status
git commit -m "Build Library Management System"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the remote URL with your own repository URL. Review `git status` before committing; never commit `.env`, secrets, a real database, or user data.

## Deployment notes

A `Procfile` is included for a platform that supports Gunicorn. Configure the start command as `gunicorn --chdir backend app:app`, and set a strong random `SECRET_KEY` in the hosting provider's environment variables. Set `FLASK_ENV=production` and use HTTPS.

**Persistence warning:** SQLite requires a persistent writable filesystem. Many free cloud hosts use ephemeral storage, which can erase local database files on restart or redeploy. Configure a persistent disk and set `DATABASE_PATH` to a file path on that disk, or adapt the app to a managed database. Do not use ephemeral storage for real library records.

For production, also review backups, access controls, HTTPS, CSRF protection, logging, and database concurrency. This starter is a learning project and should receive a security review before being used for sensitive or high-volume real-world records.

## Environment variables

- `SECRET_KEY`: required strong random value for deployment
- `DATABASE_PATH`: optional database file path
- `FLASK_DEBUG`: set to `1` only for local development
- `FLASK_ENV`: set to `production` on production hosting
- `TRUST_PROXY`: set to `1` only when deployed behind a trusted reverse proxy

`.env.example` documents the expected values; environment variables must be configured in the shell or hosting dashboard. The app does not automatically load `.env`.

## Advanced modules added in this edition

- **Reservations:** staff can queue a request for an active member and fulfil it by issuing the selected book, or cancel it.
- **Audit trail:** admin-only page captures route, actor, method, time and HTTP status for state-changing requests. Request bodies and credentials are not recorded.
- **Dashboard analytics:** category distribution and monthly circulation charts use browser Canvas and vanilla JavaScript; no additional package is required.
- **Operational indicators:** pending reservations and low-stock titles are visible on the dashboard.
- **Loan CSV export:** export circulation history for spreadsheet analysis.
- **Additive database schema:** new tables are created with `CREATE TABLE IF NOT EXISTS`; existing books, members, users and loans are not dropped. Back up your database before replacing project files.

## Security and production checklist

This is an educational project, not a security-audited production system. Before exposing it publicly, add CSRF tokens to all state-changing forms, rate-limit login attempts, review role permissions, configure a unique strong `SECRET_KEY`, enforce HTTPS, set secure cookies, and plan encrypted backups. Audit entries record route metadata only, not form values. Keep debug mode disabled in deployment.

Fine rate and loan duration are simple policy constants in `backend/services.py`. Email reminders, password reset, barcode scanning and automated reservation notifications are not implemented in this edition.
=======
# library_management_system
>>>>>>> origin/main
