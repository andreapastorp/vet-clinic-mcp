import sqlite3
import os
import json

def init_db(db_path="vet_clinic.db"):
    """Initialize the veterinary clinic database with the schema."""
    # Check if db already exists - don't reinitialize if it does
    if os.path.exists(db_path):
        print(f"Database {db_path} already exists. Skipping initialization.")
        return
    
    print(f"Initializing database {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        species TEXT NOT NULL,
        breed TEXT,
        gender TEXT,
        birth_date TEXT,
        microchip_number TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        notes TEXT,
        appointment_type TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weight_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        weight REAL NOT NULL,
        date TEXT NOT NULL,
        note TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vaccinations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        type TEXT NOT NULL,
        date TEXT NOT NULL,
        expiration_date TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    )
    ''')
    
    # Insert sample data
    sample_patients = [
        ('P001', 'Max', 'Dog', 'Labrador Retriever', 'Male', '2018-05-10', 'MC123456'),
        ('P002', 'Luna', 'Cat', 'Maine Coon', 'Female', '2019-03-15', 'MC789012'),
        ('P003', 'Charlie', 'Dog', 'Golden Retriever', 'Male', '2020-11-20', 'MC345678')
    ]
    
    cursor.executemany('''
    INSERT INTO patients (id, name, species, breed, gender, birth_date, microchip_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_patients)
    
    sample_appointments = [
        ('P001', '2023-11-15 10:00', 'Completed', 'Annual checkup', 'Checkup'),
        ('P002', '2023-12-05 14:30', 'Scheduled', 'Vaccination due', 'Vaccination'),
        ('P003', '2023-11-28 11:15', 'Completed', 'Limping on left hind leg', 'Examination')
    ]
    
    cursor.executemany('''
    INSERT INTO appointments (patient_id, date, status, notes, appointment_type)
    VALUES (?, ?, ?, ?, ?)
    ''', sample_appointments)
    
    sample_weights = [
        ('P001', 32.5, '2023-11-15', 'Healthy weight'),
        ('P002', 12.2, '2023-10-20', 'Slightly overweight'),
        ('P003', 28.7, '2023-11-28', 'Weight stable')
    ]
    
    cursor.executemany('''
    INSERT INTO weight_records (patient_id, weight, date, note)
    VALUES (?, ?, ?, ?)
    ''', sample_weights)
    
    sample_vaccinations = [
        ('P001', 'Rabies', '2023-01-15', '2024-01-15'),
        ('P002', 'FVRCP', '2023-08-10', '2024-08-10'),
        ('P003', 'DHPP', '2023-04-22', '2024-04-22')
    ]
    
    cursor.executemany('''
    INSERT INTO vaccinations (patient_id, type, date, expiration_date)
    VALUES (?, ?, ?, ?)
    ''', sample_vaccinations)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully with sample data.")

if __name__ == "__main__":
    init_db()
