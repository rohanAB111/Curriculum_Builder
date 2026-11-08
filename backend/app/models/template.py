from datetime import datetime

try:
    from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
    from backend.app.core.database import Base
except ImportError:
    Base = object
    Column = Integer = String = Text = Boolean = DateTime = lambda *args, **kwargs: None


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), default="NBA-AICTE", nullable=False)
    description = Column(Text, nullable=True)
    latex_template_content = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
