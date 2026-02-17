"""Database models and schema."""
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import os

DB_PATH = Path(os.getenv("JOBBOT_DB", "/tmp/jobbot.db"))


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE NOT NULL,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Filters table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            keywords TEXT NOT NULL,
            location TEXT NOT NULL,
            salary_min INTEGER,
            level TEXT,
            job_type TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            salary TEXT,
            job_type TEXT,
            source TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            description TEXT,
            posted_date TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Applied jobs tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applied_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    # Sent jobs (to avoid duplicates in telegram)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()


# Helper functions
def add_user(telegram_id: str, username: str = None) -> int:
    """Add or get user."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
        conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user_id = cursor.fetchone()[0]
    finally:
        conn.close()
    return user_id


def set_filters(user_id: int, keywords: list, location: str, salary_min: int = None, level: str = None, job_type: str = None):
    """Set user filters."""
    conn = get_connection()
    cursor = conn.cursor()
    keywords_str = json.dumps(keywords)
    job_type_str = json.dumps(job_type) if isinstance(job_type, list) else job_type
    
    cursor.execute("""
        INSERT OR REPLACE INTO filters (user_id, keywords, location, salary_min, level, job_type)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, keywords_str, location, salary_min, level, job_type_str))
    conn.commit()
    conn.close()


def get_filters(user_id: int) -> dict:
    """Get user filters."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT keywords, location, salary_min, level, job_type FROM filters WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return {
        "keywords": json.loads(row[0]),
        "location": row[1],
        "salary_min": row[2],
        "level": row[3],
        "job_type": json.loads(row[4]) if row[4] else None,
    }


def add_job(title: str, company: str, location: str, salary: str, job_type: str, source: str, url: str, description: str = None) -> int:
    """Add job to database."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO jobs (title, company, location, salary, job_type, source, url, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, company, location, salary, job_type, source, url, description))
        conn.commit()
        job_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM jobs WHERE url = ?", (url,))
        job_id = cursor.fetchone()[0]
    finally:
        conn.close()
    return job_id


def get_unsent_jobs(user_id: int, limit: int = 10) -> list:
    """Get jobs not yet sent to user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT j.id, j.title, j.company, j.location, j.salary, j.job_type, j.source, j.url
        FROM jobs j
        WHERE j.id NOT IN (
            SELECT job_id FROM sent_jobs WHERE user_id = ?
        )
        ORDER BY j.scraped_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def mark_sent(user_id: int, job_id: int):
    """Mark job as sent to user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sent_jobs (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    conn.commit()
    conn.close()


def mark_applied(user_id: int, job_id: int):
    """Mark job as applied."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO applied_jobs (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    conn.commit()
    conn.close()


# Initialize on import
init_db()
