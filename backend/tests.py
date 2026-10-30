import os
import tempfile
import unittest
from app import app
from database import init_db, get_db
from auth import create_admin
from services import issue_book, return_book

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.config.update(TESTING=True, SECRET_KEY="test-secret", DATABASE_PATH=os.path.join(self.temp.name,"test.db"))
        self.ctx = app.app_context()
        self.ctx.push()
        init_db()
        create_admin("testadmin", "test-password-123")
        db = get_db()
        db.execute("INSERT INTO books (title,author,category,total_copies,available_copies) VALUES ('Test Book','Test Author','Testing',1,1)")
        db.execute("INSERT INTO members (member_code,full_name,email) VALUES ('M001','Test Member','test@example.com')")
        db.commit()
        self.client = app.test_client()

    def tearDown(self):
        from database import close_db
        close_db()
        self.ctx.pop()
        self.temp.cleanup()

    def login(self):
        return self.client.post("/login", data={"username":"testadmin","password":"test-password-123"}, follow_redirects=True)

    def test_login_and_dashboard(self):
        self.login()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)

    def test_issue_and_return(self):
        loan_id = issue_book(1, 1)
        db = get_db()
        self.assertEqual(db.execute("SELECT available_copies FROM books WHERE id=1").fetchone()[0], 0)
        return_book(loan_id)
        self.assertEqual(db.execute("SELECT available_copies FROM books WHERE id=1").fetchone()[0], 1)

    def test_unavailable_book_cannot_be_issued(self):
        issue_book(1, 1)
        with self.assertRaises(ValueError):
            issue_book(1, 1)

    def test_duplicate_return_is_rejected(self):
        loan_id = issue_book(1, 1)
        return_book(loan_id)
        with self.assertRaises(ValueError):
            return_book(loan_id)

    def test_unauthenticated_dashboard_redirects(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)

    def test_reservations_page_loads_for_admin(self):
        self.login()
        response = self.client.get("/reservations")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reservation queue", response.data)

    def test_new_schema_tables_exist(self):
        db = get_db()
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        self.assertIn("reservations", names)
        self.assertIn("audit_logs", names)

if __name__ == "__main__":
    unittest.main()
