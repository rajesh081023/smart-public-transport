# Smart Public Transport

A Flask-based smart mobility and public transport demo for planning routes, comparing transport modes, exploring EV charging stations, and tracking carbon impact.

## Features

- Smart journey planner with origin/destination comparison
- Route explorer for public transport networks
- EV charging station directory and status view
- Carbon calculator and mode-by-mode emission comparison
- User login/dashboard with saved journey history
- Admin dashboard for route, stop, EV, and feedback management

## Stack

- Python 3
- Flask
- SQLite (default) / MySQL (optional)
- Jinja2 templates

## Local setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the sample environment file and adjust values if needed:
   ```bash
   cp .env.example .env
   ```
4. Initialize the database:
   ```bash
   python init_db.py
   ```
5. Run the app:
   ```bash
   python app.py
   ```

The app will start on http://127.0.0.1:5000.

## Notes

- The default database is SQLite unless `DB_TYPE=mysql` is configured.
- For production, disable debug mode and use a secure secret key.
- For a public Flask deployment, follow [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md). Rotate the seeded administrator password before exposing the app.
