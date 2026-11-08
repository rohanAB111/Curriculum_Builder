import enum
from datetime import datetime

try:
    from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
    from sqlalchemy.orm import relationship
    from backend.app.core.database import Base
except ImportError:
    Base = object
    Column = Integer = String = Boolean = DateTime = ForeignKey = SQLEnum = relationship = lambda *args, **kwargs: None


class RoleEnum(str, enum.Enum):
    ADMIN = "Admin"
    HOD = "HOD"
    FACULTY = "Faculty"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.FACULTY, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", back_populates="faculty_members")
    curricula = relationship("Curriculum", back_populates="creator", foreign_keys="Curriculum.created_by")
