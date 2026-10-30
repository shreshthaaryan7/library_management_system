from datetime import date, timedelta
from database import get_db

def issue_book(book_id, member_id, loan_days=14):
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        member = db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if not book:
            raise ValueError("Book not found.")
        if not member or not member["active"]:
            raise ValueError("Choose an active member.")
        if book["available_copies"] < 1:
            raise ValueError("No copies of this book are currently available.")
        due = date.today() + timedelta(days=loan_days)
        db.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book_id,))
        cur = db.execute(
            "INSERT INTO loans (book_id, member_id, issued_at, due_date) VALUES (?, ?, ?, ?)",
            (book_id, member_id, date.today().isoformat(), due.isoformat()),
        )
        db.commit()
        return cur.lastrowid
    except Exception:
        db.rollback()
        raise

def return_book(loan_id, daily_fine=2.0):
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        loan = db.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        if not loan:
            raise ValueError("Loan record not found.")
        if loan["returned_at"]:
            raise ValueError("This book has already been returned.")
        today = date.today()
        overdue_days = max(0, (today - date.fromisoformat(loan["due_date"])).days)
        fine = round(overdue_days * daily_fine, 2)
        db.execute(
            "UPDATE loans SET returned_at = ?, fine_amount = ? WHERE id = ?",
            (today.isoformat(), fine, loan_id),
        )
        db.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id = ?",
            (loan["book_id"],),
        )
        db.commit()
        return fine
    except Exception:
        db.rollback()
        raise
