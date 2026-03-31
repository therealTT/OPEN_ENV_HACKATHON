"""
Run this script to create and seed portal.db from scratch.
Usage: python seed_db.py
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")


def create_and_seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE drugs (
            drug_name    TEXT PRIMARY KEY,
            app_number   TEXT UNIQUE,
            approval_date TEXT,
            manufacturer TEXT,
            indication   TEXT,
            status       TEXT
        )
    """)

    c.execute("""
        CREATE TABLE documents (
            doc_id    TEXT PRIMARY KEY,
            drug_name TEXT,
            doc_type  TEXT,
            content   TEXT
        )
    """)

    c.execute("""
        CREATE TABLE form_submissions (
            submission_id TEXT PRIMARY KEY,
            form_type     TEXT,
            drug_name     TEXT,
            app_number    TEXT,
            submitted_at  TEXT,
            fields_json   TEXT
        )
    """)

    # --- Drugs ---
    drugs = [
        ("NEXOLARA",  "NDA-042817", "2022-03-15", "Helivar Therapeutics", "Myelofibrosis",     "Approved"),
        ("ZETHROVAN", "NDA-039204", "2020-11-08", "Coraxis Pharma",       "Myelofibrosis",     "Approved"),
        ("PRIMAVEX",  "NDA-051673", "2023-06-22", "Dunmore BioSciences",  "Myelofibrosis",     "Approved"),
        ("VALDIPRINE","NDA-028941", "2018-04-30", "Solvanta Inc",         "Thrombocytopenia",  "Approved"),
    ]
    c.executemany("INSERT INTO drugs VALUES (?,?,?,?,?,?)", drugs)

    # --- Documents ---
    documents = [
        ("DOC-001", "NEXOLARA", "Prescribing Information", json.dumps({
            "starting_dose":       "100mg once daily",
            "max_dose":            "200mg once daily",
            "renal_adjustment":    "50mg once daily if eGFR < 30",
            "hepatic_adjustment":  "Not recommended in severe hepatic impairment",
        })),
        ("DOC-002", "NEXOLARA", "Patient Medication Guide", json.dumps({
            "storage":      "Store at room temperature (68-77°F)",
            "missed_dose":  "Take as soon as remembered unless next dose is within 12 hours",
        })),
        ("DOC-003", "ZETHROVAN", "Prescribing Information", json.dumps({
            "starting_dose":    "150mg twice daily",
            "max_dose":         "300mg twice daily",
            "renal_adjustment": "No adjustment required",
        })),
        ("DOC-004", "PRIMAVEX", "Prescribing Information", json.dumps({
            "starting_dose":    "200mg once daily",
            "max_dose":         "400mg once daily",
            "renal_adjustment": "100mg once daily if eGFR < 45",
        })),
        ("DOC-005", "VALDIPRINE", "Prescribing Information", json.dumps({
            "starting_dose":    "50mg once daily",
            "max_dose":         "100mg once daily",
            "renal_adjustment": "25mg once daily if eGFR < 60",
        })),
    ]
    c.executemany("INSERT INTO documents VALUES (?,?,?,?)", documents)

    conn.commit()
    conn.close()
    print(f"portal.db seeded at {DB_PATH}")


if __name__ == "__main__":
    create_and_seed()
