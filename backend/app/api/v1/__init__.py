from fastapi import APIRouter

from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.curriculum import router as curriculum_router
from backend.app.api.v1.rag import router as rag_router
from backend.app.api.v1.templates import router as templates_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(curriculum_router)
api_router.include_router(rag_router)
api_router.include_router(templates_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
