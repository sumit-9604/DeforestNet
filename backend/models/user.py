from sqlalchemy import Column, Integer, String, DateTime, func
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from backend.database.database import Base

# SQLAlchemy ORM Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="Researcher")  # Admin, Researcher, Authority
    created_at = Column(DateTime, server_default=func.now())

# Pydantic Schemas
class UserBase(BaseModel):
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
