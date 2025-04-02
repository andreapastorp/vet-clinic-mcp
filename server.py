import sqlite3
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from mcp.server.fastmcp import FastMCP, Context

# Initialize the FastMCP server
mcp = FastMCP("Vet Clinic")

# Database connection function
def get_db_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect("vet_clinic.db")
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

# ====== RESOURCES ======

@mcp.resource("schema://all")
def get_all_schemas() -> str:
    """Retrieve schema information for all tables in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get schema for all tables
    schema_query = """
    SELECT 
        name, 
        sql
    FROM 
        sqlite_master
    WHERE 
        type='table' AND 
        name NOT LIKE 'sqlite_%'
    """
    
    tables = cursor.execute(schema_query).fetchall()
    schema_info = []
    
    for table in tables:
        schema_info.append(f"Table: {table['name']}\n{table['sql']}\n")
    
    conn.close()
    return "\n".join(schema_info)

@mcp.resource("schema://{table_name}")
def get_table_schema(table_name: str) -> str:
    """Retrieve schema information for a specific table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify the table exists
    table_check = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (table_name,)
    ).fetchone()
    
    if not table_check:
        conn.close()
        return f"Table '{table_name}' not found."
    
    # Get table schema
    schema = cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", 
        (table_name,)
    ).fetchone()
    
    # Get column info
    columns = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    column_info = "\nColumns:\n" + "\n".join(
        [f"- {col['name']} ({col['type']})" for col in columns]
    )
    
    conn.close()
    return f"Table: {table_name}\n{schema['sql']}{column_info}"

@mcp.resource("patients://all")
def get_all_patients() -> str:
    """List all patients in the system."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    patients = cursor.execute("""
        SELECT id, name, species, breed, gender, birth_date, microchip_number
        FROM patients
        ORDER BY name
    """).fetchall()
    
    if not patients:
        conn.close()
        return "No patients found."
    
    result = "Patients:\n"
    for patient in patients:
        result += f"ID: {patient['id']} | Name: {patient['name']} | Species: {patient['species']} | Breed: {patient['breed']}\n"
    
    conn.close()
    return result

@mcp.resource("patients://{patient_id}")
def get_patient_details(patient_id: str) -> str:
    """Get detailed information about a specific patient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get patient info
    patient = cursor.execute("""
        SELECT id, name, species, breed, gender, birth_date, microchip_number
        FROM patients
        WHERE id = ?
    """, (patient_id,)).fetchone()
    
    if not patient:
        conn.close()
        return f"Patient with ID {patient_id} not found."
    
    # Format patient info
    result = f"Patient: {patient['name']} (ID: {patient['id']})\n"
    result += f"Species: {patient['species']}\n"
    result += f"Breed: {patient['breed']}\n"
    result += f"Gender: {patient['gender']}\n"
    result += f"Birth Date: {patient['birth_date']}\n"
    result += f"Microchip: {patient['microchip_number']}\n\n"
    
    # Get appointments
    appointments = cursor.execute("""
        SELECT date, status, notes, appointment_type
        FROM appointments
        WHERE patient_id = ?
        ORDER BY date DESC
    """, (patient_id,)).fetchall()
    
    if appointments:
        result += "Appointments:\n"
        for appt in appointments:
            result += f"- {appt['date']} | {appt['appointment_type']} | {appt['status']}\n"
            if appt['notes']:
                result += f"  Notes: {appt['notes']}\n"
    
    # Get weight history
    weights = cursor.execute("""
        SELECT weight, date, note
        FROM weight_records
        WHERE patient_id = ?
        ORDER BY date DESC
    """, (patient_id,)).fetchall()
    
    if weights:
        result += "\nWeight History:\n"
        for weight in weights:
            result += f"- {weight['date']} | {weight['weight']} kg"
            if weight['note']:
                result += f" | {weight['note']}"
            result += "\n"
    
    # Get vaccinations
    vaccinations = cursor.execute("""
        SELECT type, date, expiration_date
        FROM vaccinations
        WHERE patient_id = ?
        ORDER BY date DESC
    """, (patient_id,)).fetchall()
    
    if vaccinations:
        result += "\nVaccinations:\n"
        for vax in vaccinations:
            result += f"- {vax['type']} | Given: {vax['date']} | Expires: {vax['expiration_date']}\n"
    
    conn.close()
    return result

# ====== TOOLS ======

@mcp.tool()
def query_patients(search_term: str) -> str:
    """
    Search for patients by name, species, or breed.
    
    Args:
        search_term: Term to search for in patient records
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Search in multiple fields
    patients = cursor.execute("""
        SELECT id, name, species, breed, gender 
        FROM patients
        WHERE name LIKE ? OR species LIKE ? OR breed LIKE ?
        ORDER BY name
    """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")).fetchall()
    
    if not patients:
        conn.close()
        return f"No patients found matching '{search_term}'."
    
    result = f"Patients matching '{search_term}':\n"
    for patient in patients:
        result += f"ID: {patient['id']} | Name: {patient['name']} | Species: {patient['species']} | Breed: {patient['breed']} | Gender: {patient['gender']}\n"
    
    conn.close()
    return result

@mcp.tool()
def create_patient(
    id: str, 
    name: str, 
    species: str, 
    breed: Optional[str] = None, 
    gender: Optional[str] = None, 
    birth_date: Optional[str] = None, 
    microchip_number: Optional[str] = None
) -> str:
    """
    Create a new patient record.
    
    Args:
        id: Unique patient ID (e.g. P123)
        name: Patient name
        species: Animal species (e.g. Dog, Cat)
        breed: Breed of the animal
        gender: Gender (Male, Female)
        birth_date: Birth date in YYYY-MM-DD format
        microchip_number: Microchip ID if available
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient ID already exists
    existing = cursor.execute("SELECT id FROM patients WHERE id = ?", (id,)).fetchone()
    if existing:
        conn.close()
        return f"Error: Patient with ID {id} already exists."
    
    # Validate birth date format if provided
    if birth_date:
        try:
            datetime.strptime(birth_date, '%Y-%m-%d')
        except ValueError:
            conn.close()
            return "Error: Birth date must be in YYYY-MM-DD format."
    
    # Insert new patient
    try:
        cursor.execute("""
            INSERT INTO patients (id, name, species, breed, gender, birth_date, microchip_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id, name, species, breed, gender, birth_date, microchip_number))
        
        conn.commit()
        conn.close()
        return f"Patient {name} (ID: {id}) created successfully."
    except sqlite3.Error as e:
        conn.close()
        return f"Error creating patient: {str(e)}"

@mcp.tool()
def update_patient(
    id: str,
    name: Optional[str] = None,
    species: Optional[str] = None,
    breed: Optional[str] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    microchip_number: Optional[str] = None
) -> str:
    """
    Update an existing patient's information.
    
    Args:
        id: Patient ID to update
        name: New name (optional)
        species: New species (optional)
        breed: New breed (optional)
        gender: New gender (optional)
        birth_date: New birth date in YYYY-MM-DD format (optional)
        microchip_number: New microchip number (optional)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    patient = cursor.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
    if not patient:
        conn.close()
        return f"Error: Patient with ID {id} not found."
    
    # Validate birth date format if provided
    if birth_date:
        try:
            datetime.strptime(birth_date, '%Y-%m-%d')
        except ValueError:
            conn.close()
            return "Error: Birth date must be in YYYY-MM-DD format."
    
    # Build update query dynamically based on provided fields
    update_fields = []
    params = []
    
    if name:
        update_fields.append("name = ?")
        params.append(name)
    
    if species:
        update_fields.append("species = ?")
        params.append(species)
    
    if breed is not None:  # Allow empty string to clear the field
        update_fields.append("breed = ?")
        params.append(breed)
    
    if gender is not None:
        update_fields.append("gender = ?")
        params.append(gender)
    
    if birth_date is not None:
        update_fields.append("birth_date = ?")
        params.append(birth_date)
    
    if microchip_number is not None:
        update_fields.append("microchip_number = ?")
        params.append(microchip_number)
    
    if not update_fields:
        conn.close()
        return "No fields provided for update."
    
    # Execute update
    query = f"UPDATE patients SET {', '.join(update_fields)} WHERE id = ?"
    params.append(id)
    
    try:
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return f"Patient {id} updated successfully."
    except sqlite3.Error as e:
        conn.close()
        return f"Error updating patient: {str(e)}"

@mcp.tool()
def add_appointment(
    patient_id: str,
    date: str,
    appointment_type: str,
    status: str = "Scheduled",
    notes: Optional[str] = None
) -> str:
    """
    Schedule a new appointment for a patient.
    
    Args:
        patient_id: ID of the patient
        date: Appointment date/time (YYYY-MM-DD HH:MM format)
        appointment_type: Type of appointment (Checkup, Vaccination, etc.)
        status: Status of appointment (Scheduled, Completed, Cancelled, etc.)
        notes: Additional notes about the appointment
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    patient = cursor.execute("SELECT id, name FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return f"Error: Patient with ID {patient_id} not found."
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d %H:%M')
    except ValueError:
        conn.close()
        return "Error: Date must be in YYYY-MM-DD HH:MM format."
    
    # Insert appointment
    try:
        cursor.execute("""
            INSERT INTO appointments (patient_id, date, appointment_type, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, date, appointment_type, status, notes))
        
        conn.commit()
        conn.close()
        return f"Appointment for {patient['name']} scheduled on {date} successfully."
    except sqlite3.Error as e:
        conn.close()
        return f"Error scheduling appointment: {str(e)}"

@mcp.tool()
def add_weight_record(
    patient_id: str,
    weight: float,
    date: str,
    note: Optional[str] = None
) -> str:
    """
    Add a new weight record for a patient.
    
    Args:
        patient_id: ID of the patient
        weight: Weight in kg
        date: Date of measurement (YYYY-MM-DD format)
        note: Additional notes about the weight
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    patient = cursor.execute("SELECT id, name FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return f"Error: Patient with ID {patient_id} not found."
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        conn.close()
        return "Error: Date must be in YYYY-MM-DD format."
    
    # Validate weight
    if weight <= 0:
        conn.close()
        return "Error: Weight must be greater than zero."
    
    # Insert weight record
    try:
        cursor.execute("""
            INSERT INTO weight_records (patient_id, weight, date, note)
            VALUES (?, ?, ?, ?)
        """, (patient_id, weight, date, note))
        
        conn.commit()
        conn.close()
        return f"Weight record for {patient['name']} added successfully: {weight} kg on {date}."
    except sqlite3.Error as e:
        conn.close()
        return f"Error adding weight record: {str(e)}"

@mcp.tool()
def add_vaccination(
    patient_id: str,
    type: str,
    date: str,
    expiration_date: str
) -> str:
    """
    Add a vaccination record for a patient.
    
    Args:
        patient_id: ID of the patient
        type: Type of vaccination (Rabies, DHPP, FVRCP, etc.)
        date: Vaccination date (YYYY-MM-DD format)
        expiration_date: Expiration date (YYYY-MM-DD format)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if patient exists
    patient = cursor.execute("SELECT id, name FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return f"Error: Patient with ID {patient_id} not found."
    
    # Validate date formats
    try:
        datetime.strptime(date, '%Y-%m-%d')
        datetime.strptime(expiration_date, '%Y-%m-%d')
    except ValueError:
        conn.close()
        return "Error: Dates must be in YYYY-MM-DD format."
    
    # Insert vaccination record
    try:
        cursor.execute("""
            INSERT INTO vaccinations (patient_id, type, date, expiration_date)
            VALUES (?, ?, ?, ?)
        """, (patient_id, type, date, expiration_date))
        
        conn.commit()
        conn.close()
        return f"Vaccination record for {patient['name']} added successfully: {type} on {date}."
    except sqlite3.Error as e:
        conn.close()
        return f"Error adding vaccination record: {str(e)}"

# ====== PROMPTS ======

@mcp.prompt()
def patient_summary_prompt(patient_id: str) -> str:
    """Create a prompt for generating a concise patient summary."""
    return f"""
    Provide a concise summary of the patient with ID {patient_id}.
    Focus on key health indicators, recent appointments, and vaccination status.
    Keep your response brief and organized by categories.
    """

@mcp.prompt()
def appointment_analysis_prompt(patient_id: str) -> str:
    """Create a prompt for analyzing a patient's appointment history."""
    return f"""
    Analyze the appointment history for patient {patient_id}.
    Identify patterns, recurring issues, and note any missed appointments.
    Provide a timeline of health events and summarize the patient's overall care journey.
    Be concise and focus only on the most relevant clinical information.
    """

@mcp.prompt()
def health_trends_prompt(patient_id: str) -> str:
    """Create a prompt for analyzing health trends based on weight and vaccination history."""
    return f"""
    Analyze the health trends for patient {patient_id} based on weight records and vaccination history.
    Focus on:
    1. Weight trends and what they indicate about the patient's health
    2. Vaccination compliance and upcoming due dates
    3. Any concerning patterns that might need attention
    Keep your analysis concise and clinically relevant.
    """

# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
