# QR Attendance Management System

A Flask-based QR attendance management system for students and teachers. This app allows registration, QR badge generation, live attendance scanning, and admin reporting.

## Features

- Student registration and QR badge generation
- Live QR scanner attendance capture
- Admin login and attendance dashboard
- Attendance reports by student and class
- Responsive UI with modern layout

## Tech Stack

- Python 3.14+
- Flask
- SQLite
- HTML/CSS/JavaScript

## Setup

1. Create and activate a virtual environment:
   `powershell
   python -m venv venv
   .\\venv\\Scripts\\Activate.ps1
   `

2. Install dependencies:
   `powershell
   pip install -r requirements.txt
   `

3. Run the application:
   `powershell
   python app.py
   `

4. Open the browser at:
   `	ext
   http://127.0.0.1:5000
   `

## Database

- The app uses ttendance.db for local data storage.
- Database tables are created automatically when the app starts.

## Default Admin

- Username: dmin
- Password: dmin123

## Project Structure

- pp.py - Flask application and routes
- 	emplates/ - HTML templates
- static/ - CSS, JavaScript, QR images, and assets
- equirements.txt - Python dependencies

## Notes

- Do not commit ttendance.db or generated QR images.
- Keep static/qrcodes/ writable so the app can save generated QR images.
- Use env/ for your virtual environment and keep it out of version control.
