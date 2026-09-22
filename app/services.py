from . import database as db

MONTHLY_LIMIT = 1000


def get_display_filename(path):
    """Turn './instance/months/y26/august.db' into 'AUGUST 2026'."""
    startIndex = path.rindex("/") + 1
    endIndex = path.rindex(".")
    yearStartIndex = path.rindex("/", 0, path.rindex("/")) + 1
    yearEndIndex = path.rindex("/")

    month_part = path[startIndex:endIndex].upper()
    year_part = "20" + path[yearStartIndex:yearEndIndex]
    return f"{month_part} {year_part}"


def handle_form_submission(cur, con, form):
    """Apply whatever add/remove action the submitted form represents."""
    day = form.get('day')
    transactionType = form.get('type')
    amount = form.get('amount')
    notes = form.get('notes')
    cash = form.get('cash')

    removePurchase = form.get('removePurchase')
    removeFood = form.get('removeFood')
    removeCash = form.get('removeCash')

    if removePurchase is not None:
        db.delete_purchase(cur, removePurchase)
    if removeFood is not None:
        db.delete_food(cur, removeFood)
    if removeCash is not None:
        db.delete_cash(cur, removeCash)

    if cash is not None:
        db.insert_cash(cur, cash)
    elif transactionType == "spent":
        db.insert_purchase(cur, day, amount, notes)
    elif transactionType == "food":
        db.insert_food(cur, day, amount, notes)

    con.commit()


def get_dashboard_data(cur):
    """Gather every total + table needed to render the dashboard."""
    totalSpent = db.get_sum(cur, "purchases")
    totalFood = db.get_sum(cur, "transfer")
    totalCash = db.get_sum(cur, "cash")
    totalLeft = round(MONTHLY_LIMIT - totalSpent, 2)

    purchaseRows = db.get_all_rows(cur, "purchases")
    foodRows = db.get_all_rows(cur, "transfer")
    cashRows = db.get_all_rows(cur, "cash", reverse=True)

    return {
        "totalSpent": totalSpent,
        "totalFood": totalFood,
        "totalCash": totalCash,
        "totalLeft": totalLeft,
        "purchaseRows": purchaseRows,
        "foodRows": foodRows,
        "cashRows": cashRows,
    }