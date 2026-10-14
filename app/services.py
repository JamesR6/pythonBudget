from datetime import date, datetime, timedelta

from . import database as db

MONTHLY_LIMIT = 1000


def get_date_range(args):
    """Read start/end (YYYY-MM-DD) from the query string; default to this month."""
    today = date.today()
    first = today.replace(day=1)
    next_month = (first + timedelta(days=32)).replace(day=1)
    last = next_month - timedelta(days=1)

    start = _valid_date(args.get('start')) or first.isoformat()
    end = _valid_date(args.get('end')) or last.isoformat()
    if start > end:
        start, end = end, start
    return start, end


def _valid_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        return None


def get_display_range(start, end):
    return f"{start} to {end}"


def handle_form_submission(cur, con, form):
    """Apply whatever add/remove action the submitted form represents."""
    day = _valid_date(form.get('day')) or date.today().isoformat()
    transactionType = form.get('type')
    amount = form.get('amount')
    notes = form.get('notes')
    cash = form.get('cash')

    removePurchase = form.get('removePurchase')
    removeFood = form.get('removeFood')
    removeCash = form.get('removeCash')

    for removed in (removePurchase, removeFood, removeCash):
        if removed is not None:
            db.delete_txn(cur, removed)

    if cash is not None:
        db.insert_txn(cur, db.CASH, day, cash, None)
    elif transactionType == "spent":
        db.insert_txn(cur, db.GENERAL, day, amount, notes)
    elif transactionType == "food":
        db.insert_txn(cur, db.SPECIFIC, day, amount, notes)

    con.commit()


def get_dashboard_data(cur, start, end):
    """Gather every total + table needed to render the dashboard."""
    totalSpent = db.get_sum(cur, db.GENERAL, start, end)
    totalFood = db.get_sum(cur, db.SPECIFIC, start, end)
    totalCash = db.get_sum(cur, db.CASH, start, end)
    totalLeft = round(MONTHLY_LIMIT - totalSpent, 2)

    return {
        "totalSpent": totalSpent,
        "totalFood": totalFood,
        "totalCash": totalCash,
        "totalLeft": totalLeft,
        "purchaseRows": db.get_rows(cur, db.GENERAL, start, end),
        "foodRows": db.get_rows(cur, db.SPECIFIC, start, end),
        "cashRows": db.get_rows(cur, db.CASH, start, end, reverse=True),
    }
