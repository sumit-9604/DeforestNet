from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any
from backend.database.database import Base

# SQLAlchemy ORM Models
class RegionOfInterest(Base):
    __tablename__ = "regions_of_interest"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    geometry = Column(String, nullable=False)  # GeoJSON string Representing boundary polygon
    contact_email = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    alerts = relationship("Alert", back_populates="region")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("regions_of_interest.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    area_ha = Column(Float, nullable=False)
    ndvi_before = Column(Float, nullable=True)
    ndvi_after = Column(Float, nullable=True)
    ndvi_diff = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="Pending")  # Pending, Verified, False Positive, Reported
    risk_level = Column(String, nullable=True)  # Low, Medium, High, Critical
    detected_at = Column(DateTime, server_default=func.now())
    imagery_before_path = Column(String, nullable=True)
    imagery_after_path = Column(String, nullable=True)
    details = Column(String, nullable=True)  # JSON String for extra context (e.g. cloud cover %, satellite name)

    region = relationship("RegionOfInterest", back_populates="alerts")
    reports = relationship("Report", back_populates="alert", cascade="all, delete-orphan")

# Pydantic Schemas
# Region of Interest
class RegionBase(BaseModel):
    name: str
    geometry: str  # GeoJSON
    contact_email: str

class RegionCreate(RegionBase):
    pass

class RegionResponse(RegionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Alert
class AlertBase(BaseModel):
    latitude: float
    longitude: float
    area_ha: float
    ndvi_before: Optional[float] = None
    ndvi_after: Optional[float] = None
    ndvi_diff: Optional[float] = None
    status: str = "Pending"
    risk_level: Optional[str] = None
    region_id: Optional[int] = None
    imagery_before_path: Optional[str] = None
    imagery_after_path: Optional[str] = None
    details: Optional[str] = None

class AlertCreate(AlertBase):
    pass

class AlertUpdateStatus(BaseModel):
    status: str
    risk_level: Optional[str] = None

class AlertResponse(AlertBase):
    id: int
    detected_at: datetime
    region: Optional[RegionResponse] = None

    class Config:
        from_attributes = True
