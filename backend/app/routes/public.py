from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Violation
from app.schemas import PublicFineResponse, ViolationOut

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/fine/{plate}", response_model=PublicFineResponse)
def lookup_fine_by_plate(plate: str, db: Session = Depends(get_db)):
    clean_plate = plate.strip().upper().replace(" ", "").replace("-", "")
    violations = db.query(Violation).filter(
        Violation.plate_number.like(f"%{clean_plate}%")
    ).order_by(desc(Violation.occurred_at)).all()

    pending_violations = [v for v in violations if v.status == "Pending"]
    total_pending_amount = sum(v.fine_amount for v in pending_violations)

    return PublicFineResponse(
        plate_number=clean_plate,
        total_violations=len(violations),
        pending_violations=len(pending_violations),
        total_pending_amount=total_pending_amount,
        violations=violations
    )


@router.post("/pay/{fine_ref}", response_model=ViolationOut)
def pay_challan(fine_ref: str, db: Session = Depends(get_db)):
    import datetime
    import uuid
    from app.models import StatusLog

    violation = db.query(Violation).filter(Violation.fine_ref == fine_ref.strip()).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Challan reference not found.")

    if violation.status == "Paid":
        return violation

    old_status = violation.status
    violation.status = "Paid"
    violation.paid_at = datetime.datetime.utcnow()
    violation.payment_ref = f"UPI-{uuid.uuid4().hex[:8].upper()}"

    log = StatusLog(
        violation_id=violation.id,
        old_status=old_status,
        new_status="Paid",
        notes=f"Settled digitally by citizen. Ref: {violation.payment_ref}"
    )
    db.add(log)
    db.commit()
    db.refresh(violation)
    return violation

