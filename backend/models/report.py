from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from backend.database.database import Base

# SQLAlchemy ORM Model
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    file_path = Column(String, nullable=False)
    narrative_summary = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    generated_at = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=False, default="Pending")  # Pending, Sent, Failed

    alert = relationship("Alert", back_populates="reports")

# Pydantic Schemas
class ReportBase(BaseModel):
    alert_id: int
    file_path: str
    narrative_summary: str
    recommended_action: str
    recipient_email: str
    status: str = "Pending"

class ReportCreate(BaseModel):
    alert_id: int
    recipient_email: Optional[str] = None  # Will default to region contact if not provided

class ReportResponse(ReportBase):
    id: int
    generated_at: datetime

    class Config:
        from_attributes = True
