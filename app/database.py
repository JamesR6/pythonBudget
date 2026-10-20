import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "finance.db"

GENERAL = "General_txn"    # shown as "Purchases" in the UI
SPECIFIC = "Specific_txn"  # shown as "Food" in the UI
CASH = "cash"


def get_connection(path=None):
    """Open a connection + cursor to the finance database."""
    if path is None:
        path = DB_PATH
    con = sqlite3.connect(path)
    cur = con.cursor()
    return con, cur


def close_connection(con):
    con.close()


def _dollars(cents):
    return round(cents / 100, 2)


def _cents(amount):
    return round(float(amount or 0) * 100)


def get_user_by_email(cur, email):
    cur.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
    )
    return cur.fetchone()


def create_user(cur, email, password_hash):
    cur.execute(
        "INSERT INTO users(email, password_hash) VALUES (?, ?)",
        (email, password_hash),
    )
    return cur.lastrowid


def initialize_legacy_user(cur, email, password_hash):
    """Set credentials for user 1 only while its password is still the placeholder."""
    cur.execute(
        "UPDATE users SET email = ?, password_hash = ? "
        "WHERE id = 1 AND password_hash = 'placeholder'",
        (email, password_hash),
    )
    return cur.rowcount == 1


# ---- Deletes ----

def delete_txn(cur, id, user_id):
    cur.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?", (id, user_id)
    )


# ---- Inserts ----

def insert_txn(cur, kind, txn_date, amount, notes, user_id):
    cur.execute(
        "INSERT INTO transactions(user_id, kind, txn_date, amount_cents, notes) "
        "VALUES (?,?,?,?,?)",
        (user_id, kind, txn_date, _cents(amount), notes),
    )


# ---- Reads ----

def get_sum(cur, kind, start, end, user_id):

    if (start != None and end != None):
        cur.execute(
            "SELECT SUM(amount_cents) FROM transactions "
            "WHERE user_id = ? AND kind = ? AND txn_date BETWEEN ? AND ?",
            (user_id, kind, start, end),
        )
    else:
        cur.execute(
            "SELECT SUM(amount_cents) FROM transactions "
            "WHERE user_id = ? AND kind = ?",
            (user_id, kind),
        )

    result = cur.fetchone()[0]
    return _dollars(result) if result is not None else 0


def get_rows(cur, kind, user_id, start=None, end=None, reverse=False):
    """Return (id, txn_date, amount_in_dollars, notes) rows, optionally limited to a date range."""
    query = (
        "SELECT id, txn_date, amount_cents, notes FROM transactions "
        "WHERE user_id = ? AND kind = ?"
    )
    params = [user_id, kind]

    if start is not None:
        query += " AND txn_date >= ?"
        params.append(start)
    if end is not None:
        query += " AND txn_date <= ?"
        params.append(end)

    query += " ORDER BY txn_date, id"
    cur.execute(query, params)

    rows = [(r[0], r[1], _dollars(r[2]), r[3] or "") for r in cur.fetchall()]
    return rows[::-1] if reverse else rows
