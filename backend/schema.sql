CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin', 'librarian')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    publisher TEXT DEFAULT '',
    publication_year INTEGER,
    shelf_location TEXT DEFAULT '',
    total_copies INTEGER NOT NULL DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER NOT NULL DEFAULT 1 CHECK (available_copies >= 0),
    description TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (available_copies <= total_copies)
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT DEFAULT '',
    course TEXT DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    issued_at TEXT NOT NULL,
    due_date TEXT NOT NULL,
    returned_at TEXT,
    fine_amount REAL NOT NULL DEFAULT 0 CHECK (fine_amount >= 0),
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_members_name ON members(full_name);
CREATE INDEX IF NOT EXISTS idx_loans_due_returned ON loans(due_date, returned_at);


-- Advanced modules: reservations and append-only operational audit trail.
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    reserved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','fulfilled','cancelled')),
    notes TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_reservations_status_date ON reservations(status, reserved_at);
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL DEFAULT 'anonymous',
    action TEXT NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER NOT NULL DEFAULT 200,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
