from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.database.connection import Base
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    role = Column(String)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
