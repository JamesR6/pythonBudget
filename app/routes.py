import sqlite3
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import database as db
from . import services
from . import _valid_email

main = Blueprint('main', __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            session.clear()
            flash("Please log in to view your budget.", "error")
            return redirect(url_for("main.login"))
        return view(user_id, *args, **kwargs)

    return wrapped


@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        con, cur = db.get_connection()
        try:
            user = db.get_user_by_email(cur, email)
        finally:
            db.close_connection(con)

        valid_password = False
        if user is not None:
            try:
                valid_password = check_password_hash(user[2], password)
            except ValueError:
                # The existing account may not have been initialized with a hash yet.
                valid_password = False

        if valid_password:
            session.clear()
            session["user_id"] = user[0]
            return redirect(url_for("main.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirm_password", "")

        if not _valid_email(email):
            flash("Enter a valid email address.", "error")
        elif len(password) < 12:
            flash("Password must be at least 12 characters.", "error")
        elif password != confirmation:
            flash("Passwords do not match.", "error")
        else:
            con, cur = db.get_connection()
            try:
                user_id = db.create_user(
                    cur, email, generate_password_hash(password)
                )
                con.commit()
            except sqlite3.IntegrityError:
                con.rollback()
                flash("An account with that email already exists.", "error")
            else:
                session.clear()
                session["user_id"] = user_id
                flash("Your account has been created.", "success")
                return redirect(url_for("main.dashboard"))
            finally:
                db.close_connection(con)

    return render_template("register.html")


@main.route("/logout", methods=["POST"])
@login_required
def logout(_user_id):
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))


@main.route('/', methods=['GET', 'POST'])
@login_required
def dashboard(user_id):
    con, cur = db.get_connection()
    try:
        if request.method == 'POST':
            services.handle_form_submission(cur, con, request.form, user_id)

        start, end = services.get_date_range(request.args)
        data = services.get_dashboard_data(cur, start, end, user_id)

        return render_template(
            'index.html',
            start=start,
            end=end,
            filename=services.get_display_range(start, end),
            **data,
        )
    finally:
        db.close_connection(con)
