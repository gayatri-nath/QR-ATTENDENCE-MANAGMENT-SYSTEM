import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('attendance.db')
c = conn.cursor()

# Create tables
c.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    roll_number TEXT UNIQUE,
    course TEXT,
    year TEXT,
    qr_code TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

conn.commit()

# Take input from terminal for new admin
username = input("Enter admin username: ")
password = input("Enter admin password: ")

# Hash password
hashed_password = generate_password_hash(password)

try:
    c.execute(
        "INSERT INTO admin (username, password) VALUES (?, ?)",
        (username, hashed_password)
    )
    conn.commit()
    print("✓ Admin user created successfully!")

except sqlite3.IntegrityError:
    print("✗ Username already exists!")

conn.close()
print("✓ Database setup complete!")