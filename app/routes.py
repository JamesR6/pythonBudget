from flask import Blueprint, render_template, request

from . import database as db
from . import services

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def dashboard():
    con, cur = db.get_connection()

    if request.method == 'POST':
        services.handle_form_submission(cur, con, request.form)

    filename = services.get_display_filename(db.DB_PATH)
    data = services.get_dashboard_data(cur)

    db.close_connection(con)

    return render_template(
        'index.html',
        filename=filename,
        **data,
    )