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


class ProgramSpecificOutcome(BaseModel):
    pso_id: str = Field(default="PSO1", example="PSO1")
    statement: str = Field(default="", example="Professional Skills: Design and develop enterprise cloud and edge systems.")

class CourseMeta(BaseModel):
    course_name: str = Field(default="Cloud-Native Distributed Systems & Microservices")
    course_code: str = Field(default="22CS501")
    academic_year: str = Field(default="2025-26")
    semester: str = Field(default="V")
    department: str = Field(default="Computer Science & Engineering")
    department_code: str = Field(default="CSE")
    scheme: str = Field(default="NEP 2020 / AICTE Model Curriculum")
    course_type: str = Field(default="Integrated (Theory + Practical)", description="Theory, Practical, Integrated, Project")
    credits_l: int = Field(default=3)
    credits_t: int = Field(default=0)
    credits_p: int = Field(default=2)
    credits_c: int = Field(default=4)
    total_contact_hours: int = Field(default=45)
    theory_hours: int = Field(default=45)
    lab_hours: int = Field(default=30)
    self_study_hours: int = Field(default=15)
    psos: List[ProgramSpecificOutcome] = Field(default_factory=list)


class CourseOutcome(BaseModel):
    co_id: str = Field(default="CO1")
    description: str = Field(default="Understand core principles.")
    domain: str = Field(default="Cognitive", description="Cognitive, Psychomotor, Affective")
    bloom_level: str = Field(default="L2: Understand", description="Specific cognitive, psychomotor or affective level")
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
    # Comprehensive Institutional Assessment Scheme Breakdown
    cia_marks: int = Field(default=20, description="Continuous Internal Assessment (Theory)")
    mse_marks: int = Field(default=30, description="Mid Semester Examination (Theory)")
    ciap_marks: int = Field(default=25, description="Continuous Internal Assessment for Practical / Lab")
    ese_marks: int = Field(default=50, description="End Semester Examination (Theory)")
    esep_marks: int = Field(default=25, description="End Semester Examination for Practical / Oral")
    sla_marks: int = Field(default=20, description="Self Learning Assessment / Mini-Project")
    total_marks: int = Field(default=150, description="Total aggregated course marks")
    passing_threshold_pct: float = Field(default=40.0)
    rubrics_summary: str = Field(
        default="Comprehensive assessment comprises Continuous Internal Assessment (CIA & MSE), Practical Lab Performance (CIAP & ESEP), and Self-Learning Assessment (SLA)."
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
    num_cos: int = Field(default=6)
    model_provider: str = Field(default="ollama")
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    ollama_url: Optional[str] = None
    temperature: float = Field(default=0.2)
