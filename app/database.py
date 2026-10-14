import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "finance.db"

# No auth yet; every query is scoped to this user.
DEFAULT_USER_ID = 1

GENERAL = "General_txn"    # shown as "Purchases" in the UI
SPECIFIC = "Specific_txn"  # shown as "Food" in the UI
CASH = "cash"


def get_connection(path=DB_PATH):
    """Open a connection + cursor to the finance database."""
    con = sqlite3.connect(path)
    cur = con.cursor()
    return con, cur


def close_connection(con):
    con.close()


def _dollars(cents):
    return round(cents / 100, 2)


def _cents(amount):
    return round(float(amount or 0) * 100)


# ---- Deletes ----

def delete_txn(cur, id, user_id=DEFAULT_USER_ID):
    cur.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?", (id, user_id)
    )


# ---- Inserts ----

def insert_txn(cur, kind, txn_date, amount, notes, user_id=DEFAULT_USER_ID):
    cur.execute(
        "INSERT INTO transactions(user_id, kind, txn_date, amount_cents, notes) "
        "VALUES (?,?,?,?,?)",
        (user_id, kind, txn_date, _cents(amount), notes),
    )


# ---- Reads ----

def get_sum(cur, kind, start, end, user_id=DEFAULT_USER_ID):
    cur.execute(
        "SELECT SUM(amount_cents) FROM transactions "
        "WHERE user_id = ? AND kind = ? AND txn_date BETWEEN ? AND ?",
        (user_id, kind, start, end),
    )
    result = cur.fetchone()[0]
    return _dollars(result) if result is not None else 0


def get_rows(cur, kind, start=None, end=None, reverse=False, user_id=DEFAULT_USER_ID):
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
