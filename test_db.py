#!/usr/bin/env python3
"""
Simple test script to verify the database setup and contents.
"""

import sqlite3
import os

# Database path - must match server.py
DB_PATH = "vet_clinic.db"

def check_db():
    """Check if database exists and what's in it"""
    if not os.path.exists(DB_PATH):
        print(f"Database does not exist at {DB_PATH}")
        return
    
    print(f"Database found at {DB_PATH}")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if patients table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients'")
    if not cursor.fetchone():
        print("Patients table does not exist!")
        conn.close()
        return
    
    # Count patients
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]
    print(f"Found {count} patients in database")
    
    # List patients
    if count > 0:
        cursor.execute("SELECT * FROM patients")
        print("\nPatients in database:")
        for row in cursor.fetchall():
            print(f"- {dict(row)}")
    
    conn.close()

def recreate_db():
    """Recreate the database with sample data"""
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        print(f"Removing existing database at {DB_PATH}")
        os.remove(DB_PATH)
    
    # Create new database
    print(f"Creating new database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            species TEXT NOT NULL,
            breed TEXT,
            age INTEGER,
            owner TEXT
        )
    """)
    
    # Insert sample data
    sample_patients = [
        ("P001", "Kubba", "Dog", "Golden Retriever", 5, "Andrea Smith"),
        ("P002", "Bella", "Cat", "Siamese", 7, "Michael Johnson"),
        ("P003", "Max", "Dog", "Beagle", 3, "Sarah Williams")
    ]
    
    cursor.executemany(
        "INSERT INTO patients (id, name, species, breed, age, owner) VALUES (?, ?, ?, ?, ?, ?)",
        sample_patients
    )
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("Database recreated with sample data")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--recreate":
        recreate_db()
    
    check_db()
