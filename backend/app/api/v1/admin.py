import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import RoleChecker, get_current_user_payload

router = APIRouter(prefix="/admin", tags=["Admin & System Configuration"])


class DepartmentCreate(BaseModel):
    code: str
    name: str
    vision: Optional[str] = None
    mission: Optional[str] = None


@router.get("/users")
def list_all_users(
    current_user: Dict[str, Any] = Depends(RoleChecker(allowed_roles=["Admin"])),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    cur.execute("SELECT id, email, full_name, role, department_id, is_active, created_at FROM users")
    return [dict(r) for r in cur.fetchall()]


@router.get("/departments")
def list_departments(db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM departments")
    return [dict(r) for r in cur.fetchall()]


@router.post("/departments")
def create_department(
    dept_in: DepartmentCreate,
    current_user: Dict[str, Any] = Depends(RoleChecker(allowed_roles=["Admin"])),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO departments (code, name, vision, mission) VALUES (?, ?, ?, ?)",
            (dept_in.code, dept_in.name, dept_in.vision, dept_in.mission)
        )
        db.commit()
        return {"id": cur.lastrowid, "code": dept_in.code, "name": dept_in.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create department: {str(e)}")


@router.get("/system-config")
def get_system_config(current_user: Dict[str, Any] = Depends(RoleChecker(allowed_roles=["Admin"]))):
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "default_llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "latex_compiler": settings.LATEX_COMPILER_BIN,
    }
