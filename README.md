# QR-ATTENDENCE-MANAGMENT-SYSTEM
QR Code Based Attendance Management System for students and teachers. Built for efficient attendance tracking and management.

## Features

- Student registration and QR badge generation
- Live QR scanner attendance capture
- Admin login and attendance dashboard
- Responsive modern layout with blue/white theme
- QR code generation and download

## Tech Stack

- Python 3.14+
- Flask
- SQLite
- HTML/CSS/JavaScript
- Font Awesome icons

## Setup

1. Create and activate a virtual environment:
   `powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   `

2. Install dependencies:
   `powershell
   pip install -r requirements.txt
   `

3. Run the application:
   `powershell
   python app.py
   `

4. Open the browser at http://127.0.0.1:5000

## Database

- The app uses ttendance.db for data storage.
- Database tables are created automatically when the app starts.

## Default Admin

- Username: dmin
- Password: dmin123

## Notes

- Keep the static/qrcodes folder writable for generated QR images.
- Use the web interface to register students, generate QR badges, and monitor attendance.

## Project Structure

- pp.py - Flask application and route definitions
- 	emplates/ - HTML templates
- static/ - CSS, JavaScript, and QR image storage
- equirements.txt - Python dependency list
