from __future__ import annotations

import os
import sqlite3
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, Any

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "iclass_v3.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production",
)

F = TypeVar("F", bound=Callable[..., Any])


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'lecturer')),
            email TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE,
            student_id TEXT UNIQUE,
            name TEXT,
            programme TEXT,
            semester TEXT,
            phone TEXT,
            email TEXT,
            class_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            name TEXT,
            class_name TEXT,
            date TEXT,
            time TEXT,
            status TEXT
        )
        """
    )

    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if cursor.fetchone() is None:
        cursor.execute(
            """
            INSERT INTO users
            (full_name, username, password_hash, role, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "System Administrator",
                "admin",
                generate_password_hash("admin123"),
                "admin",
                "admin@iclass.local",
            ),
        )

    connection.commit()
    connection.close()


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        if "user_id" not in session:
            flash("Sila log masuk terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view  # type: ignore[return-value]


def admin_required(view: F) -> F:
    @wraps(view)
    def wrapped_view(*args: Any, **kwargs: Any):
        if session.get("role") != "admin":
            flash("Akses ini hanya untuk pentadbir.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)

    return wrapped_view  # type: ignore[return-value]


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_db()
        user = connection.execute(
            """
            SELECT id, full_name, username, password_hash, role, is_active
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
        connection.close()

        if (
            user is None
            or not user["is_active"]
            or not check_password_hash(user["password_hash"], password)
        ):
            flash("Nama pengguna atau kata laluan tidak sah.", "danger")
            return render_template("login.html")

        session.clear()
        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        flash(f"Selamat datang, {user['full_name']}.", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Anda telah log keluar.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    connection = get_db()

    total_students = connection.execute(
        "SELECT COUNT(*) AS total FROM students"
    ).fetchone()["total"]

    attendance_today = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM attendance
        WHERE date = strftime('%d/%m/%Y', 'now', 'localtime')
        """
    ).fetchone()["total"]

    present_today = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM attendance
        WHERE date = strftime('%d/%m/%Y', 'now', 'localtime')
          AND status LIKE 'Present%'
        """
    ).fetchone()["total"]

    late_today = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM attendance
        WHERE date = strftime('%d/%m/%Y', 'now', 'localtime')
          AND status LIKE 'Late%'
        """
    ).fetchone()["total"]

    no_class_today = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM attendance
        WHERE date = strftime('%d/%m/%Y', 'now', 'localtime')
          AND status LIKE 'No Class%'
        """
    ).fetchone()["total"]

    recent_attendance = connection.execute(
        """
        SELECT student_id, name, class_name, date, time, status
        FROM attendance
        ORDER BY id DESC
        LIMIT 8
        """
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        attendance_today=attendance_today,
        present_today=present_today,
        late_today=late_today,
        no_class_today=no_class_today,
        recent_attendance=recent_attendance,
    )


@app.route("/users")
@login_required
@admin_required
def users():
    connection = get_db()
    user_rows = connection.execute(
        """
        SELECT id, full_name, username, role, email, is_active, created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()
    connection.close()
    return render_template("users.html", users=user_rows)


@app.route("/users/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "lecturer")
    email = request.form.get("email", "").strip()

    if not full_name or not username or len(password) < 6:
        flash(
            "Nama, username dan kata laluan minimum 6 aksara diperlukan.",
            "danger",
        )
        return redirect(url_for("users"))

    if role not in {"admin", "lecturer"}:
        role = "lecturer"

    connection = get_db()
    try:
        connection.execute(
            """
            INSERT INTO users
            (full_name, username, password_hash, role, email)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                username,
                generate_password_hash(password),
                role,
                email,
            ),
        )
        connection.commit()
        flash("Pengguna berjaya ditambah.", "success")
    except sqlite3.IntegrityError:
        flash("Username tersebut telah digunakan.", "danger")
    finally:
        connection.close()

    return redirect(url_for("users"))


@app.route("/module/<module_name>")
@login_required
def module_placeholder(module_name: str):
    module_titles = {
        "classes": "Class Management",
        "students": "Student Profile",
        "attendance": "NFC Attendance",
        "analytics": "Analytics Dashboard",
        "reports": "Report & Export",
    }

    title = module_titles.get(module_name)
    if title is None:
        flash("Modul tidak ditemui.", "danger")
        return redirect(url_for("dashboard"))

    return render_template(
        "placeholder.html",
        module_title=title,
        module_name=module_name,
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
