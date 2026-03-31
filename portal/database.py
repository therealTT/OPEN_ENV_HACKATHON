import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "portal.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_drugs(query: str) -> list[dict]:
    q = f"%{query.strip()}%"
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM drugs WHERE drug_name LIKE ? OR app_number LIKE ?",
            (q, q),
        ).fetchall()
    return [dict(r) for r in rows]


def get_drug(drug_name: str) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM drugs WHERE LOWER(drug_name) = LOWER(?)", (drug_name,)
        ).fetchone()
    return dict(row) if row else None


def search_documents(drug_name: str = "", doc_type: str = "") -> list[dict]:
    sql = "SELECT doc_id, drug_name, doc_type FROM documents WHERE 1=1"
    params: list = []
    if drug_name:
        sql += " AND LOWER(drug_name) = LOWER(?)"
        params.append(drug_name)
    if doc_type:
        sql += " AND LOWER(doc_type) = LOWER(?)"
        params.append(doc_type)
    with _conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_document(doc_id: str) -> Optional[dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE doc_id = ?", (doc_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["content"] = json.loads(d["content"])
    return d


def submit_form(form_type: str, fields: dict) -> str:
    submission_id = f"SUB-{str(uuid.uuid4())[:8].upper()}"
    with _conn() as conn:
        conn.execute(
            """INSERT INTO form_submissions
               (submission_id, form_type, drug_name, app_number, submitted_at, fields_json)
               VALUES (?,?,?,?,?,?)""",
            (
                submission_id,
                form_type,
                fields.get("drug_name", ""),
                fields.get("app_number", ""),
                datetime.utcnow().isoformat(),
                json.dumps(fields),
            ),
        )
        conn.commit()
    return submission_id


def all_drug_names() -> list[str]:
    with _conn() as conn:
        rows = conn.execute("SELECT drug_name FROM drugs ORDER BY drug_name").fetchall()
    return [r["drug_name"] for r in rows]


def all_doc_types() -> list[str]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT doc_type FROM documents ORDER BY doc_type"
        ).fetchall()
    return [r["doc_type"] for r in rows]
