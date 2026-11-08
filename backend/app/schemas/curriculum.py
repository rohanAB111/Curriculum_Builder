from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CourseMeta(BaseModel):
    course_name: str = Field(..., example="Advanced Distributed Systems & Cloud Architecture")
    course_code: str = Field(..., example="22CS501")
    academic_year: str = Field(default="2025-26", example="2025-26")
    semester: str = Field(default="V", example="V")
    department: str = Field(default="Computer Science & Engineering", example="Computer Science & Engineering")
    department_code: str = Field(default="CSE", example="CSE")
    scheme: str = Field(default="NEP 2020 / AICTE Model Curriculum", example="NEP 2020 / AICTE Model Curriculum")
    credits_l: int = Field(default=3, ge=0, le=6, description="Lectures per week")
    credits_t: int = Field(default=0, ge=0, le=4, description="Tutorials per week")
    credits_p: int = Field(default=2, ge=0, le=6, description="Practicals/Lab per week")
    credits_c: int = Field(default=4, ge=1, le=10, description="Total Credits")
    total_contact_hours: int = Field(default=45, ge=20, le=120, description="Total theory/lecture contact hours")
    theory_hours: int = Field(default=45, ge=0)
    lab_hours: int = Field(default=30, ge=0)
    self_study_hours: int = Field(default=15, ge=0)


class CourseOutcome(BaseModel):
    co_id: str = Field(..., example="CO1")
    description: str = Field(..., example="Understand the architectural foundations and consensus protocols of distributed systems.")
    bloom_level: str = Field(..., example="L2: Understand")
    target_attainment_pct: Optional[float] = 70.0


class ModuleTopic(BaseModel):
    module_number: int = Field(..., ge=1, le=10)
    title: str = Field(..., example="Foundations of Distributed State & Consensus")
    contact_hours: int = Field(..., ge=1, description="Allocated hours for this unit")
    weightage_pct: float = Field(default=20.0, description="Percentage of marks weightage")
    cognitive_level: str = Field(default="L2-L3", example="L2-L3")
    topics: List[str] = Field(..., description="Itemized lecture topics")
    industry_integration_tags: List[str] = Field(default_factory=list, description="Emerging tools/platforms injected")


class ArticulationCell(BaseModel):
    co_id: str
    target_id: str
    correlation_level: int = Field(ge=0, le=3, description="0=No correlation (-), 1=Slight, 2=Moderate, 3=Substantial")
    rationale: Optional[str] = None


class BookCitation(BaseModel):
    book_type: str = Field(default="Textbook", example="Textbook")
    authors: str = Field(..., example="Martin Kleppmann")
    title: str = Field(..., example="Designing Data-Intensive Applications")
    edition: str = Field(default="1st Edition", example="1st Edition")
    publisher: str = Field(default="O'Reilly Media", example="O'Reilly Media")
    year: int = Field(default=2023, example=2023)
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
    status: str = Field(..., example="APPROVED")
    comments: Optional[str] = Field(None, example="Approved. Complies with AICTE modern computing mandate.")


class GenerationRequest(BaseModel):
    course_meta: CourseMeta
    reference_syllabus_text: Optional[str] = None
    course_outcomes: Optional[List[CourseOutcome]] = None
    industry_topics: Optional[str] = Field(
        default="Edge AI, vLLM, TensorRT-LLM, Kafka Streams, TinyML, LangGraph",
        description="Emerging trending topics to blend into Modules 4-6"
    )
    num_modules: int = Field(default=5, ge=4, le=6)
    model_provider: str = Field(default="ollama", example="ollama")
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    ollama_url: Optional[str] = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
