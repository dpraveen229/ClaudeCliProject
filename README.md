# Employee Manager (Flask + SQLite)

A simple web app to add, list, search, edit and delete employee records.

## Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

The database file `employees.db` is created automatically on first run.

## Project structure

```
app.py              # Flask routes, validation, DB access
templates/          # HTML pages (Jinja2)
static/style.css    # Styling
employees.db        # SQLite database (auto-created)
```

## Inspecting the database

Use [DB Browser for SQLite](https://sqlitebrowser.org/) (free) to open `employees.db`.
