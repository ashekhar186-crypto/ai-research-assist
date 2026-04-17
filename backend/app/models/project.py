from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
