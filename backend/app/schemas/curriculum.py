from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:  # type: ignore
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__
    def Field(default=None, **kwargs):  # type: ignore
        return default


class CourseMeta(BaseModel):
    course_name: str = Field(default="Advanced Distributed Systems & Cloud Architecture")
    course_code: str = Field(default="22CS501")
    academic_year: str = Field(default="2025-26")
    semester: str = Field(default="V")
    department: str = Field(default="Computer Science & Engineering")
    department_code: str = Field(default="CSE")
    scheme: str = Field(default="NEP 2020 / AICTE Model Curriculum")
    credits_l: int = Field(default=3)
    credits_t: int = Field(default=0)
    credits_p: int = Field(default=2)
    credits_c: int = Field(default=4)
    total_contact_hours: int = Field(default=45)
    theory_hours: int = Field(default=45)
    lab_hours: int = Field(default=30)
    self_study_hours: int = Field(default=15)


class CourseOutcome(BaseModel):
    co_id: str = Field(default="CO1")
    description: str = Field(default="Understand core engineering principles.")
    bloom_level: str = Field(default="L2: Understand")
    target_attainment_pct: Optional[float] = 70.0


class ModuleTopic(BaseModel):
    module_number: int = Field(default=1)
    title: str = Field(default="Foundations")
    contact_hours: int = Field(default=9)
    weightage_pct: float = Field(default=20.0)
    cognitive_level: str = Field(default="L2-L3")
    topics: List[str] = Field(default_factory=list)
    industry_integration_tags: List[str] = Field(default_factory=list)


class ArticulationCell(BaseModel):
    co_id: str
    target_id: str
    correlation_level: int = Field(default=0)
    rationale: Optional[str] = None


class BookCitation(BaseModel):
    book_type: str = Field(default="Textbook")
    authors: str = Field(default="")
    title: str = Field(default="")
    edition: str = Field(default="1st Edition")
    publisher: str = Field(default="")
    year: int = Field(default=2024)
    isbn: Optional[str] = None


class AssessmentScheme(BaseModel):
    cie_marks: int = Field(default=50)
    see_marks: int = Field(default=50)
    total_marks: int = Field(default=100)
    continuous_tests_marks: int = Field(default=30)
    quizzes_assignments_marks: int = Field(default=20)
    see_duration_hours: int = Field(default=3)
    rubrics_summary: str = Field(
        default="Continuous assessment comprises 2 internal tests (30 marks) and active problem-solving/quizzes (20 marks). SEE evaluates comprehensive analytical and design mastery across all modules."
    )


class CurriculumCreate(BaseModel):
    course_meta: CourseMeta
    course_outcomes: List[CourseOutcome]
    industry_topics: Optional[str] = None
    modules: List[ModuleTopic]
    articulation_matrix: List[ArticulationCell]
    textbooks: List[BookCitation]
    reference_books: List[BookCitation]
    assessment_scheme: AssessmentScheme
    department_id: Optional[int] = 1


class CurriculumUpdate(BaseModel):
    course_meta: Optional[CourseMeta] = None
    course_outcomes: Optional[List[CourseOutcome]] = None
    industry_topics: Optional[str] = None
    modules: Optional[List[ModuleTopic]] = None
    articulation_matrix: Optional[List[ArticulationCell]] = None
    textbooks: Optional[List[BookCitation]] = None
    reference_books: Optional[List[BookCitation]] = None
    assessment_scheme: Optional[AssessmentScheme] = None
    latex_source: Optional[str] = None


class CurriculumResponse(BaseModel):
    id: int
    course_code: str
    course_name: str
    academic_year: str
    semester: str
    department_id: int
    scheme: str
    credits_l: int
    credits_t: int
    credits_p: int
    credits_c: int
    total_contact_hours: int
    theory_hours: int
    lab_hours: int
    self_study_hours: int
    course_outcomes: List[CourseOutcome]
    industry_topics: Optional[str]
    modules: List[ModuleTopic]
    articulation_matrix: List[ArticulationCell]
    textbooks: List[BookCitation]
    reference_books: List[BookCitation]
    assessment_scheme: Optional[AssessmentScheme]
    status: str
    created_by: int
    reviewed_by: Optional[int] = None
    review_comments: Optional[str] = None
    version: int
    latex_source: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CurriculumReviewRequest(BaseModel):
    status: str = Field(default="APPROVED")
    comments: Optional[str] = None


class GenerationRequest(BaseModel):
    course_meta: CourseMeta
    reference_syllabus_text: Optional[str] = None
    course_outcomes: Optional[List[CourseOutcome]] = None
    industry_topics: Optional[str] = Field(
        default="Edge AI, vLLM, TensorRT-LLM, Kafka Streams, TinyML, LangGraph"
    )
    num_modules: int = Field(default=5)
    model_provider: str = Field(default="ollama")
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    ollama_url: Optional[str] = None
    temperature: float = Field(default=0.2)
