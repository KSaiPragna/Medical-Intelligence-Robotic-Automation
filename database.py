import os
import sqlite3
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), "patients.db")


def get_connection():
    """Create a persistent SQLite connection with row support."""
    connection = sqlite3.connect(DB_FILE, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def create_table():
    """Create the patients table and initialize sample records."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    dob DATE NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    glucose REAL NOT NULL,
                    haemoglobin REAL NOT NULL,
                    cholesterol REAL NOT NULL,
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        _initialize_sample_data()
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to initialize database: {error}") from error


def _initialize_sample_data():
    """Insert sample patients when the database is empty."""
    sample_patients = [
        {
            "full_name": "Aisha Khan",
            "dob": "1987-06-12",
            "email": "aisha.khan@example.com",
            "glucose": 134.0,
            "haemoglobin": 11.7,
            "cholesterol": 225.0,
            "remarks": "Patient blood profile suggests elevated glucose and cholesterol. Clinical follow-up for diabetes and cardiovascular risk is recommended."
        },
        {
            "full_name": "Daniel Morris",
            "dob": "1993-11-28",
            "email": "daniel.morris@example.com",
            "glucose": 96.0,
            "haemoglobin": 14.1,
            "cholesterol": 182.0,
            "remarks": "Blood values are within a healthy range. Continue regular preventive care and maintain balanced nutrition."
        },
        {
            "full_name": "Priya Patel",
            "dob": "1979-02-05",
            "email": "priya.patel@example.com",
            "glucose": 105.0,
            "haemoglobin": 10.9,
            "cholesterol": 198.0,
            "remarks": "Mildly elevated glucose and reduced haemoglobin may warrant a targeted wellness plan and further hematology review."
        }
    ]
    try:
        with get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            if count == 0:
                for patient in sample_patients:
                    conn.execute(
                        "INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            patient["full_name"],
                            patient["dob"],
                            patient["email"],
                            patient["glucose"],
                            patient["haemoglobin"],
                            patient["cholesterol"],
                            patient["remarks"],
                        ),
                    )
                conn.commit()
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to insert sample patients: {error}") from error


def add_patient(full_name, dob, email, glucose, haemoglobin, cholesterol, remarks):
    """Insert a new patient record."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks),
            )
            conn.commit()
    except sqlite3.IntegrityError as integrity_error:
        raise ValueError("A patient with this email already exists.") from integrity_error
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to add patient: {error}") from error


def get_patients():
    """Retrieve all patient records ordered by creation date."""
    try:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to retrieve patients: {error}") from error


def get_patient(patient_id):
    """Retrieve a single patient by ID."""
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            return dict(row) if row else None
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to retrieve patient: {error}") from error


def update_patient(patient_id, full_name, dob, email, glucose, haemoglobin, cholesterol, remarks):
    """Update an existing patient record."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE patients
                SET full_name = ?, dob = ?, email = ?, glucose = ?, haemoglobin = ?, cholesterol = ?, remarks = ?
                WHERE id = ?
                """,
                (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks, patient_id),
            )
            conn.commit()
    except sqlite3.IntegrityError as integrity_error:
        raise ValueError("A patient with this email already exists.") from integrity_error
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to update patient: {error}") from error


def delete_patient(patient_id):
    """Delete a patient record."""
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
    except sqlite3.Error as error:
        raise RuntimeError(f"Unable to delete patient: {error}") from error
