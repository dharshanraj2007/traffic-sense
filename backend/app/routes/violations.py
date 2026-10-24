import datetime
import random
import string
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models import Violation, FineRule, StatusLog, Admin
from app.schemas import (
    ViolationOut, ViolationCreate, ViolationUpdate,
    ViolationStatusUpdate, ViolationListResponse
)
from app.auth import get_current_admin
from app.services.storage import get_storage_service

router = APIRouter(prefix="/api/violations", tags=["violations"])

def generate_fine_ref() -> str:
    date_str = datetime.datetime.utcnow().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"FN-{date_str}-{random_str}"

@router.get("", response_model=ViolationListResponse)
def list_violations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    needs_review: Optional[bool] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    video_job_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    query = db.query(Violation)

    if video_job_id is not None:
        query = query.filter(Violation.video_job_id == video_job_id)

    if search:
        search_pattern = f"%{search.strip().upper()}%"
        query = query.filter(
            (Violation.plate_number.like(search_pattern)) |
            (Violation.fine_ref.like(search_pattern)) |
            (Violation.location.like(search_pattern))
        )
    
    if status and status != "All":
        query = query.filter(Violation.status == status)

    if source and source != "All":
        query = query.filter(Violation.source == source)

    if needs_review is not None:
        query = query.filter(Violation.needs_review == needs_review)

    if start_date:
        try:
            sd = datetime.datetime.fromisoformat(start_date)
            query = query.filter(Violation.occurred_at >= sd)
        except ValueError:
            pass

    if end_date:
        try:
            ed = datetime.datetime.fromisoformat(end_date)
            # include full day
            ed = ed.replace(hour=23, minute=59, second=59)
            query = query.filter(Violation.occurred_at <= ed)
        except ValueError:
            pass

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size
    items = query.order_by(desc(Violation.occurred_at)).offset(offset).limit(page_size).all()

    return ViolationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("", response_model=ViolationOut, status_code=status.HTTP_201_CREATED)
def create_manual_violation(
    plate_number: str = Form(...),
    violation_type: str = Form("Helmet Violation"),
    location: str = Form("Sector 4 Junction, Smart City"),
    fine_amount: Optional[float] = Form(None),
    occurred_at: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    evidence_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    # Lookup fine amount from fine rules if not explicitly supplied
    if fine_amount is None:
        rule = db.query(FineRule).filter(FineRule.violation_type == violation_type).first()
        fine_amount = rule.amount if rule else 1000.0

    occ_dt = datetime.datetime.utcnow()
    if occurred_at:
        try:
            occ_dt = datetime.datetime.fromisoformat(occurred_at)
        except Exception:
            pass

    # Save evidence file if provided
    evidence_url = None
    if evidence_file and evidence_file.filename:
        storage = get_storage_service()
        file_bytes = evidence_file.file.read()
        evidence_url = storage.save_image(file_bytes, f"manual_{evidence_file.filename}")

    # Generate unique fine ref
    while True:
        ref = generate_fine_ref()
        if not db.query(Violation).filter(Violation.fine_ref == ref).first():
            break

    violation = Violation(
        fine_ref=ref,
        plate_number=plate_number.strip().upper(),
        violation_type=violation_type,
        location=location.strip(),
        occurred_at=occ_dt,
        fine_amount=float(fine_amount),
        status="Pending",
        source="Manual",
        evidence_url=evidence_url,
        notes=notes
    )
    db.add(violation)
    db.commit()
    db.refresh(violation)

    # Initial status log
    log = StatusLog(
        violation_id=violation.id,
        old_status="None",
        new_status="Pending",
        notes="Manual violation record created"
    )
    db.add(log)
    db.commit()
    db.refresh(violation)

    return violation

@router.get("/{violation_id}", response_model=ViolationOut)
def get_violation(
    violation_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")
    return v

@router.put("/{violation_id}", response_model=ViolationOut)
def update_violation(
    violation_id: int,
    data: ViolationUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    if data.plate_number is not None:
        v.plate_number = data.plate_number.strip().upper()
    if data.violation_type is not None:
        v.violation_type = data.violation_type
    if data.location is not None:
        v.location = data.location
    if data.fine_amount is not None:
        v.fine_amount = data.fine_amount
    if data.needs_review is not None:
        v.needs_review = data.needs_review
    if data.notes is not None:
        v.notes = data.notes

    db.commit()
    db.refresh(v)
    return v

@router.patch("/{violation_id}/status", response_model=ViolationOut)
def update_violation_status(
    violation_id: int,
    status_data: ViolationStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")

    old_status = v.status
    new_status = status_data.status

    if new_status not in ["Pending", "Paid", "Cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status value. Must be Pending, Paid, or Cancelled.")

    v.status = new_status
    if new_status == "Paid":
        v.paid_at = datetime.datetime.utcnow()
        v.payment_ref = status_data.payment_ref or f"PAY-{uuid_hex()[:8].upper()}"
    elif new_status == "Pending":
        v.paid_at = None
        v.payment_ref = None

    if status_data.notes:
        v.notes = f"{v.notes or ''}\nStatus update: {status_data.notes}".strip()

    # Log status change
    log = StatusLog(
        violation_id=v.id,
        old_status=old_status,
        new_status=new_status,
        notes=status_data.notes or f"Status changed from {old_status} to {new_status}"
    )
    db.add(log)
    db.commit()
    db.refresh(v)
    return v

def uuid_hex():
    import uuid
    return uuid.uuid4().hex

@router.delete("/{violation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_violation(
    violation_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    db.delete(v)
    db.commit()
    return None
