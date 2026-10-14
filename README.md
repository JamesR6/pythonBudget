# Budget Tracker

## First-time setup

The budget database has a placeholder account at user ID 1, and the existing
transactions are associated with it. Initialize its real email and password
once from a terminal in the project directory:

```powershell
$env:FLASK_SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
python -m pip install -r requirements.txt
flask --app run.py setup-owner you@example.com
```

The command prompts for a password and confirmation without displaying either.
Use a password of at least 12 characters. This changes only the email and
password hash on user ID 1; it does not change or move any transactions. The
command can only run while user 1 still has its placeholder password, so this
one-time initialization cannot be used to reset the account later.

Start the app in the same PowerShell terminal, where the secret key is still
available:

```powershell
python run.py
```

Then open `http://127.0.0.1:5000/register` to create an account, or
`http://127.0.0.1:5000/login` to sign in. Public registration creates ordinary
accounts with their own isolated transactions. User IDs are assigned by
SQLite: with this schema, a new account gets an ID above the current maximum.
The ID is an internal database key, not a role or a special permission.

The secret key is used to sign Flask's session cookie. Keep it private and
stable; changing it signs out active sessions. Set `SESSION_COOKIE_SECURE=true`
when serving the app over HTTPS.
The built-in server started by `run.py` is for local development, not public
production hosting.

The built-in server started by `run.py` is for local development, not public
production hosting.
