from flask import Blueprint, render_template, request

from . import database as db
from . import services

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def dashboard():
    con, cur = db.get_connection()

    if request.method == 'POST':
        services.handle_form_submission(cur, con, request.form)

    start, end = services.get_date_range(request.args)
    data = services.get_dashboard_data(cur, start, end)

    db.close_connection(con)

    return render_template(
        'index.html',
        start=start,
        end=end,
        filename=services.get_display_range(start, end),
        **data,
    )
