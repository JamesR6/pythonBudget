import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "finance.db"
        with closing(sqlite3.connect(self.database_path)) as con:
            con.executescript(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE transactions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    kind TEXT NOT NULL,
                    txn_date TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    notes TEXT
                );
                """
            )
            con.execute(
                "INSERT INTO users(id, email, password_hash) VALUES (?, ?, ?)",
                (1, "owner@example.com", generate_password_hash("correct-password")),
            )
            con.execute(
                "INSERT INTO users(id, email, password_hash) VALUES (?, ?, ?)",
                (2, "other@example.com", generate_password_hash("other-password")),
            )
            con.execute(
                "INSERT INTO transactions(user_id, kind, txn_date, amount_cents, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (1, "General_txn", date.today().isoformat(), 1234, "owner-only"),
            )
            con.execute(
                "INSERT INTO transactions(user_id, kind, txn_date, amount_cents, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (2, "General_txn", date.today().isoformat(), 5000, "other-only"),
            )
            con.commit()

        self.database_patch = patch("app.database.DB_PATH", self.database_path)
        self.database_patch.start()
        self.addCleanup(self.temp_dir.cleanup)
        self.addCleanup(self.database_patch.stop)

        self.app = create_app(
            {"SECRET_KEY": "test-secret", "WTF_CSRF_ENABLED": False, "TESTING": True}
        )
        self.client = self.app.test_client()

    def _login(self, email="owner@example.com", password="correct-password"):
        return self.client.post(
            "/login", data={"email": email, "password": password}
        )

    def test_dashboard_requires_login(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

    def test_login_shows_only_the_signed_in_users_transactions(self):
        response = self._login()
        self.assertEqual(response.status_code, 302)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"owner-only", response.data)
        self.assertNotIn(b"other-only", response.data)

    def test_invalid_password_does_not_create_a_session(self):
        response = self._login(password="wrong-password")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password.", response.data)
        self.assertEqual(self.client.get("/").headers["Location"], "/login")

    def test_registration_creates_an_account_and_starts_a_session(self):
        response = self.client.post(
            "/register",
            data={
                "email": " New.User@Example.com ",
                "password": "a-long-registration-password",
                "confirm_password": "a-long-registration-password",
            },
        )

        self.assertEqual(response.status_code, 302)
        dashboard = self.client.get("/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertNotIn(b"owner-only", dashboard.data)
        with closing(sqlite3.connect(self.database_path)) as con:
            user = con.execute(
                "SELECT id, email, password_hash FROM users "
                "WHERE email = 'new.user@example.com'"
            ).fetchone()
        self.assertIsNotNone(user)
        self.assertGreater(user[0], 2)
        self.assertTrue(check_password_hash(user[2], "a-long-registration-password"))

    def test_registration_rejects_duplicate_email_and_mismatched_passwords(self):
        duplicate = self.client.post(
            "/register",
            data={
                "email": "OWNER@example.com",
                "password": "a-long-registration-password",
                "confirm_password": "a-long-registration-password",
            },
        )
        mismatch = self.client.post(
            "/register",
            data={
                "email": "new@example.com",
                "password": "a-long-registration-password",
                "confirm_password": "a-different-long-password",
            },
        )

        self.assertIn(b"An account with that email already exists.", duplicate.data)
        self.assertIn(b"Passwords do not match.", mismatch.data)
        self.assertEqual(self.client.get("/").headers["Location"], "/login")

    def test_posts_write_and_delete_only_for_the_signed_in_user(self):
        self._login()
        with closing(sqlite3.connect(self.database_path)) as con:
            other_transaction_id = con.execute(
                "SELECT id FROM transactions WHERE user_id = 2"
            ).fetchone()[0]

        self.client.post(
            "/",
            data={
                "day": date.today().isoformat(),
                "type": "spent",
                "amount": "2.50",
                "notes": "new-owner-transaction",
            },
        )
        self.client.post("/", data={"removePurchase": other_transaction_id})

        with closing(sqlite3.connect(self.database_path)) as con:
            self.assertEqual(
                con.execute(
                    "SELECT user_id FROM transactions WHERE notes = ?",
                    ("new-owner-transaction",),
                ).fetchone()[0],
                1,
            )
            self.assertIsNotNone(
                con.execute(
                    "SELECT id FROM transactions WHERE id = ? AND user_id = 2",
                    (other_transaction_id,),
                ).fetchone()
            )

    def test_logout_clears_the_session(self):
        self._login()
        response = self.client.post("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/").headers["Location"], "/login")

    def test_cli_initializes_user_one_without_changing_transactions(self):
        with closing(sqlite3.connect(self.database_path)) as con:
            con.execute(
                "UPDATE users SET password_hash = 'placeholder' WHERE id = 1"
            )
            transaction_count = con.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id = 1"
            ).fetchone()[0]
            con.commit()

        runner = self.app.test_cli_runner()
        result = runner.invoke(
            args=["setup-owner", "new-owner@example.com"],
            input="a-long-test-password\n" * 2,
        )

        self.assertEqual(result.exit_code, 0, result.output)
        with closing(sqlite3.connect(self.database_path)) as con:
            email, password_hash = con.execute(
                "SELECT email, password_hash FROM users WHERE id = 1"
            ).fetchone()
            self.assertEqual(email, "new-owner@example.com")
            self.assertTrue(check_password_hash(password_hash, "a-long-test-password"))
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM transactions WHERE user_id = 1"
                ).fetchone()[0],
                transaction_count,
            )

        second_attempt = runner.invoke(
            args=["setup-owner", "another@example.com"],
            input="a-long-test-password\n" * 2,
        )
        self.assertNotEqual(second_attempt.exit_code, 0)


class CsrfTests(unittest.TestCase):
    def test_login_post_requires_csrf_token(self):
        app = create_app({"SECRET_KEY": "test-secret", "TESTING": True})
        response = app.test_client().post(
            "/login", data={"email": "owner@example.com", "password": "password"}
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
