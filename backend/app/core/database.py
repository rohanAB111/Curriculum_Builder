import json
import os
import sqlite3
from typing import Any, Dict, Generator, List, Optional

from backend.app.core.config import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    Base = object  # type: ignore
    engine = None
    SessionLocal = None


class StandaloneDB:
    def __init__(self, db_path: str = "curriculumai.db"):
        self.db_path = db_path
        self._init_schema()

    def get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        conn = self.get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                vision TEXT,
                mission TEXT,
                peos TEXT,
                pos TEXT,
                psos TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Faculty',
                department_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'NBA-AICTE',
                description TEXT,
                latex_template_content TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS curricula (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                course_name TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                semester TEXT NOT NULL,
                department_id INTEGER NOT NULL,
                scheme TEXT NOT NULL,
                credits_l INTEGER NOT NULL DEFAULT 3,
                credits_t INTEGER NOT NULL DEFAULT 0,
                credits_p INTEGER NOT NULL DEFAULT 0,
                credits_c INTEGER NOT NULL DEFAULT 3,
                total_contact_hours INTEGER NOT NULL DEFAULT 45,
                theory_hours INTEGER NOT NULL DEFAULT 45,
                lab_hours INTEGER NOT NULL DEFAULT 0,
                self_study_hours INTEGER NOT NULL DEFAULT 15,
                course_outcomes TEXT NOT NULL,
                industry_topics TEXT,
                modules TEXT NOT NULL,
                articulation_matrix TEXT NOT NULL,
                textbooks TEXT,
                reference_books TEXT,
                assessment_scheme TEXT,
                status TEXT NOT NULL DEFAULT 'DRAFT',
                created_by INTEGER NOT NULL,
                reviewed_by INTEGER,
                review_comments TEXT,
                version INTEGER DEFAULT 1,
                latex_source TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Seed default department and admin if empty
        cur.execute("SELECT COUNT(*) as count FROM departments")
        if cur.fetchone()["count"] == 0:
            cur.execute("""
                INSERT INTO departments (code, name, vision, mission)
                VALUES ('CSE', 'Computer Science and Engineering', 
                        'To excel in computer engineering education and industry innovation.',
                        'Provide quality education, foster applied research, and instill ethical values.')
            """)
        
        cur.execute("SELECT COUNT(*) as count FROM users")
        if cur.fetchone()["count"] == 0:
            from backend.app.core.security import hash_password
            admin_pwd = hash_password("Admin@123")
            faculty_pwd = hash_password("Faculty@123")
            hod_pwd = hash_password("Hod@123")
            cur.execute("""
                INSERT INTO users (email, full_name, hashed_password, role, department_id)
                VALUES ('admin@curriculumai.edu', 'System Administrator', ?, 'Admin', 1),
                       ('hod.cse@curriculumai.edu', 'Dr. Rajesh Sharma (HOD)', ?, 'HOD', 1),
                       ('faculty@curriculumai.edu', 'Prof. Ananya Iyer', ?, 'Faculty', 1)
            """, (admin_pwd, hod_pwd, faculty_pwd))

        conn.commit()
        conn.close()


db_manager = StandaloneDB()


def get_db():
    conn = db_manager.get_conn()
    try:
        yield conn
    finally:
        conn.close()
