import enum
from datetime import datetime

try:
    from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
    from sqlalchemy.orm import relationship
    from backend.app.core.database import Base
except ImportError:
    Base = object
    Column = Integer = String = Text = DateTime = ForeignKey = SQLEnum = relationship = lambda *args, **kwargs: None


class CurriculumStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Curriculum(Base):
    __tablename__ = "curricula"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(50), nullable=False, index=True)
    course_name = Column(String(255), nullable=False)
    academic_year = Column(String(50), nullable=False)
    semester = Column(String(20), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    scheme = Column(String(100), nullable=False, default="NEP 2020 / AICTE")
    
    credits_l = Column(Integer, default=3, nullable=False)
    credits_t = Column(Integer, default=0, nullable=False)
    credits_p = Column(Integer, default=0, nullable=False)
    credits_c = Column(Integer, default=3, nullable=False)
    
    total_contact_hours = Column(Integer, default=45, nullable=False)
    theory_hours = Column(Integer, default=45, nullable=False)
    lab_hours = Column(Integer, default=0, nullable=False)
    self_study_hours = Column(Integer, default=15, nullable=False)
    
    course_outcomes = Column(Text, nullable=False)
    industry_topics = Column(Text, nullable=True)
    modules = Column(Text, nullable=False)
    articulation_matrix = Column(Text, nullable=False)
    textbooks = Column(Text, nullable=True)
    reference_books = Column(Text, nullable=True)
    assessment_scheme = Column(Text, nullable=True)
    
    status = Column(SQLEnum(CurriculumStatus), default=CurriculumStatus.DRAFT, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_comments = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    
    latex_source = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="curricula")
    creator = relationship("User", foreign_keys=[created_by], back_populates="curricula")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
