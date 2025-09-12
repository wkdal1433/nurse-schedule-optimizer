"""
근무 규칙 및 법적 준수 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database.connection import get_db
from app.models.models import ShiftRule, ComplianceViolation, Schedule
from app.services.compliance_service import ComplianceService

router = APIRouter()

# Pydantic 모델들
class ShiftRuleCreate(BaseModel):
    ward_id: Optional[int] = None
    rule_name: str
    rule_type: str  # "hard" or "soft"
    category: str  # "consecutive", "weekly", "legal", "pattern"
    max_consecutive_nights: int = 3
    max_consecutive_days: int = 5
    min_rest_days_per_week: int = 1
    max_hours_per_week: int = 40
    forbidden_patterns: Optional[List[str]] = []
    penalty_weight: float = 1.0

class ShiftRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_type: Optional[str] = None
    max_consecutive_nights: Optional[int] = None
    max_consecutive_days: Optional[int] = None
    min_rest_days_per_week: Optional[int] = None
    max_hours_per_week: Optional[int] = None
    forbidden_patterns: Optional[List[str]] = None
    penalty_weight: Optional[float] = None
    is_active: Optional[bool] = None

class ComplianceValidationRequest(BaseModel):
    schedule_id: int

class ComplianceReport(BaseModel):
    is_compliant: bool
    compliance_score: float
    total_violations: int
    violations_by_severity: Dict[str, int]
    violations: List[Dict]

@router.post("/rules/", response_model=Dict)
async def create_shift_rule(
    rule: ShiftRuleCreate,
    db: Session = Depends(get_db)
):
    """근무 규칙 생성"""
    try:
        db_rule = ShiftRule(
            ward_id=rule.ward_id,
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            category=rule.category,
            max_consecutive_nights=rule.max_consecutive_nights,
            max_consecutive_days=rule.max_consecutive_days,
            min_rest_days_per_week=rule.min_rest_days_per_week,
            max_hours_per_week=rule.max_hours_per_week,
            forbidden_patterns=rule.forbidden_patterns,
            penalty_weight=rule.penalty_weight
        )
        
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        return {
            "message": "근무 규칙이 생성되었습니다",
            "rule_id": db_rule.id,
            "rule_name": db_rule.rule_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"규칙 생성 실패: {str(e)}"
        )

@router.get("/rules/", response_model=List[Dict])
async def get_shift_rules(
    ward_id: Optional[int] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """근무 규칙 조회"""
    query = db.query(ShiftRule)
    
    if ward_id is not None:
        query = query.filter((ShiftRule.ward_id == ward_id) | (ShiftRule.ward_id.is_(None)))
    
    if is_active is not None:
        query = query.filter(ShiftRule.is_active == is_active)
    
    rules = query.all()
    
    return [
        {
            "id": rule.id,
            "ward_id": rule.ward_id,
            "rule_name": rule.rule_name,
            "rule_type": rule.rule_type,
            "category": rule.category,
            "max_consecutive_nights": rule.max_consecutive_nights,
            "max_consecutive_days": rule.max_consecutive_days,
            "min_rest_days_per_week": rule.min_rest_days_per_week,
            "max_hours_per_week": rule.max_hours_per_week,
            "forbidden_patterns": rule.forbidden_patterns,
            "penalty_weight": rule.penalty_weight,
            "is_active": rule.is_active,
            "created_at": rule.created_at
        }
        for rule in rules
    ]

@router.put("/rules/{rule_id}", response_model=Dict)
async def update_shift_rule(
    rule_id: int,
    rule_update: ShiftRuleUpdate,
    db: Session = Depends(get_db)
):
    """근무 규칙 수정"""
    db_rule = db.query(ShiftRule).filter(ShiftRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="규칙을 찾을 수 없습니다"
        )
    
    update_data = rule_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db.commit()
    db.refresh(db_rule)
    
    return {
        "message": "규칙이 수정되었습니다",
        "rule_id": db_rule.id
    }

@router.delete("/rules/{rule_id}", response_model=Dict)
async def delete_shift_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """근무 규칙 삭제 (비활성화)"""
    db_rule = db.query(ShiftRule).filter(ShiftRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="규칙을 찾을 수 없습니다"
        )
    
    db_rule.is_active = False
    db.commit()
    
    return {
        "message": "규칙이 삭제되었습니다",
        "rule_id": rule_id
    }

@router.post("/validate/", response_model=ComplianceReport)
async def validate_schedule_compliance(
    validation_request: ComplianceValidationRequest,
    db: Session = Depends(get_db)
):
    """스케줄 규칙 준수 검증"""
    schedule = db.query(Schedule).filter(Schedule.id == validation_request.schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스케줄을 찾을 수 없습니다"
        )
    
    compliance_service = ComplianceService(db)
    is_compliant, violations = compliance_service.validate_schedule(schedule)
    compliance_score = compliance_service.calculate_compliance_score(schedule)
    
    # 위반 사항을 심각도별로 분류
    violations_by_severity = {}
    for violation in violations:
        severity = violation.get("severity", "medium")
        violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
    
    return ComplianceReport(
        is_compliant=is_compliant,
        compliance_score=compliance_score,
        total_violations=len(violations),
        violations_by_severity=violations_by_severity,
        violations=violations
    )

@router.post("/rules/default/{ward_id}", response_model=Dict)
async def create_default_rules(
    ward_id: int,
    db: Session = Depends(get_db)
):
    """기본 근무 규칙 생성"""
    compliance_service = ComplianceService(db)
    rules = compliance_service.create_default_rules(ward_id)
    
    return {
        "message": f"기본 규칙 {len(rules)}개가 생성되었습니다",
        "ward_id": ward_id,
        "rules_created": len(rules)
    }

@router.get("/violations/{schedule_id}", response_model=List[Dict])
async def get_compliance_violations(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """스케줄별 규칙 위반 사항 조회"""
    violations = db.query(ComplianceViolation).filter(
        ComplianceViolation.schedule_id == schedule_id
    ).all()
    
    return [
        {
            "id": v.id,
            "employee_id": v.employee_id,
            "rule_id": v.rule_id,
            "violation_type": v.violation_type,
            "description": v.description,
            "severity": v.severity,
            "penalty_score": v.penalty_score,
            "is_resolved": v.is_resolved,
            "violation_date": v.violation_date,
            "created_at": v.created_at
        }
        for v in violations
    ]

@router.get("/report/{ward_id}", response_model=Dict)
async def get_compliance_report(
    ward_id: int,
    db: Session = Depends(get_db)
):
    """병동별 규칙 준수 현황 리포트"""
    # 최근 스케줄들의 준수 현황 분석
    recent_schedules = db.query(Schedule).filter(
        Schedule.ward_id == ward_id
    ).order_by(Schedule.created_at.desc()).limit(5).all()
    
    compliance_service = ComplianceService(db)
    report_data = {
        "ward_id": ward_id,
        "total_schedules_analyzed": len(recent_schedules),
        "schedules": []
    }
    
    total_score = 0
    for schedule in recent_schedules:
        is_compliant, violations = compliance_service.validate_schedule(schedule)
        score = compliance_service.calculate_compliance_score(schedule)
        total_score += score
        
        schedule_data = {
            "schedule_id": schedule.id,
            "month": schedule.month,
            "year": schedule.year,
            "is_compliant": is_compliant,
            "compliance_score": score,
            "total_violations": len(violations),
            "status": schedule.status
        }
        report_data["schedules"].append(schedule_data)
    
    report_data["average_compliance_score"] = total_score / len(recent_schedules) if recent_schedules else 0
    
    return report_data