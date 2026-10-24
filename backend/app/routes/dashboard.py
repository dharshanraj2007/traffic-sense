import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models import Violation, Admin
from app.schemas import DashboardStats, DailyViolationStat, StatusStat, ViolationOut
from app.auth import get_current_admin

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    # Total violations
    total_violations = db.query(Violation).count()

    # Status counts
    pending_fines = db.query(Violation).filter(Violation.status == "Pending").count()
    paid_fines = db.query(Violation).filter(Violation.status == "Paid").count()
    cancelled_fines = db.query(Violation).filter(Violation.status == "Cancelled").count()

    # Amount calculations
    collected_res = db.query(func.sum(Violation.fine_amount)).filter(Violation.status == "Paid").scalar()
    total_collected_amount = float(collected_res or 0.0)

    pending_res = db.query(func.sum(Violation.fine_amount)).filter(Violation.status == "Pending").scalar()
    total_pending_amount = float(pending_res or 0.0)

    # Needs review count
    needs_review_count = db.query(Violation).filter(Violation.needs_review == True).count()

    # Daily violations for the past 7 days
    today = datetime.datetime.utcnow().date()
    daily_stats = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        start_day = datetime.datetime.combine(day, datetime.time.min)
        end_day = datetime.datetime.combine(day, datetime.time.max)
        
        count = db.query(Violation).filter(
            Violation.occurred_at >= start_day,
            Violation.occurred_at <= end_day
        ).count()
        daily_stats.append(DailyViolationStat(date=day.strftime("%b %d"), count=count))

    # Status distribution for donut chart
    status_distribution = [
        StatusStat(name="Pending", value=pending_fines),
        StatusStat(name="Paid", value=paid_fines),
        StatusStat(name="Cancelled", value=cancelled_fines),
    ]

    # Recent 10 violations
    recent = db.query(Violation).order_by(desc(Violation.occurred_at)).limit(10).all()

    return DashboardStats(
        total_violations=total_violations,
        pending_fines=pending_fines,
        paid_fines=paid_fines,
        cancelled_fines=cancelled_fines,
        total_collected_amount=total_collected_amount,
        total_pending_amount=total_pending_amount,
        needs_review_count=needs_review_count,
        daily_stats=daily_stats,
        status_distribution=status_distribution,
        recent_violations=recent
    )
