import asyncio
import json
import sqlite3
import os
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# Database path - keep it simple
DB_PATH = "vet_clinic.db"

# Initialize FastMCP server
mcp = FastMCP("pims")

# Function to initialize the database
def init_db():
    # Check if database needs to be created
    db_exists = os.path.exists(DB_PATH)

    # Create or connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            age INTEGER,
            owner TEXT
        );
    """)

    # Insert sample data if database is new
    if not db_exists:
        sample_patients = [
            ("P001", "Kubba", "Dog", "Golden Retriever", 5, "Andrea Smith"),
            ("P002", "Bella", "Cat", "Siamese", 7, "Michael Johnson"),
            ("P003", "Max", "Dog", "Beagle", 3, "Sarah Williams")
        ]

        cursor.executemany(
            "INSERT INTO patients (id, name, species, breed, age, owner) VALUES (?, ?, ?, ?, ?, ?)",
            sample_patients
        )
        print("Database initialized with sample data")

    conn.commit()
    conn.close()

# Initialize database when module is loaded
init_db()

@mcp.tool()
async def get_patient(identifier: str) -> Dict[str, Any]:
    """Get information about a patient by name or ID.

    Args:
        identifier: Patient name or ID

    Returns:
        Dictionary with patient information or error message
    """
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Try to find by ID
    cursor.execute("SELECT * FROM patients WHERE id = ?", (identifier,))
    patient = cursor.fetchone()

    # If not found, try by name (case insensitive)
    if not patient:
        cursor.execute("SELECT * FROM patients WHERE LOWER(name) = LOWER(?)", (identifier,))
        patient = cursor.fetchone()

    # Close connection
    conn.close()

    # Return result
    if patient:
        return {
            "found": True,
            "patient": dict(patient)
        }
    else:
        return {
            "found": False,
            "message": f"No patient found with identifier: {identifier}"
        }

@mcp.tool()
async def list_patients() -> Dict[str, Any]:
    """List all patients in the database.

    Returns:
        Dictionary with count and list of all patients
    """
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all patients
    cursor.execute("SELECT * FROM patients")
    patients = [dict(row) for row in cursor.fetchall()]

    # Close connection
    conn.close()

    # Return result
    return {
        "count": len(patients),
        "patients": patients
    }

@mcp.tool()
async def search_patients(query: str) -> Dict[str, Any]:
    """Search for patients by name, species, or breed.

    Args:
        query: Search query string

    Returns:
        Dictionary with patients matching the search
    """
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search for patients
    search_param = f"%{query}%"
    cursor.execute(
        "SELECT * FROM patients WHERE name LIKE ? OR species LIKE ? OR breed LIKE ?", 
        (search_param, search_param, search_param)
    )
    patients = [dict(row) for row in cursor.fetchall()]

    # Close connection
    conn.close()

    # Return result
    return {
        "count": len(patients),
        "patients": patients
    }

if __name__ == "__main__":
    # Run server
    mcp.run(transport='stdio')
