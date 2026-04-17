from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    analysis_type = Column(String)  # e.g., 'literature_review'
    query = Column(String)
    result = Column(JSON)
    status = Column(String, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
