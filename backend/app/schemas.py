from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional, Any, List

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    institution: Optional[str] = None
    research_interests: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Auth Schemas ---
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: Any
    email: str

# --- Paper Schemas ---
class PaperBase(BaseModel):
    title: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[str] = None
    file_size: Optional[int] = None
    project_id: Optional[int] = None

class Paper(PaperBase):
    id: int
    owner_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Analysis Schemas ---
class AnalysisBase(BaseModel):
    analysis_type: str
    query: str
    status: str = "pending"

class AnalysisCreate(AnalysisBase):
    project_id: Optional[int] = None

class Analysis(AnalysisBase):
    id: int
    result: Optional[Any] = None
    created_at: datetime
    owner_id: int
    model_config = ConfigDict(from_attributes=True)
