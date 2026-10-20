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


def handle_form_submission(cur, con, form, user_id):
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
            db.delete_txn(cur, removed, user_id)

    if cash is not None:
        db.insert_txn(cur, db.CASH, day, cash, None, user_id)
    elif transactionType == "spent":
        db.insert_txn(cur, db.GENERAL, day, amount, notes, user_id)
    elif transactionType == "food":
        db.insert_txn(cur, db.SPECIFIC, day, amount, notes, user_id)

    con.commit()


def get_dashboard_data(cur, start, end, user_id):
    """Gather every total + table needed to render the dashboard."""
    totalSpent = db.get_sum(cur, db.GENERAL, start, end, user_id)
    totalFood = db.get_sum(cur, db.SPECIFIC, start, end, user_id)
    totalCash = db.get_sum(cur, db.CASH, None, None, user_id)
    totalLeft = round(MONTHLY_LIMIT - totalSpent, 2)

    return {
        "totalSpent": totalSpent,
        "totalFood": totalFood,
        "totalCash": totalCash,
        "totalLeft": totalLeft,
        "purchaseRows": db.get_rows(cur, db.GENERAL, user_id, start, end),
        "foodRows": db.get_rows(cur, db.SPECIFIC, user_id, start, end),
        "cashRows": db.get_rows(cur, db.CASH, user_id, reverse=True),
    }