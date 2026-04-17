from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.sql import func
from app.database.connection import Base

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(String, nullable=True)
    abstract = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    url = Column(String, nullable=True)
    publication_date = Column(String, nullable=True)
    research_domain = Column(String, nullable=True)
    processing_status = Column(String, default="pending")   # pending / processing / complete / failed
    analysis_result = Column(Text, nullable=True)           # JSON string — set after AI analysis
    owner_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
