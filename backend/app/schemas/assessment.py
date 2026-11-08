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

from backend.app.schemas.curriculum import CourseMeta, CourseOutcome, AssessmentScheme


class AssessmentComponentDetail(BaseModel):
    component_name: str  # e.g., "CIA - Continuous Internal Assessment"
    component_code: str  # "CIA", "MSE", "CIAP", "ESE", "ESEP", "SLA"
    selected_methods: List[str]  # e.g., ["Technical Reel / Short Video", "Case Study Analysis"]
    allocated_marks: int
    target_cos: List[str]  # e.g., ["CO1", "CO2"]
    bloom_focus: str  # e.g., "L3 (Apply), L4 (Analyze)"
    activity_description: str
    faculty_guidelines: str
    student_deliverables: str
    rubric_criteria: List[Dict[str, Any]]  # Specific criteria with 4 levels


class AssessmentPlanRequest(BaseModel):
    course_meta: CourseMeta
    course_outcomes: List[CourseOutcome]
    assessment_scheme: AssessmentScheme
    cia_methods: List[str] = Field(default_factory=lambda: ["Case Study Analysis", "Technical Video / Reel Explainer"])
    mse_methods: List[str] = Field(default_factory=lambda: ["Higher-Order Thinking Questions (HOTS)", "Bloom's Balanced Descriptive Exam"])
    ciap_methods: List[str] = Field(default_factory=lambda: ["Continuous Experiment Logbook Audit", "Live Code Debugging & Implementation"])
    ese_methods: List[str] = Field(default_factory=lambda: ["Comprehensive Theory Exam Blueprint", "Bloom's Balanced Part A & B Question Paper"])
    esep_methods: List[str] = Field(default_factory=lambda: ["Hands-on System Demonstration", "External Viva-Voce & Problem Diagnosis"])
    sla_methods: List[str] = Field(default_factory=lambda: ["NPTEL / MOOC Certification Audit", "Capstone Open-Source Mini-Project"])
    faculty_prompt: Optional[str] = Field(
        default="Design modern engaging assessments for CIA using technical reels and real-world system failure case studies. For CIAP, focus on live containerized deployments and Git commit logs.",
        description="Faculty specific instructions on student deliverables and scenarios"
    )
    model_provider: str = Field(default="ollama")
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    ollama_url: Optional[str] = None
    temperature: float = Field(default=0.2)


class AssessmentPlanResponse(BaseModel):
    course_code: str
    course_name: str
    academic_year: str
    semester: str
    total_marks: int
    components: List[AssessmentComponentDetail]
    attainment_methodology: str
    latex_source: Optional[str] = None
    pdf_path: Optional[str] = None
