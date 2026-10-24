import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import Violation, Admin
from app.auth import get_current_admin
from app.services.reports import generate_csv_report, generate_pdf_report

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/summary")
def get_reports_summary(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    total = db.query(Violation).count()
    pending = db.query(Violation).filter(Violation.status == "Pending").count()
    paid = db.query(Violation).filter(Violation.status == "Paid").count()
    cancelled = db.query(Violation).filter(Violation.status == "Cancelled").count()
    needs_review = db.query(Violation).filter(Violation.needs_review == True).count()

    total_amount = float(db.query(func.sum(Violation.fine_amount)).scalar() or 0.0)
    collected_amount = float(db.query(func.sum(Violation.fine_amount)).filter(Violation.status == "Paid").scalar() or 0.0)
    pending_amount = float(db.query(func.sum(Violation.fine_amount)).filter(Violation.status == "Pending").scalar() or 0.0)

    # Violations by day (last 14 days)
    today = datetime.datetime.utcnow().date()
    days_data = []
    for i in range(13, -1, -1):
        d = today - datetime.timedelta(days=i)
        start_d = datetime.datetime.combine(d, datetime.time.min)
        end_d = datetime.datetime.combine(d, datetime.time.max)
        c = db.query(Violation).filter(
            Violation.occurred_at >= start_d,
            Violation.occurred_at <= end_d
        ).count()
        days_data.append({"date": d.strftime("%Y-%m-%d"), "count": c})

    return {
        "total_violations": total,
        "pending_count": pending,
        "paid_count": paid,
        "cancelled_count": cancelled,
        "needs_review_count": needs_review,
        "total_amount": total_amount,
        "collected_amount": collected_amount,
        "pending_amount": pending_amount,
        "violations_by_day": days_data
    }

@router.get("/export")
def export_report(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    query = db.query(Violation)

    if search:
        p = f"%{search.strip().upper()}%"
        query = query.filter((Violation.plate_number.like(p)) | (Violation.fine_ref.like(p)))
    if status and status != "All":
        query = query.filter(Violation.status == status)
    if source and source != "All":
        query = query.filter(Violation.source == source)
    if start_date:
        try:
            query = query.filter(Violation.occurred_at >= datetime.datetime.fromisoformat(start_date))
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)
            query = query.filter(Violation.occurred_at <= ed)
        except ValueError:
            pass

    violations = query.order_by(desc(Violation.occurred_at)).all()

    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        csv_data = generate_csv_report(violations)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=traffic_violations_{timestamp}.csv"}
        )
    else:
        # PDF report
        total_amt = sum(v.fine_amount for v in violations)
        collected_amt = sum(v.fine_amount for v in violations if v.status == "Paid")
        pending_amt = sum(v.fine_amount for v in violations if v.status == "Pending")
        pending_cnt = sum(1 for v in violations if v.status == "Pending")
        paid_cnt = sum(1 for v in violations if v.status == "Paid")
        cancelled_cnt = sum(1 for v in violations if v.status == "Cancelled")
        needs_rev_cnt = sum(1 for v in violations if v.needs_review)

        summary_dict = {
            "total_violations": len(violations),
            "pending_count": pending_cnt,
            "paid_count": paid_cnt,
            "cancelled_count": cancelled_cnt,
            "needs_review_count": needs_rev_cnt,
            "total_amount": total_amt,
            "collected_amount": collected_amt,
            "pending_amount": pending_amt,
            "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

        pdf_bytes = generate_pdf_report(violations, summary_dict)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=traffic_violations_{timestamp}.pdf"}
        )
