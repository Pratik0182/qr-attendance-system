# QR Attendance System

This project is an end-to-end design and implementation of a QR Attendance System developed using FastAPI, Python, SQLite, and Jinja2 templating. The system automates lecture attendance via time-bound encrypted QR codes, prevents proxy marking through IP and timestamp validation, and provides both teacher and student interfaces for seamless interaction.

## Features

- **Automated Attendance**: Students scan dynamic QR codes to mark present using their devices.
- **Secure & Anti-Proxy**:
  - **Time-Bound**: QR codes expire after a set duration (e.g., 60 seconds).
  - **Network Validation**: Ensures students are on the same local network as the instructor to prevent remote attendance marking.
  - **Encryption**: QR tokens are base64-encoded and encrypted with timestamps and course data.
- **Role-Based Interfaces**:
  - **Teachers**: Generate QRs, view real-time logs, and manually edit attendance records if needed.
  - **Students**: Scan QRs, view personal attendance history, and see monthly calendar reports.
- **Responsive Design**: precise layouts for both mobile and desktop views, including Dark/Light mode support.

## System Architecture

The application is built on a robust, lightweight stack:
- **Backend**: FastAPI (High-performance Async Python framework).
- **Database**: SQLite with SQLAlchemy ORM (Zero-configuration storage).
- **Frontend**: Server-side rendered HTML using Jinja2 templates, styled with custom CSS.

### Workflow
1.  **Teacher** generates a QR code for a specific course session.
2.  **Student** logs in and scans the QR code.
3.  **Server** validates the token (expiry, network check) and marks the student as present in the database.
4.  **Dashboard** updates instantly to reflect the new record.

## Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/qr_attendance.git
    cd qr_attendance
    ```

2.  **Install Dependencies**
    Ensure you have Python 3.9+ installed.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    - Access the app at `http://localhost:8000` (or `http://<your-ip>:8000` for mobile scanning).

## Usage

### For Teachers
1.  Go to **Teacher Login** (e.g., use Course Code "Artificial Intelligence").
2.  Click **QR Attendance** to generate a code for the current class.
3.  Use **Manual Attendance** to fix any discrepancies.
4.  View **Dashboard** for overall class statistics.

### For Students
1.  Go to **Student Login** (e.g., use unique Roll Number).
2.  Go to **Scan QR** to mark attendance.
3.  Check **My Attendance** for detailed history and percentage.

## Technologies Used

-   **Backend Framework**: FastAPI
-   **Templating**: Jinja2
-   **Database**: SQLite / SQLAlchemy
-   **QR Generation**: `qrcode` (Python library)
-   **Server**: Uvicorn

## Database Schema

-   **students**: Stores unique roll numbers.
-   **courses**: Stores course codes and active QR session data.
-   **attendances**: Links students and courses with timestamps and presence status.

---
© 2025 Student Attendance Management System
