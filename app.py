from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response
import sqlite3
import os
import qrcode
import re
import csv
import io
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "qrcodes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"^[0-9+\-\s]{7,20}$")
ROLL_RE = re.compile(r"^[A-Za-z0-9\-]{2,30}$")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Check if attendance table exists and has correct schema
    try:
        c.execute("PRAGMA table_info(attendance)")
        columns = [row[1] for row in c.fetchall()]
        
        # If student_id column is missing, drop and recreate tables
        if "student_id" not in columns:
            print("Migrating database schema...")
            c.execute("DROP TABLE IF EXISTS attendance")
            c.execute("DROP TABLE IF EXISTS students")
            conn.commit()
    except:
        pass

    c.execute(
        """CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            roll_number TEXT UNIQUE,
            course TEXT,
            year TEXT,
            qr_code TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )"""
    )

    c.execute(
        """CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )"""
    )

    conn.commit()
    c.execute("SELECT COUNT(*) FROM admin WHERE username=?", ("admin",))
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO admin (username, password) VALUES (?, ?)",
            ("admin", generate_password_hash("admin123")),
        )
        conn.commit()

    conn.close()


init_db()


def create_qr_code(student_id):
    filename = f"{student_id}.png"
    output_path = os.path.join(UPLOAD_FOLDER, filename)

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(str(student_id))
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    image.save(output_path)

    return filename


def validate_student_data(data, required_fields=None):
    required_fields = required_fields or []
    errors = []

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    roll_number = data.get("roll_number", "").strip()
    course = data.get("course", "").strip()
    year = data.get("year", "").strip()

    if not name:
        errors.append("Student name is required.")

    if not email or not EMAIL_RE.match(email):
        errors.append("Please enter a valid email address.")

    if "phone" in required_fields and not phone:
        errors.append("Phone number is required.")
    elif phone and not PHONE_RE.match(phone):
        errors.append("Phone number must contain digits and may include +, -, or spaces.")

    if "roll_number" in required_fields:
        if not roll_number:
            errors.append("Roll number is required.")
        elif not ROLL_RE.match(roll_number):
            errors.append("Roll number must be alphanumeric and may include dashes.")

    if "course" in required_fields and not course:
        errors.append("Course name is required.")

    if "year" in required_fields and not year:
        errors.append("Year is required.")

    return errors


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/generate", methods=["GET", "POST"])
def generate_page():
    if request.method == "POST":
        form = request.form
        errors = validate_student_data(form, required_fields=["phone"])

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("generate.html", form=form)

        name = form.get("name", "").strip()
        email = form.get("email", "").strip().lower()
        phone = form.get("phone", "").strip()
        course = form.get("course", "").strip()
        year = form.get("year", "").strip()

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO students (name, email, phone, course, year) VALUES (?, ?, ?, ?, ?)",
                (name, email, phone, course, year),
            )
            student_id = c.lastrowid
            qr_filename = create_qr_code(student_id)
            c.execute("UPDATE students SET qr_code=? WHERE id=?", (qr_filename, student_id))
            conn.commit()
            student = {
                "name": name,
                "email": email,
                "phone": phone,
                "course": course,
                "year": year,
            }
            return render_template(
                "generate.html",
                success=True,
                qr_filename=qr_filename,
                student_id=student_id,
                student=student,
            )
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            if "email" in str(exc).lower():
                flash("This email is already registered.", "warning")
            else:
                flash("Unable to create student record. Please verify your data.", "warning")
            return render_template("generate.html", form=form)
        finally:
            conn.close()

    return render_template("generate.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        form = request.form
        errors = validate_student_data(form, required_fields=["phone", "roll_number", "course", "year"])

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", form=form)

        name = form.get("name", "").strip()
        email = form.get("email", "").strip().lower()
        phone = form.get("phone", "").strip()
        roll_number = form.get("roll_number", "").strip()
        course = form.get("course", "").strip()
        year = form.get("year", "").strip()

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO students (name, email, phone, roll_number, course, year) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, phone, roll_number, course, year),
            )
            student_id = c.lastrowid
            qr_filename = create_qr_code(student_id)
            c.execute("UPDATE students SET qr_code=? WHERE id=?", (qr_filename, student_id))
            conn.commit()
            student = {
                "name": name,
                "email": email,
                "phone": phone,
                "roll_number": roll_number,
                "course": course,
                "year": year,
            }
            return render_template(
                "register.html",
                success=True,
                qr_filename=qr_filename,
                student_id=student_id,
                student=student,
            )
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            if "email" in str(exc).lower():
                flash("This email is already registered.", "warning")
            elif "roll_number" in str(exc).lower():
                flash("This roll number is already assigned.", "warning")
            else:
                flash("Unable to save student. Please verify your details.", "warning")
            return render_template("register.html", form=form)
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=?", (username,))
        admin = c.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin"] = username
            flash("Welcome back, administrator.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    filter_date = request.args.get("date", "").strip()

    conn = get_db()
    c = conn.cursor()

    total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_attendance = c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    today = datetime.now().date().isoformat()
    present_today = c.execute(
        "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE DATE(timestamp)=?", (today,)
    ).fetchone()[0]
    absent_today = max(total_students - present_today, 0)

    filter_clauses = []
    filter_params = []

    if search:
        filter_clauses.append("(students.name LIKE ? OR students.email LIKE ? OR students.roll_number LIKE ?)")
        filter_params.extend([f"%{search}%"] * 3)

    if filter_date:
        filter_clauses.append("DATE(attendance.timestamp)=?")
        filter_params.append(filter_date)

    base_sql = """
        SELECT attendance.id, students.id AS student_id, students.name, students.email,
        students.roll_number, students.course, students.year,
        attendance.status, attendance.timestamp
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """

    if filter_clauses:
        base_sql += " WHERE " + " AND ".join(filter_clauses)

    attendance_rows = c.execute(base_sql + " ORDER BY attendance.timestamp DESC LIMIT 100", filter_params).fetchall()
    recent_students = c.execute(
        "SELECT id, name, email, roll_number, course, year, qr_code FROM students ORDER BY created_at DESC LIMIT 8"
    ).fetchall()
    conn.close()

    return render_template(
        "admin.html",
        total_students=total_students,
        total_attendance=total_attendance,
        present_today=present_today,
        absent_today=absent_today,
        attendance=attendance_rows,
        recent_students=recent_students,
        search=search,
        filter_date=filter_date,
    )


@app.route('/students')
def student_management():
    if "admin" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    year_filter = request.args.get("year", "").strip()
    course_filter = request.args.get("course", "").strip()

    conn = get_db()
    c = conn.cursor()
    filter_clauses = []
    filter_params = []

    if search:
        filter_clauses.append("(name LIKE ? OR email LIKE ? OR roll_number LIKE ?)")
        filter_params.extend([f"%{search}%"] * 3)

    if year_filter:
        filter_clauses.append("year = ?")
        filter_params.append(year_filter)

    if course_filter:
        filter_clauses.append("course LIKE ?")
        filter_params.append(f"%{course_filter}%")

    students_sql = "SELECT * FROM students"
    if filter_clauses:
        students_sql += " WHERE " + " AND ".join(filter_clauses)
    students_sql += " ORDER BY created_at DESC"

    students = c.execute(students_sql, filter_params).fetchall()
    years = [r[0] for r in c.execute("SELECT DISTINCT year FROM students WHERE year IS NOT NULL AND year <> '' ORDER BY year").fetchall()]
    courses = [r[0] for r in c.execute("SELECT DISTINCT course FROM students WHERE course IS NOT NULL AND course <> '' ORDER BY course").fetchall()]
    conn.close()

    return render_template(
        "student.html",
        students=students,
        search=search,
        year_filter=year_filter,
        course_filter=course_filter,
        years=years,
        courses=courses,
    )


@app.route('/classes')
def class_root():
    return redirect(url_for("class_management", class_id=1))


@app.route('/classes/<int:class_id>')
def class_management(class_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    per_page = 10
    offset = max(class_id - 1, 0) * per_page

    conn = get_db()
    c = conn.cursor()
    filter_clauses = []
    filter_params = []

    if search:
        filter_clauses.append("(name LIKE ? OR email LIKE ? OR roll_number LIKE ?)")
        filter_params.extend([f"%{search}%"] * 3)

    students_sql = "SELECT * FROM students"
    if filter_clauses:
        students_sql += " WHERE " + " AND ".join(filter_clauses)
    students_sql += " ORDER BY name ASC LIMIT ? OFFSET ?"
    filter_params.extend([per_page, offset])

    students = c.execute(students_sql, filter_params).fetchall()
    count_sql = "SELECT COUNT(*) FROM students"
    if filter_clauses:
        count_sql += " WHERE " + " AND ".join(filter_clauses)
    total = c.execute(count_sql, filter_params[:-2]).fetchone()[0]
    conn.close()

    total_pages = max((total + per_page - 1) // per_page, 1)
    return render_template(
        "class.html",
        class_id=class_id,
        students=students,
        search=search,
        total_pages=total_pages,
    )


@app.route('/attendance')
def attendance_list():
    if "admin" not in session:
        return redirect(url_for("login"))

    search = request.args.get("search", "").strip()
    conn = get_db()
    c = conn.cursor()

    filter_clauses = []
    filter_params = []
    if search:
        filter_clauses.append("(students.name LIKE ? OR students.email LIKE ? OR students.roll_number LIKE ?)")
        filter_params.extend([f"%{search}%"] * 3)

    base_sql = """
        SELECT attendance.id, students.name, students.email, students.roll_number,
        attendance.status, attendance.timestamp
        FROM attendance
        JOIN students ON attendance.student_id = students.id
    """
    if filter_clauses:
        base_sql += " WHERE " + " AND ".join(filter_clauses)
    base_sql += " ORDER BY attendance.timestamp DESC"

    rows = c.execute(base_sql, filter_params).fetchall()
    conn.close()

    return render_template("attendance.html", rows=rows, search=search)


@app.route('/reports')
def reports_page():
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    total_students = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_attendance = c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    today = datetime.now().date().isoformat()
    present_today = c.execute(
        "SELECT COUNT(DISTINCT student_id) FROM attendance WHERE DATE(timestamp)=?", (today,)
    ).fetchone()[0]
    conn.close()

    return render_template(
        "reports.html",
        total_students=total_students,
        total_attendance=total_attendance,
        present_today=present_today,
    )


@app.route("/student/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (student_id,))
    student = c.fetchone()

    if not student:
        conn.close()
        flash("Student record not found.", "warning")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        form = request.form
        errors = validate_student_data(form, required_fields=["phone", "roll_number", "course", "year"])

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("edit_student.html", student=student)

        name = form.get("name", "").strip()
        email = form.get("email", "").strip().lower()
        phone = form.get("phone", "").strip()
        roll_number = form.get("roll_number", "").strip()
        course = form.get("course", "").strip()
        year = form.get("year", "").strip()

        try:
            c.execute(
                "UPDATE students SET name=?, email=?, phone=?, roll_number=?, course=?, year=? WHERE id=?",
                (name, email, phone, roll_number, course, year, student_id),
            )
            conn.commit()
            flash("Student profile updated successfully.", "success")
            return redirect(url_for("admin_dashboard"))
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            if "email" in str(exc).lower():
                flash("This email address is already in use.", "warning")
            elif "roll_number" in str(exc).lower():
                flash("This roll number is already assigned.", "warning")
            else:
                flash("Unable to update student details.", "warning")

    conn.close()
    return render_template("edit_student.html", student=student)


@app.route("/student/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
    c.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()

    flash("Student record and attendance history deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/export")
def export_attendance():
    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    rows = c.execute(
        """
            SELECT attendance.timestamp, students.name, students.email,
            students.roll_number, students.course, students.year, attendance.status
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            ORDER BY attendance.timestamp DESC
        """
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Name", "Email", "Roll", "Course", "Year", "Status"])
    for row in rows:
        writer.writerow([
            row["timestamp"],
            row["name"],
            row["email"],
            row["roll_number"] or "",
            row["course"] or "",
            row["year"] or "",
            row["status"],
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=attendance_export.csv"
    return response


@app.route("/scan", methods=["POST"])
def scan():
    payload = request.get_json(silent=True) or {}
    student_id = payload.get("student_id")

    if not student_id or not str(student_id).isdigit():
        return jsonify({"status": "error", "message": "Invalid QR payload."})

    student_id = int(student_id)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (student_id,))
    student = c.fetchone()

    if not student:
        conn.close()
        return jsonify({"status": "error", "message": "Student not found for scanned QR code."})

    c.execute(
        "INSERT INTO attendance (student_id, status) VALUES (?, ?)",
        (student_id, "Present"),
    )
    conn.commit()
    conn.close()

    return jsonify(
        {
            "status": "success",
            "message": f"Attendance recorded for {student['name']}",
            "student_name": student["name"],
            "attendance_status": "Present",
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
