import os
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.security import RoleChecker, get_current_user_payload

router = APIRouter(prefix="/templates", tags=["LaTeX Templates"])


class TemplateCreate(BaseModel):
    name: str
    category: str = "NBA-AICTE"
    description: Optional[str] = None
    latex_template_content: str
    is_default: bool = False


@router.get("/list")
def list_templates(db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id, name, category, description, is_default, created_at FROM templates")
    rows = cur.fetchall()
    
    # If empty, return built-in template metadata
    results = [dict(row) for row in rows]
    if not results:
        results.append({
            "id": 1,
            "name": "Standard NBA/AICTE Outcome-Based Template",
            "category": "NBA-AICTE",
            "description": "Standard publication-grade OBE template with CO-PO articulation matrix and module breakdown.",
            "is_default": True
        })
    return results


@router.get("/{id}")
def get_template(id: int, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM templates WHERE id = ?", (id,))
    row = cur.fetchone()
    if row:
        return dict(row)
    
    # Fallback to local template file
    local_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "templates",
        "curriculum_nba_aicte.tex.j2"
    )
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "id": 1,
            "name": "Standard NBA/AICTE Outcome-Based Template",
            "category": "NBA-AICTE",
            "description": "Standard institutional template",
            "latex_template_content": content,
            "is_default": True
        }
    raise HTTPException(status_code=404, detail="Template not found.")


@router.post("/create")
def create_template(
    t_in: TemplateCreate,
    current_user: Dict[str, Any] = Depends(RoleChecker(allowed_roles=["Admin", "HOD"])),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO templates (name, category, description, latex_template_content, is_default)
        VALUES (?, ?, ?, ?, ?)
        """,
        (t_in.name, t_in.category, t_in.description, t_in.latex_template_content, int(t_in.is_default))
    )
    db.commit()
    t_id = cur.lastrowid
    return {"id": t_id, "name": t_in.name, "status": "Template saved successfully."}
