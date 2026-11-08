import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse, PlainTextResponse

from backend.app.core.database import get_db
from backend.app.core.security import RoleChecker, get_current_user_payload
from backend.app.latex.compiler import LatexCompiler
from backend.app.rag.generator import CurriculumGenerator
from backend.app.schemas.curriculum import (
    ArticulationCell,
    AssessmentScheme,
    BookCitation,
    CourseMeta,
    CourseOutcome,
    CurriculumCreate,
    CurriculumResponse,
    CurriculumReviewRequest,
    CurriculumUpdate,
    GenerationRequest,
    ModuleTopic,
)

router = APIRouter(prefix="/curriculum", tags=["Curriculum Management"])


@router.post("/generate", response_model=CurriculumCreate)
async def generate_curriculum_endpoint(
    req: GenerationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_payload)
):
    """
    RAG & Multi-Model Inference Endpoint:
    Orchestrates RAG retrieval, invokes LLM (Ollama or Cloud APIs),
    balances module contact hours, and validates Bloom's taxonomy verbs.
    """
    try:
        generator = CurriculumGenerator(req)
        curriculum = await generator.generate_curriculum()
        return curriculum
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Curriculum generation failed: {str(e)}"
        )


@router.post("/create", response_model=CurriculumResponse)
def create_curriculum(
    curriculum_in: CurriculumCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_payload),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    meta = curriculum_in.course_meta
    
    # Render baseline LaTeX source
    compiler = LatexCompiler()
    rendered_tex = compiler.render_template(curriculum_in)

    cur.execute(
        """
        INSERT INTO curricula (
            course_code, course_name, academic_year, semester, department_id, scheme,
            credits_l, credits_t, credits_p, credits_c, total_contact_hours,
            theory_hours, lab_hours, self_study_hours, course_outcomes, industry_topics,
            modules, articulation_matrix, textbooks, reference_books, assessment_scheme,
            status, created_by, version, latex_source
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, 1, ?)
        """,
        (
            meta.course_code,
            meta.course_name,
            meta.academic_year,
            meta.semester,
            curriculum_in.department_id or current_user.get("department_id", 1),
            meta.scheme,
            meta.credits_l,
            meta.credits_t,
            meta.credits_p,
            meta.credits_c,
            meta.total_contact_hours,
            meta.theory_hours,
            meta.lab_hours,
            meta.self_study_hours,
            json.dumps([co.dict() for co in curriculum_in.course_outcomes]),
            curriculum_in.industry_topics,
            json.dumps([mod.dict() for mod in curriculum_in.modules]),
            json.dumps([cell.dict() for cell in curriculum_in.articulation_matrix]),
            json.dumps([b.dict() for b in curriculum_in.textbooks]),
            json.dumps([r.dict() for r in curriculum_in.reference_books]),
            json.dumps(curriculum_in.assessment_scheme.dict()),
            current_user["user_id"],
            rendered_tex
        )
    )
    db.commit()
    curriculum_id = cur.lastrowid

    return _load_curriculum_by_id(curriculum_id, db)


@router.get("/list", response_model=List[CurriculumResponse])
def list_curricula(
    current_user: Dict[str, Any] = Depends(get_current_user_payload),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    user_role = current_user.get("role", "Faculty")
    
    if user_role == "Faculty":
        cur.execute("SELECT id FROM curricula WHERE created_by = ? ORDER BY id DESC", (current_user["user_id"],))
    else:
        # HOD or Admin can view all departmental curricula
        dept_id = current_user.get("department_id", 1)
        cur.execute("SELECT id FROM curricula WHERE department_id = ? ORDER BY id DESC", (dept_id,))
    
    rows = cur.fetchall()
    return [_load_curriculum_by_id(row["id"], db) for row in rows]


@router.get("/{id}", response_model=CurriculumResponse)
def get_curriculum(
    id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_payload),
    db: sqlite3.Connection = Depends(get_db)
):
    return _load_curriculum_by_id(id, db)


@router.post("/{id}/compile")
def compile_curriculum_endpoint(
    id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_payload),
    db: sqlite3.Connection = Depends(get_db)
):
    curr_obj = _load_curriculum_by_id(id, db)
    compiler = LatexCompiler()

    # Re-render or use edited latex_source
    tex_source = curr_obj.latex_source
    if not tex_source:
        create_payload = _response_to_create(curr_obj)
        tex_source = compiler.render_template(create_payload)

    prefix = f"{curr_obj.course_code}_{curr_obj.course_name}"
    result = compiler.compile(tex_source, output_prefix=prefix)

    if result.success:
        cur = db.cursor()
        cur.execute(
            "UPDATE curricula SET pdf_path = ?, latex_source = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (result.pdf_path, tex_source, id)
        )
        db.commit()
        return {
            "success": True,
            "pdf_path": result.pdf_path,
            "zip_path": result.zip_path,
            "message": "Curriculum compiled successfully into standard NBA PDF."
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "LaTeX compilation failed.",
                "errors": result.errors,
                "log": result.log_output[-1500:]
            }
        )


@router.post("/{id}/review")
def review_curriculum(
    id: int,
    review_in: CurriculumReviewRequest,
    current_user: Dict[str, Any] = Depends(RoleChecker(allowed_roles=["HOD", "Admin"])),
    db: sqlite3.Connection = Depends(get_db)
):
    cur = db.cursor()
    cur.execute(
        """
        UPDATE curricula
        SET status = ?, reviewed_by = ?, review_comments = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (review_in.status, current_user["user_id"], review_in.comments, id)
    )
    db.commit()
    return _load_curriculum_by_id(id, db)


@router.get("/{id}/export/pdf")
def export_pdf(
    id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    curr_obj = _load_curriculum_by_id(id, db)
    if curr_obj.pdf_path and os.path.exists(curr_obj.pdf_path):
        return FileResponse(
            path=curr_obj.pdf_path,
            filename=f"{curr_obj.course_code}_NBA_Curriculum.pdf",
            media_type="application/pdf"
        )
    
    # Auto-compile on the fly if PDF not already generated
    compiler = LatexCompiler()
    create_payload = _response_to_create(curr_obj)
    tex_source = curr_obj.latex_source or compiler.render_template(create_payload)
    result = compiler.compile(tex_source, output_prefix=f"{curr_obj.course_code}_{curr_obj.course_name}")
    
    if result.success and result.pdf_path:
        cur = db.cursor()
        cur.execute("UPDATE curricula SET pdf_path = ? WHERE id = ?", (result.pdf_path, id))
        db.commit()
        return FileResponse(
            path=result.pdf_path,
            filename=f"{curr_obj.course_code}_NBA_Curriculum.pdf",
            media_type="application/pdf"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to compile PDF.")


@router.get("/{id}/export/tex")
def export_tex(
    id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    curr_obj = _load_curriculum_by_id(id, db)
    compiler = LatexCompiler()
    tex = curr_obj.latex_source
    if not tex:
        create_payload = _response_to_create(curr_obj)
        tex = compiler.render_template(create_payload)
    return PlainTextResponse(tex, media_type="text/x-tex")


@router.get("/{id}/export/zip")
def export_zip(
    id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    curr_obj = _load_curriculum_by_id(id, db)
    compiler = LatexCompiler()
    create_payload = _response_to_create(curr_obj)
    tex_source = curr_obj.latex_source or compiler.render_template(create_payload)
    result = compiler.compile(tex_source, output_prefix=f"{curr_obj.course_code}_{curr_obj.course_name}")
    
    if result.success and result.zip_path and os.path.exists(result.zip_path):
        return FileResponse(
            path=result.zip_path,
            filename=f"{curr_obj.course_code}_Curriculum_Bundle.zip",
            media_type="application/zip"
        )
    raise HTTPException(status_code=500, detail="Failed to build ZIP bundle.")


def _load_curriculum_by_id(id: int, db: sqlite3.Connection) -> CurriculumResponse:
    cur = db.cursor()
    cur.execute("SELECT * FROM curricula WHERE id = ?", (id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Curriculum not found.")

    cos = [CourseOutcome(**c) for c in json.loads(row["course_outcomes"])]
    modules = [ModuleTopic(**m) for m in json.loads(row["modules"])]
    matrix = [ArticulationCell(**a) for a in json.loads(row["articulation_matrix"])]
    textbooks = [BookCitation(**b) for b in json.loads(row["textbooks"] or "[]")]
    reference_books = [BookCitation(**r) for r in json.loads(row["reference_books"] or "[]")]
    assessment = AssessmentScheme(**json.loads(row["assessment_scheme"])) if row["assessment_scheme"] else None

    return CurriculumResponse(
        id=row["id"],
        course_code=row["course_code"],
        course_name=row["course_name"],
        academic_year=row["academic_year"],
        semester=row["semester"],
        department_id=row["department_id"],
        scheme=row["scheme"],
        credits_l=row["credits_l"],
        credits_t=row["credits_t"],
        credits_p=row["credits_p"],
        credits_c=row["credits_c"],
        total_contact_hours=row["total_contact_hours"],
        theory_hours=row["theory_hours"],
        lab_hours=row["lab_hours"],
        self_study_hours=row["self_study_hours"],
        course_outcomes=cos,
        industry_topics=row["industry_topics"],
        modules=modules,
        articulation_matrix=matrix,
        textbooks=textbooks,
        reference_books=reference_books,
        assessment_scheme=assessment,
        status=row["status"],
        created_by=row["created_by"],
        reviewed_by=row["reviewed_by"],
        review_comments=row["review_comments"],
        version=row["version"],
        latex_source=row["latex_source"],
        pdf_path=row["pdf_path"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


def _response_to_create(resp: CurriculumResponse) -> CurriculumCreate:
    meta = CourseMeta(
        course_name=resp.course_name,
        course_code=resp.course_code,
        academic_year=resp.academic_year,
        semester=resp.semester,
        scheme=resp.scheme,
        credits_l=resp.credits_l,
        credits_t=resp.credits_t,
        credits_p=resp.credits_p,
        credits_c=resp.credits_c,
        total_contact_hours=resp.total_contact_hours,
        theory_hours=resp.theory_hours,
        lab_hours=resp.lab_hours,
        self_study_hours=resp.self_study_hours
    )
    return CurriculumCreate(
        course_meta=meta,
        course_outcomes=resp.course_outcomes,
        industry_topics=resp.industry_topics,
        modules=resp.modules,
        articulation_matrix=resp.articulation_matrix,
        textbooks=resp.textbooks,
        reference_books=resp.reference_books,
        assessment_scheme=resp.assessment_scheme or AssessmentScheme(),
        department_id=resp.department_id
    )
