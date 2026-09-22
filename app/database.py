import sqlite3

# Path to the active month's database.
# Later you could make this dynamic (e.g. based on today's date or a URL param)
# instead of hardcoding it here.
DB_PATH = "./instance/months/y26/august.db"


def get_connection(path=DB_PATH):
    """Open a connection + cursor to the given db file."""
    con = sqlite3.connect(path)
    cur = con.cursor()
    return con, cur


def close_connection(con):
    con.close()


# ---- Deletes ----

def delete_purchase(cur, id):
    cur.execute("DELETE FROM purchases WHERE id = ?", (id,))


def delete_food(cur, id):
    cur.execute("DELETE FROM transfer WHERE id = ?", (id,))


def delete_cash(cur, id):
    cur.execute("DELETE FROM cash WHERE id = ?", (id,))


# ---- Inserts ----

def insert_purchase(cur, day, amount, notes):
    cur.execute(
        "INSERT INTO purchases(day, amount, notes) VALUES (?,?,?)",
        (day, amount, notes),
    )


def insert_food(cur, day, amount, notes):
    cur.execute(
        "INSERT INTO transfer(day, amount, notes) VALUES (?,?,?)",
        (day, amount, notes),
    )


def insert_cash(cur, amount):
    cur.execute("INSERT INTO cash(amount) VALUES (?)", (amount,))


# ---- Reads ----

def get_sum(cur, table):
    cur.execute(f"SELECT SUM(amount) FROM {table}")
    result = cur.fetchone()[0]
    return round(result, 2) if result is not None else 0


def get_all_rows(cur, table, reverse=False):
    cur.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    return rows[::-1] if reverse else rows