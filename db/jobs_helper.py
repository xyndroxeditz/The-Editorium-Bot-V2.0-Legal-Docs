"""
Jobs helper functions for job creation, applications, and management.
"""
from __future__ import annotations
import sqlite3
import json
import threading
from typing import Optional, List, Dict, Any
import uuid
import time

_LOCK = threading.Lock()

def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_job(db_path: str, job_data: Dict[str, Any]) -> str:
    """Create a new job and return job_id"""
    job_id = str(uuid.uuid4())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO jobs (job_id, creator_id, guild_id, title, description, budget, 
                software_required, deadline, reference_links, status, created_at, message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (job_id, str(job_data["creator_id"]), str(job_data.get("guild_id", "")),
                 job_data["title"], job_data["description"], job_data.get("budget"),
                 job_data.get("software_required"), job_data.get("deadline"),
                 job_data.get("reference_links"), "open", int(time.time()), job_data.get("message_id"))
            )
            conn.commit()
            return job_id
        finally:
            conn.close()

def get_job(db_path: str, job_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

def get_user_jobs(db_path: str, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            if status:
                cur.execute("SELECT * FROM jobs WHERE creator_id = ? AND status = ? ORDER BY created_at DESC", (str(user_id), status))
            else:
                cur.execute("SELECT * FROM jobs WHERE creator_id = ? ORDER BY created_at DESC", (str(user_id),))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def update_job_status(db_path: str, job_id: str, status: str, assigned_to: Optional[str] = None) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            if assigned_to:
                cur.execute("UPDATE jobs SET status = ?, assigned_to = ? WHERE job_id = ?", (status, assigned_to, job_id))
            else:
                cur.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (status, job_id))
            conn.commit()
        finally:
            conn.close()

def create_application(db_path: str, app_data: Dict[str, Any]) -> str:
    """Create application and return application_id"""
    app_id = str(uuid.uuid4())
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO applications (application_id, job_id, applicant_id, message, 
                portfolio_links, status, applied_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (app_id, app_data["job_id"], str(app_data["applicant_id"]),
                 app_data.get("message"), json.dumps(app_data.get("portfolio_links", [])),
                 "pending", int(time.time()))
            )
            conn.commit()
            return app_id
        finally:
            conn.close()

def get_job_applications(db_path: str, job_id: str) -> List[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM applications WHERE job_id = ? ORDER BY applied_at DESC", (job_id,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

def update_application_status(db_path: str, app_id: str, status: str) -> None:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE applications SET status = ? WHERE application_id = ?", (status, app_id))
            conn.commit()
        finally:
            conn.close()

def get_user_applications(db_path: str, user_id: str) -> List[Dict[str, Any]]:
    with _LOCK:
        conn = _get_conn(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM applications WHERE applicant_id = ? ORDER BY applied_at DESC", (str(user_id),))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
