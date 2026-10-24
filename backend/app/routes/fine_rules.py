from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FineRule, Admin
from app.schemas import FineRuleOut, FineRuleUpdate
from app.auth import get_current_admin

router = APIRouter(prefix="/api/fine-rules", tags=["fine-rules"])

@router.get("", response_model=List[FineRuleOut])
def get_fine_rules(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    return db.query(FineRule).all()

@router.put("/{rule_id}", response_model=FineRuleOut)
def update_fine_rule(
    rule_id: int,
    rule_in: FineRuleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    rule = db.query(FineRule).filter(FineRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Fine rule not found")
    
    if rule_in.amount is not None:
        rule.amount = rule_in.amount
    if rule_in.active is not None:
        rule.active = rule_in.active
        
    db.commit()
    db.refresh(rule)
    return rule
