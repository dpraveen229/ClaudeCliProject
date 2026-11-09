import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE_PATH", str(BASE_DIR / "employees.db"))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret")

DEPARTMENTS = ["Engineering", "HR", "Finance", "Sales", "Marketing", "Operations"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- Database helpers ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name      TEXT NOT NULL,
                last_name       TEXT NOT NULL,
                email           TEXT NOT NULL UNIQUE,
                phone           TEXT,
                department      TEXT NOT NULL,
                designation     TEXT,
                date_of_joining TEXT,
                salary          REAL,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


# ---------- Validation ----------

FIELDS = ["first_name", "last_name", "email", "phone", "department",
          "designation", "date_of_joining", "salary"]


def read_form():
    return {f: request.form.get(f, "").strip() for f in FIELDS}


def validate(data):
    errors = []
    if not data["first_name"]:
        errors.append("First name is required.")
    if not data["last_name"]:
        errors.append("Last name is required.")
    if not EMAIL_RE.match(data["email"]):
        errors.append("A valid email is required.")
    if data["department"] not in DEPARTMENTS:
        errors.append("Please choose a department.")
    if data["phone"] and not re.fullmatch(r"[0-9+\-\s]{7,15}", data["phone"]):
        errors.append("Phone must be 7-15 digits (may include +, -, spaces).")
    if data["salary"]:
        try:
            if float(data["salary"]) < 0:
                errors.append("Salary cannot be negative.")
        except ValueError:
            errors.append("Salary must be a number.")
    return errors


def to_db_values(data):
    return (
        data["first_name"], data["last_name"], data["email"].lower(),
        data["phone"] or None, data["department"], data["designation"] or None,
        data["date_of_joining"] or None,
        float(data["salary"]) if data["salary"] else None,
    )


# ---------- Routes ----------

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    dept = request.args.get("department", "")
    sql = "SELECT * FROM employees WHERE 1=1"
    params = []
    if q:
        sql += " AND (first_name LIKE ? OR last_name LIKE ? OR email LIKE ?)"
        params += [f"%{q}%"] * 3
    if dept:
        sql += " AND department = ?"
        params.append(dept)
    sql += " ORDER BY id DESC"
    employees = get_db().execute(sql, params).fetchall()
    return render_template("index.html", employees=employees, q=q,
                           dept=dept, departments=DEPARTMENTS)


@app.route("/add", methods=["GET", "POST"])
def add_employee():
    data = {f: "" for f in FIELDS}
    if request.method == "POST":
        data = read_form()
        errors = validate(data)
        if not errors:
            try:
                db = get_db()
                db.execute(
                    """INSERT INTO employees (first_name, last_name, email, phone,
                       department, designation, date_of_joining, salary)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    to_db_values(data),
                )
                db.commit()
                flash("Employee added successfully.", "success")
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                errors.append("An employee with this email already exists.")
        for e in errors:
            flash(e, "error")
    return render_template("form.html", data=data, departments=DEPARTMENTS,
                           title="Add Employee")


@app.route("/edit/<int:emp_id>", methods=["GET", "POST"])
def edit_employee(emp_id):
    db = get_db()
    row = db.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    if row is None:
        flash("Employee not found.", "error")
        return redirect(url_for("index"))

    data = {f: "" if row[f] is None else str(row[f]) for f in FIELDS}
    if request.method == "POST":
        data = read_form()
        errors = validate(data)
        if not errors:
            try:
                db.execute(
                    """UPDATE employees SET first_name=?, last_name=?, email=?, phone=?,
                       department=?, designation=?, date_of_joining=?, salary=?
                       WHERE id=?""",
                    (*to_db_values(data), emp_id),
                )
                db.commit()
                flash("Employee updated successfully.", "success")
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                errors.append("Another employee already uses this email.")
        for e in errors:
            flash(e, "error")
    return render_template("form.html", data=data, departments=DEPARTMENTS,
                           title="Edit Employee")


@app.route("/delete/<int:emp_id>", methods=["POST"])
def delete_employee(emp_id):
    db = get_db()
    db.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
    db.commit()
    flash("Employee deleted.", "success")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
