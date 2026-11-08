from datetime import datetime

try:
    from sqlalchemy import Column, Integer, String, Text, DateTime
    from sqlalchemy.orm import relationship
    from backend.app.core.database import Base
except ImportError:
    Base = object
    Column = Integer = String = Text = DateTime = relationship = lambda *args, **kwargs: None


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    vision = Column(Text, nullable=True)
    mission = Column(Text, nullable=True)
    peos = Column(Text, nullable=True)
    pos = Column(Text, nullable=True)
    psos = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty_members = relationship("User", back_populates="department")
    curricula = relationship("Curriculum", back_populates="department")
