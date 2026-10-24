import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class FineRule(Base):
    __tablename__ = "fine_rules"

    id = Column(Integer, primary_key=True, index=True)
    violation_type = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False, default=1000.0)
    active = Column(Boolean, default=True)

class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), default="queued") # queued, processing, completed, failed
    progress = Column(Integer, default=0) # 0 to 100
    total_frames = Column(Integer, default=0)
    vehicles_detected = Column(Integer, default=0)
    violations_found = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    violations = relationship("Violation", back_populates="video_job", cascade="all, delete-orphan")

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    fine_ref = Column(String(50), unique=True, index=True, nullable=False)
    plate_number = Column(String(50), index=True, nullable=False)
    violation_type = Column(String(100), nullable=False, default="Helmet Violation")
    location = Column(String(255), nullable=False, default="Sector 4 Junction, Smart City")
    occurred_at = Column(DateTime, default=datetime.datetime.utcnow)
    fine_amount = Column(Float, nullable=False, default=1000.0)
    status = Column(String(50), default="Pending") # Pending, Paid, Cancelled
    source = Column(String(50), default="Manual") # Manual, AI
    confidence = Column(Float, nullable=True)
    needs_review = Column(Boolean, default=False)
    evidence_url = Column(String(500), nullable=True)
    plate_crop_url = Column(String(500), nullable=True)
    video_job_id = Column(Integer, ForeignKey("video_jobs.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_ref = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    video_job = relationship("VideoJob", back_populates="violations")
    status_logs = relationship("StatusLog", back_populates="violation", cascade="all, delete-orphan")

class StatusLog(Base):
    __tablename__ = "status_logs"

    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    notes = Column(String(255), nullable=True)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)

    violation = relationship("Violation", back_populates="status_logs")
