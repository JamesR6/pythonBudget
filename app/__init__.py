import os
import sqlite3

import click
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash

from . import database as db

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower()
        in {"1", "true", "yes"},
    )
    if test_config is not None:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "Set FLASK_SECRET_KEY to a random secret before starting the app."
        )

    csrf.init_app(app)
    from .routes import main
    app.register_blueprint(main)

    @app.cli.command("setup-owner")
    @click.argument("email")
    def setup_owner(email):
        """Initialize user 1's email and password before first use."""
        email = email.strip().lower()
        if not _valid_email(email):
            raise click.ClickException("Enter a valid email address.")

        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
        if len(password) < 12:
            raise click.ClickException("Password must be at least 12 characters.")

        con, cur = db.get_connection()
        try:
            initialized = db.initialize_legacy_user(
                cur, email, generate_password_hash(password)
            )
            if not initialized:
                raise click.ClickException(
                    "User 1 is missing or has already been initialized."
                )
            con.commit()
        except sqlite3.IntegrityError as error:
            raise click.ClickException(
                "That email address is already registered."
            ) from error
        finally:
            db.close_connection(con)

        click.echo(f"Owner account initialized for {email} (user ID 1).")

    return app


def _valid_email(email):
    return (
        len(email) <= 254
        and "@" in email
        and not any(character.isspace() for character in email)
        and not email.startswith("@")
        and not email.endswith("@")
    )