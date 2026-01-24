# QR Code Attendance System

![System Overview](assets/imgs/Screenshot%202026-01-24%20163351.png)

This project is a **QR-Based Student Attendance Management System** designed to track and automate the attendance process using dynamic, encrypted QR codes. The focus of this project was to create a secure backend architecture that prevents proxy attendance while keeping the user experience simple.

The system utilizes time-bound tokens and network validation to ensure that students must be physically present in the class to mark their attendance.

## Key Features

*   **Dynamic QR Codes**: The system generates unique, encrypted QR codes that expire after a short duration (1-2 minutes), preventing code sharing.

    <div align="center">
      <img src="assets/imgs/Screenshot%202026-01-24%20163034.png" alt="Dynamic QR Generation" width="600"/>
      <p><i>Teacher Interface for Generating Dynamic QRs</i></p>
    </div>

*   **Anti-Proxy Mechanisms**:
    *   **Subnet Verification**: Validates that the student's device is connected to the same local network as the instructor.
    *   **Timestamp Encryption**: Embeds time data within the QR token to prevent replay attacks.
*   **Role-Based Access Control**:
    *   **Teachers**: Capabilities include generating session-specific QRs, monitoring real-time attendance logs, and manual override for attendance records.
    
    <div align="center">
      <img src="assets/imgs/Screenshot%202026-01-24%20163007.png" alt="Teacher Dashboard" width="600"/>
      <p><i>Teacher Dashboard</i></p>
    </div>

    *   **Students**: Streamlined interface to scan QRs and view detailed attendance history and subject-wise logs.
    
    <div align="center">
      <img src="assets/imgs/Screenshot%202026-01-24%20163108.png" alt="Student View" width="600"/>
      <p><i>Student Attendance History</i></p>
    </div>

*   **Data Management**: Implements a structured relational database using SQLAlchemy to efficiently handle student data, course mappings, and daily attendance records.
*   **Streamlined Authentication**: The login process utilizes unique identifiers (Roll Number/Course Code) without password verification. This design choice was made purposely to facilitate rapid testing and evaluation cycles during the development phase.

    <div align="center">
      <img src="assets/imgs/Screenshot%202026-01-24%20162644.png" alt="Simple Login" width="600"/>
      <p><i>Streamlined Login Interface</i></p>
    </div>

## Technology Stack

The project emphasizes backend logic and system security:

*   **Backend**: **FastAPI** (Python) - Utilizing its asynchronous capabilities for high performance.
*   **Database**: **SQLite** with **SQLAlchemy ORM** - For reliable relational data management.
*   **Frontend**: Jinja2 Templates (HTML/CSS) - Providing a functional and responsive user interface.
*   **Security**: Custom implementation of token encryption and network validation logic.

## Installation and Run Instructions

To set up the project locally:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Pratik0182/qr-attendance-system.git
    cd qr-attendance-system
    ```

2.  **Install dependencies**:
    Ensure Python is installed, then run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the server**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

4.  **Access the application**:
    Navigate to `http://localhost:8000` in your web browser.
    *   **Student Login**: Use a registered Roll Number (e.g., `231210066`).
    *   **Teacher Login**: Select a registered Course Code (e.g., `CSBB 252: Artificial Intelligence`).

## Project Structure

*   `main.py`: Core application logic containing API routes, security validation, and database interactions.
*   `templates/`: HTML templates for the user interface.
*   `data/`: Directory containing the SQLite database.
*   `static/`: Static assets including CSS.
*   `assets/`: Directory containing font files and other static resources.

<div align="center">
  <img src="assets/imgs/Screenshot%202026-01-24%20163159.png" alt="Logs" width="45%" style="margin-right: 10px;"/>
  <img src="assets/imgs/Screenshot%202026-01-24%20163140.png" alt="Analytics" width="45%"/>
  <p><i>Comprehensive Logs and Analytics</i></p>
</div>

## Configuration Note

The current implementation comes with pre-populated data (specific courses and roll number ranges) tailored to our current academic batch for demonstration and testing purposes.

These values are defined in the database initialization logic within `main.py` and can be easily modified or integrated with an external student database to adapt the system for other classes or institutions.

## Future Enhancements

*   **Secure Authentication**: While the current version prioritizes testing speed, future iterations will include password-based authentication (Hashing/JWT) for enhanced user security.

## Note

This application was developed to demonstrate secure backend system architecture and automation using Python. The core validation logic housed in `main.py` is the primary focus of this implementation.
