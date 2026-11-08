import os
import shutil
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from backend.app.core.config import settings
from backend.app.core.security import get_current_user_payload
from backend.app.rag.engine import SyllabusParser, rag_store

router = APIRouter(prefix="/rag", tags=["RAG Pipeline & Context Store"])


@router.post("/upload")
async def upload_reference_document(
    file: UploadFile = File(...),
    document_title: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user_payload)
):
    """
    Ingests syllabus PDF/DOCX/TXT reference documents into the hierarchical RAG index.
    Preserves module and lecture hierarchies without breaking across topics.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = file.filename or "uploaded_syllabus.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text = SyllabusParser.extract_text_from_file(file_path)
        doc_id = os.path.splitext(filename)[0]
        chunks = SyllabusParser.hierarchical_chunk(raw_text, doc_id=doc_id)
        rag_store.add_documents(chunks)

        return {
            "status": "success",
            "filename": filename,
            "document_title": document_title or filename,
            "extracted_length": len(raw_text),
            "chunks_created": len(chunks),
            "total_indexed_chunks": len(rag_store.chunks),
            "message": "Reference syllabus ingested and indexed successfully."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse and index document: {str(e)}"
        )


@router.get("/index-status")
def get_rag_status(current_user: Dict[str, Any] = Depends(get_current_user_payload)):
    return {
        "total_chunks": len(rag_store.chunks),
        "unique_terms": len(rag_store.doc_frequencies),
        "chunk_types": {
            "parents": sum(1 for c in rag_store.chunks if c.section_type == "module_parent"),
            "children": sum(1 for c in rag_store.chunks if c.section_type == "topic_child"),
        }
    }


@router.post("/search")
def search_rag(
    query: str,
    industry_focus: Optional[str] = None,
    top_k: int = 5,
    current_user: Dict[str, Any] = Depends(get_current_user_payload)
):
    results = rag_store.hybrid_search_and_rerank(
        query=query,
        industry_focus=industry_focus,
        top_k=top_k
    )
    return [
        {
            "chunk_id": chunk.chunk_id,
            "score": round(score, 4),
            "section_type": chunk.section_type,
            "module_num": chunk.module_num,
            "text": chunk.text,
            "metadata": chunk.metadata
        }
        for chunk, score in results
    ]
