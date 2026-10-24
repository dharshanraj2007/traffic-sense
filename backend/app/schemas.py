from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# Auth Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AdminOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Fine Rules
class FineRuleBase(BaseModel):
    violation_type: str
    amount: float
    active: bool = True

class FineRuleOut(FineRuleBase):
    id: int

    class Config:
        from_attributes = True

class FineRuleUpdate(BaseModel):
    amount: Optional[float] = None
    active: Optional[bool] = None

# Status Log
class StatusLogOut(BaseModel):
    id: int
    violation_id: int
    old_status: str
    new_status: str
    notes: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True

# Violations
class ViolationBase(BaseModel):
    plate_number: str
    violation_type: str = "Helmet Violation"
    location: str = "Sector 4 Junction, Smart City"
    occurred_at: Optional[datetime] = None
    fine_amount: Optional[float] = None
    notes: Optional[str] = None

class ViolationCreate(ViolationBase):
    pass

class ViolationUpdate(BaseModel):
    plate_number: Optional[str] = None
    violation_type: Optional[str] = None
    location: Optional[str] = None
    fine_amount: Optional[float] = None
    needs_review: Optional[bool] = None
    notes: Optional[str] = None

class ViolationStatusUpdate(BaseModel):
    status: str # Pending, Paid, Cancelled
    payment_ref: Optional[str] = None
    notes: Optional[str] = None

class ViolationOut(BaseModel):
    id: int
    fine_ref: str
    plate_number: str
    violation_type: str
    location: str
    occurred_at: datetime
    fine_amount: float
    status: str
    source: str
    confidence: Optional[float] = None
    needs_review: bool
    evidence_url: Optional[str] = None
    plate_crop_url: Optional[str] = None
    video_job_id: Optional[int] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    payment_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    status_logs: List[StatusLogOut] = []

    class Config:
        from_attributes = True

class ViolationListResponse(BaseModel):
    items: List[ViolationOut]
    total: int
    page: int
    page_size: int
    total_pages: int

# Dashboard
class DailyViolationStat(BaseModel):
    date: str
    count: int

class StatusStat(BaseModel):
    name: str
    value: int

class DashboardStats(BaseModel):
    total_violations: int
    pending_fines: int
    paid_fines: int
    cancelled_fines: int
    total_collected_amount: float
    total_pending_amount: float
    needs_review_count: int
    daily_stats: List[DailyViolationStat]
    status_distribution: List[StatusStat]
    recent_violations: List[ViolationOut]

# Video Jobs
class VideoJobOut(BaseModel):
    id: int
    filename: str
    status: str
    progress: int
    total_frames: int
    vehicles_detected: int
    violations_found: int
    error: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
    violation_ids: List[int] = []

    class Config:
        from_attributes = True

class VideoAnalyzeResponse(BaseModel):
    job_id: int
    message: str
    filename: str

# Public Fine Lookup
class PublicFineResponse(BaseModel):
    plate_number: str
    total_violations: int
    pending_violations: int
    total_pending_amount: float
    violations: List[ViolationOut]
