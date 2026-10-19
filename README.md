# Budget Tracker

## Overview and Usage

pythonBudget is a Flask based budget tracker. Command-line setup below.


```powershell
$env:FLASK_SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
python -m pip install -r requirements.txt
```

Start the app in the same PowerShell terminal, where the secret key is still
available:

```powershell
python run.py
```

Then open `http://127.0.0.1:5000/register` to create an account, or
`http://127.0.0.1:5000/login` to sign in. Public registration creates
accounts with their own isolated transactions. 
UserID is an internal database key, not a role or a special permission.

The secret key is used to sign Flask's session cookie. Keep it private and
stable; changing it signs out active sessions. Set `SESSION_COOKIE_SECURE=true`
when serving the app over HTTPS.

The built-in server started by `run.py` is for local development, not public
production hosting.
