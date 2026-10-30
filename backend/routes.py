import csv
import io
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, Response
from database import get_db
from auth import verify_user, login_required, admin_required
from validators import required, positive_int, optional_email
from services import issue_book, return_book

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.login"))

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = verify_user(request.form.get("username", ""), request.form.get("password", ""))
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Welcome back!", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))

@bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    stats = {
        "titles": db.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "copies": db.execute("SELECT COALESCE(SUM(total_copies),0) FROM books").fetchone()[0],
        "available": db.execute("SELECT COALESCE(SUM(available_copies),0) FROM books").fetchone()[0],
        "members": db.execute("SELECT COUNT(*) FROM members WHERE active=1").fetchone()[0],
        "loans": db.execute("SELECT COUNT(*) FROM loans WHERE returned_at IS NULL").fetchone()[0],
        "overdue": db.execute("SELECT COUNT(*) FROM loans WHERE returned_at IS NULL AND due_date < ?", (date.today().isoformat(),)).fetchone()[0],
        "low_stock": db.execute("SELECT COUNT(*) FROM books WHERE available_copies <= 1 AND total_copies > 0").fetchone()[0],
        "reservations": db.execute("SELECT COUNT(*) FROM reservations WHERE status='queued'").fetchone()[0],
    }
    recent = db.execute("""SELECT l.id, b.title, m.full_name, l.issued_at, l.due_date, l.returned_at
        FROM loans l JOIN books b ON b.id=l.book_id JOIN members m ON m.id=l.member_id
        ORDER BY l.id DESC LIMIT 6""").fetchall()
    categories = db.execute("SELECT category, COUNT(*) AS count FROM books GROUP BY category ORDER BY count DESC, category LIMIT 8").fetchall()
    monthly = db.execute("SELECT substr(issued_at,1,7) AS month, COUNT(*) AS count FROM loans WHERE issued_at >= date('now','-5 months') GROUP BY month ORDER BY month").fetchall()
    return render_template("dashboard.html", stats=stats, recent=recent, categories=categories, monthly=monthly, today=date.today().isoformat())

@bp.route("/books")
@login_required
def books():
    q = request.args.get("q", "").strip()
    db = get_db()
    rows = db.execute("""SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ? OR COALESCE(isbn,'') LIKE ? OR category LIKE ?
        ORDER BY title COLLATE NOCASE""", tuple([f"%{q}%"]*4)).fetchall()
    return render_template("books.html", books=rows, q=q)

@bp.route("/books/new", methods=["GET", "POST"])
@admin_required
def book_new():
    if request.method == "POST":
        try:
            title = required(request.form.get("title"), "Title")
            author = required(request.form.get("author"), "Author")
            category = required(request.form.get("category"), "Category")
            total = positive_int(request.form.get("total_copies"), "Total copies", 1)
            year_raw = request.form.get("publication_year", "").strip()
            year = positive_int(year_raw, "Publication year", 0) if year_raw else None
            isbn = request.form.get("isbn", "").strip() or None
            db = get_db()
            db.execute("""INSERT INTO books
                (isbn,title,author,category,publisher,publication_year,shelf_location,total_copies,available_copies,description)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (isbn,title,author,category,request.form.get("publisher","").strip(),year,
                 request.form.get("shelf_location","").strip(),total,total,request.form.get("description","").strip()))
            db.commit()
            flash("Book added successfully.", "success")
            return redirect(url_for("main.books"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            if "UNIQUE constraint failed: books.isbn" in str(e):
                flash("That ISBN already exists.", "danger")
            else:
                current_app.logger.exception("Could not add book")
                flash("Could not save this book. Check the fields and try again.", "danger")
    return render_template("book_form.html", book=None)

@bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@admin_required
def book_edit(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    if not book:
        flash("Book not found.", "danger")
        return redirect(url_for("main.books"))
    if request.method == "POST":
        try:
            title = required(request.form.get("title"), "Title")
            author = required(request.form.get("author"), "Author")
            category = required(request.form.get("category"), "Category")
            total = positive_int(request.form.get("total_copies"), "Total copies", 1)
            issued = book["total_copies"] - book["available_copies"]
            if total < issued:
                raise ValueError(f"Total copies cannot be less than the {issued} copies currently on loan.")
            year_raw = request.form.get("publication_year", "").strip()
            year = positive_int(year_raw, "Publication year", 0) if year_raw else None
            isbn = request.form.get("isbn", "").strip() or None
            db.execute("""UPDATE books SET isbn=?,title=?,author=?,category=?,publisher=?,publication_year=?,
                shelf_location=?,total_copies=?,available_copies=?,description=? WHERE id=?""",
                (isbn,title,author,category,request.form.get("publisher","").strip(),year,
                 request.form.get("shelf_location","").strip(),total,total-issued,
                 request.form.get("description","").strip(),book_id))
            db.commit()
            flash("Book updated successfully.", "success")
            return redirect(url_for("main.books"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Could not update this book. Check that the ISBN is unique.", "danger")
    return render_template("book_form.html", book=book)

@bp.route("/books/<int:book_id>/delete", methods=["POST"])
@admin_required
def book_delete(book_id):
    db = get_db()
    active = db.execute("SELECT COUNT(*) FROM loans WHERE book_id=? AND returned_at IS NULL", (book_id,)).fetchone()[0]
    history = db.execute("SELECT COUNT(*) FROM loans WHERE book_id=?", (book_id,)).fetchone()[0]
    if active:
        flash("This book has active loans and cannot be deleted.", "danger")
    elif history:
        db.execute("UPDATE books SET total_copies=0, available_copies=0 WHERE id=?", (book_id,))
        db.commit()
        flash("Book archived because it has transaction history.", "success")
    else:
        db.execute("DELETE FROM books WHERE id=?", (book_id,))
        db.commit()
        flash("Book deleted.", "success")
    return redirect(url_for("main.books"))

@bp.route("/members")
@login_required
def members():
    q = request.args.get("q", "").strip()
    rows = get_db().execute("""SELECT m.*, (SELECT COUNT(*) FROM loans l WHERE l.member_id=m.id AND l.returned_at IS NULL) AS active_loans
        FROM members m WHERE full_name LIKE ? OR member_code LIKE ? OR COALESCE(email,'') LIKE ?
        ORDER BY full_name COLLATE NOCASE""", (f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
    return render_template("members.html", members=rows, q=q)

@bp.route("/members/new", methods=["GET", "POST"])
@admin_required
def member_new():
    if request.method == "POST":
        try:
            code = required(request.form.get("member_code"), "Member ID")
            name = required(request.form.get("full_name"), "Full name")
            email = optional_email(request.form.get("email"))
            db = get_db()
            db.execute("INSERT INTO members (member_code,full_name,email,phone,course) VALUES (?,?,?,?,?)",
                (code,name,email,request.form.get("phone","").strip(),request.form.get("course","").strip()))
            db.commit()
            flash("Member registered successfully.", "success")
            return redirect(url_for("main.members"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Could not register member. Member ID and email must be unique.", "danger")
    return render_template("member_form.html", member=None)

@bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@admin_required
def member_edit(member_id):
    db = get_db()
    member = db.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("main.members"))
    if request.method == "POST":
        try:
            code = required(request.form.get("member_code"), "Member ID")
            name = required(request.form.get("full_name"), "Full name")
            email = optional_email(request.form.get("email"))
            active = 1 if request.form.get("active") == "on" else 0
            db.execute("UPDATE members SET member_code=?,full_name=?,email=?,phone=?,course=?,active=? WHERE id=?",
                (code,name,email,request.form.get("phone","").strip(),request.form.get("course","").strip(),active,member_id))
            db.commit()
            flash("Member updated successfully.", "success")
            return redirect(url_for("main.members"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Could not update member. Member ID and email must be unique.", "danger")
    return render_template("member_form.html", member=member)

@bp.route("/members/<int:member_id>/history")
@login_required
def member_history(member_id):
    db = get_db()
    member = db.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for("main.members"))
    loans = db.execute("""SELECT l.*, b.title FROM loans l JOIN books b ON b.id=l.book_id
        WHERE l.member_id=? ORDER BY l.id DESC""", (member_id,)).fetchall()
    return render_template("member_history.html", member=member, loans=loans)

@bp.route("/loans")
@login_required
def loans():
    status = request.args.get("status", "active")
    where = "l.returned_at IS NULL" if status == "active" else ("l.returned_at IS NOT NULL" if status == "returned" else "1=1")
    rows = get_db().execute(f"""SELECT l.*, b.title, m.full_name, m.member_code
        FROM loans l JOIN books b ON b.id=l.book_id JOIN members m ON m.id=l.member_id
        WHERE {where} ORDER BY l.id DESC""").fetchall()
    return render_template("loans.html", loans=rows, status=status, today=date.today().isoformat())

@bp.route("/loans/issue", methods=["GET", "POST"])
@admin_required
def issue():
    db = get_db()
    if request.method == "POST":
        try:
            book_id = positive_int(request.form.get("book_id"), "Book", 1)
            member_id = positive_int(request.form.get("member_id"), "Member", 1)
            issue_book(book_id, member_id)
            flash("Book issued successfully. Standard loan period: 14 days.", "success")
            return redirect(url_for("main.loans"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            current_app.logger.exception("Issue operation failed")
            flash("Could not issue this book. Please check the selected records.", "danger")
    books = db.execute("SELECT * FROM books WHERE available_copies>0 ORDER BY title").fetchall()
    members = db.execute("SELECT * FROM members WHERE active=1 ORDER BY full_name").fetchall()
    return render_template("issue_book.html", books=books, members=members)

@bp.route("/loans/<int:loan_id>/return", methods=["POST"])
@admin_required
def return_loan(loan_id):
    try:
        fine = return_book(loan_id)
        flash(f"Book returned successfully. Overdue fine: ₹{fine:.2f}. Policy: ₹2 per overdue day.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        current_app.logger.exception("Return operation failed")
        flash("Could not return this book.", "danger")
    return redirect(url_for("main.loans"))

@bp.route("/reports")
@login_required
def reports():
    db = get_db()
    popular = db.execute("""SELECT b.title, b.author, COUNT(l.id) AS borrow_count
        FROM books b LEFT JOIN loans l ON l.book_id=b.id
        GROUP BY b.id ORDER BY borrow_count DESC, b.title LIMIT 10""").fetchall()
    overdue = db.execute("""SELECT l.id, b.title, m.full_name, m.member_code, l.due_date,
        CAST(julianday(?) - julianday(l.due_date) AS INTEGER) AS days_overdue
        FROM loans l JOIN books b ON b.id=l.book_id JOIN members m ON m.id=l.member_id
        WHERE l.returned_at IS NULL AND l.due_date < ? ORDER BY l.due_date""",
        (date.today().isoformat(), date.today().isoformat())).fetchall()
    return render_template("reports.html", popular=popular, overdue=overdue)

@bp.route("/reports/books.csv")
@login_required
def export_books():
    rows = get_db().execute("SELECT isbn,title,author,category,total_copies,available_copies FROM books ORDER BY title").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ISBN","Title","Author","Category","Total copies","Available copies"])
    writer.writerows([tuple(row) for row in rows])
    return Response("\ufeff"+output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":"attachment; filename=library-books.csv"})

@bp.route("/health")
def health():
    return {"status": "ok"}


@bp.route("/reservations", methods=["GET", "POST"])
@login_required
def reservations():
    db = get_db()
    if request.method == "POST":
        try:
            book_id = positive_int(request.form.get("book_id"), "Book", 1)
            member_id = positive_int(request.form.get("member_id"), "Member", 1)
            book = db.execute("SELECT id FROM books WHERE id=?", (book_id,)).fetchone()
            member = db.execute("SELECT id FROM members WHERE id=? AND active=1", (member_id,)).fetchone()
            if not book or not member:
                raise ValueError("Choose an existing book and an active member.")
            duplicate = db.execute("SELECT id FROM reservations WHERE book_id=? AND member_id=? AND status='queued'", (book_id,member_id)).fetchone()
            if duplicate:
                raise ValueError("This member already has a pending reservation for this book.")
            db.execute("INSERT INTO reservations(book_id,member_id,notes) VALUES(?,?,?)", (book_id,member_id,request.form.get("notes", "").strip()))
            db.commit()
            flash("Reservation added to the queue.", "success")
            return redirect(url_for("main.reservations"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            current_app.logger.exception("Reservation could not be created")
            flash("Could not create reservation. Please check the selected records.", "danger")
    rows = db.execute("SELECT r.*, b.title, b.available_copies, m.full_name, m.member_code FROM reservations r JOIN books b ON b.id=r.book_id JOIN members m ON m.id=r.member_id ORDER BY CASE r.status WHEN 'queued' THEN 0 ELSE 1 END, r.id DESC").fetchall()
    books = db.execute("SELECT id,title,available_copies FROM books ORDER BY title").fetchall()
    members = db.execute("SELECT id,full_name,member_code FROM members WHERE active=1 ORDER BY full_name").fetchall()
    return render_template("reservations.html", reservations=rows, books=books, members=members)

@bp.route("/reservations/<int:reservation_id>/<action>", methods=["POST"])
@admin_required
def reservation_action(reservation_id, action):
    if action not in ("fulfill", "cancel"):
        flash("Unknown reservation action.", "danger")
        return redirect(url_for("main.reservations"))
    db = get_db()
    row = db.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
    if not row or row["status"] != "queued":
        flash("Only pending reservations can be updated.", "warning")
    elif action == "fulfill" and row["status"] == "queued":
        try:
            issue_book(row["book_id"], row["member_id"])
            db.execute("UPDATE reservations SET status='fulfilled' WHERE id=?", (reservation_id,))
            db.commit()
            flash("Reservation fulfilled and book issued.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            db.rollback()
            current_app.logger.exception("Could not fulfill reservation")
            flash("Could not fulfill reservation.", "danger")
    else:
        db.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (reservation_id,))
        db.commit()
        flash("Reservation cancelled.", "success")
    return redirect(url_for("main.reservations"))

@bp.route("/reports/loans.csv")
@login_required
def export_loans():
    rows = get_db().execute("SELECT l.id,b.title,m.member_code,m.full_name,l.issued_at,l.due_date,l.returned_at,l.fine_amount FROM loans l JOIN books b ON b.id=l.book_id JOIN members m ON m.id=l.member_id ORDER BY l.id DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Loan ID","Book","Member ID","Member","Issued","Due","Returned","Fine (INR)"])
    writer.writerows([tuple(row) for row in rows])
    return Response("\ufeff"+output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=library-loans.csv"})

@bp.route("/audit")
@admin_required
def audit():
    rows = get_db().execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 200").fetchall()
    return render_template("audit.html", logs=rows)
