from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database.connection import Base
class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
