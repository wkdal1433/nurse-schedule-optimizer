"""
역할 기반 및 고용형태별 배치 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date
from app.database.connection import get_db
from app.models.models import (
    Employee, RoleConstraint, SupervisionPair, EmploymentTypeRule, 
    RoleViolation, Schedule
)
from app.services.role_assignment_service import RoleAssignmentService

router = APIRouter()

# Pydantic 모델들
class EmployeeRoleUpdate(BaseModel):
    role: str
    employment_type: str
    allowed_shifts: Optional[List[str]] = None
    max_hours_per_week: int = 40
    max_days_per_week: int = 5
    can_work_alone: bool = True
    requires_supervision: bool = False
    can_supervise: bool = True
    specialization: Optional[str] = None

class RoleConstraintCreate(BaseModel):
    role: str
    ward_id: Optional[int] = None
    allowed_shifts: List[str] = ["day", "evening", "night"]
    forbidden_shifts: List[str] = []
    min_per_shift: int = 0
    max_per_shift: int = 10
    requires_pairing_with_roles: List[str] = []
    cannot_work_with_roles: List[str] = []
    must_have_supervisor: bool = False
    can_be_sole_charge: bool = True

class SupervisionPairCreate(BaseModel):
    supervisor_id: int
    supervisee_id: int
    pairing_type: str = "mentor"
    end_date: Optional[str] = None

class EmploymentTypeRuleCreate(BaseModel):
    employment_type: str
    ward_id: Optional[int] = None
    max_hours_per_day: int = 8
    max_hours_per_week: int = 40
    max_days_per_week: int = 5
    max_consecutive_days: int = 5
    allowed_shift_types: List[str] = ["day", "evening", "night"]
    forbidden_shift_types: List[str] = []
    weekend_work_allowed: bool = True
    night_shift_allowed: bool = True
    holiday_work_allowed: bool = True
    scheduling_priority: int = 5

class RoleValidationRequest(BaseModel):
    schedule_id: int

@router.put("/employees/{employee_id}/role", response_model=Dict)
async def update_employee_role(
    employee_id: int,
    role_update: EmployeeRoleUpdate,
    db: Session = Depends(get_db)
):
    """직원 역할 및 고용형태 정보 업데이트"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직원을 찾을 수 없습니다"
            )
        
        # 역할 정보 업데이트
        employee.role = role_update.role
        employee.employment_type = role_update.employment_type
        employee.allowed_shifts = role_update.allowed_shifts
        employee.max_hours_per_week = role_update.max_hours_per_week
        employee.max_days_per_week = role_update.max_days_per_week
        employee.can_work_alone = role_update.can_work_alone
        employee.requires_supervision = role_update.requires_supervision
        employee.can_supervise = role_update.can_supervise
        employee.specialization = role_update.specialization
        
        db.commit()
        
        return {
            "message": "직원 역할 정보가 업데이트되었습니다",
            "employee_id": employee_id,
            "role": employee.role,
            "employment_type": employee.employment_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"역할 정보 업데이트 실패: {str(e)}"
        )

@router.get("/employees/{employee_id}/role", response_model=Dict)
async def get_employee_role_info(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """직원의 역할 및 고용형태 정보 조회"""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="직원을 찾을 수 없습니다"
        )
    
    return {
        "employee_id": employee.id,
        "employee_name": employee.user.full_name,
        "role": employee.role,
        "employment_type": employee.employment_type,
        "allowed_shifts": employee.allowed_shifts,
        "max_hours_per_week": employee.max_hours_per_week,
        "max_days_per_week": employee.max_days_per_week,
        "can_work_alone": employee.can_work_alone,
        "requires_supervision": employee.requires_supervision,
        "can_supervise": employee.can_supervise,
        "specialization": employee.specialization,
        "years_experience": employee.years_experience,
        "skill_level": employee.skill_level
    }

@router.post("/constraints/", response_model=Dict)
async def create_role_constraint(
    constraint: RoleConstraintCreate,
    db: Session = Depends(get_db)
):
    """역할별 제약조건 생성"""
    try:
        role_service = RoleAssignmentService(db)
        created_constraint = role_service.create_role_constraint(
            constraint.role, constraint.ward_id, constraint.dict()
        )
        
        return {
            "message": "역할별 제약조건이 생성되었습니다",
            "constraint_id": created_constraint.id,
            "role": created_constraint.role
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제약조건 생성 실패: {str(e)}"
        )

@router.get("/constraints/", response_model=List[Dict])
async def get_role_constraints(
    ward_id: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """역할별 제약조건 조회"""
    query = db.query(RoleConstraint).filter(RoleConstraint.is_active == True)
    
    if ward_id is not None:
        query = query.filter(
            (RoleConstraint.ward_id == ward_id) | (RoleConstraint.ward_id.is_(None))
        )
    
    if role:
        query = query.filter(RoleConstraint.role == role)
    
    constraints = query.all()
    
    return [
        {
            "id": c.id,
            "role": c.role,
            "ward_id": c.ward_id,
            "allowed_shifts": c.allowed_shifts,
            "forbidden_shifts": c.forbidden_shifts,
            "min_per_shift": c.min_per_shift,
            "max_per_shift": c.max_per_shift,
            "requires_pairing_with_roles": c.requires_pairing_with_roles,
            "cannot_work_with_roles": c.cannot_work_with_roles,
            "must_have_supervisor": c.must_have_supervisor,
            "can_be_sole_charge": c.can_be_sole_charge,
            "created_at": c.created_at
        }
        for c in constraints
    ]

@router.post("/supervision-pairs/", response_model=Dict)
async def create_supervision_pair(
    pair_data: SupervisionPairCreate,
    db: Session = Depends(get_db)
):
    """감독 페어 생성"""
    try:
        # 감독자와 피감독자 존재 확인
        supervisor = db.query(Employee).filter(Employee.id == pair_data.supervisor_id).first()
        supervisee = db.query(Employee).filter(Employee.id == pair_data.supervisee_id).first()
        
        if not supervisor or not supervisee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="감독자 또는 피감독자를 찾을 수 없습니다"
            )
        
        if not supervisor.can_supervise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지정된 감독자는 감독 권한이 없습니다"
            )
        
        role_service = RoleAssignmentService(db)
        end_date = datetime.fromisoformat(pair_data.end_date) if pair_data.end_date else None
        
        pair = role_service.create_supervision_pair(
            pair_data.supervisor_id,
            pair_data.supervisee_id,
            pair_data.pairing_type,
            end_date
        )
        
        return {
            "message": "감독 페어가 생성되었습니다",
            "pair_id": pair.id,
            "supervisor": supervisor.user.full_name,
            "supervisee": supervisee.user.full_name,
            "pairing_type": pair.pairing_type
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"감독 페어 생성 실패: {str(e)}"
        )

@router.get("/supervision-pairs/", response_model=List[Dict])
async def get_supervision_pairs(
    ward_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """감독 페어 목록 조회"""
    query = db.query(SupervisionPair)
    
    if active_only:
        query = query.filter(SupervisionPair.is_active == True)
    
    if ward_id is not None:
        query = query.join(Employee, SupervisionPair.supervisee_id == Employee.id)\
                    .filter(Employee.ward_id == ward_id)
    
    pairs = query.all()
    
    return [
        {
            "id": pair.id,
            "supervisor": {
                "id": pair.supervisor.id,
                "name": pair.supervisor.user.full_name,
                "role": pair.supervisor.role
            },
            "supervisee": {
                "id": pair.supervisee.id,
                "name": pair.supervisee.user.full_name,
                "role": pair.supervisee.role
            },
            "pairing_type": pair.pairing_type,
            "is_mandatory": pair.is_mandatory,
            "start_date": pair.start_date,
            "end_date": pair.end_date,
            "is_active": pair.is_active
        }
        for pair in pairs
    ]

@router.post("/employment-rules/", response_model=Dict)
async def create_employment_type_rule(
    rule_data: EmploymentTypeRuleCreate,
    db: Session = Depends(get_db)
):
    """고용형태별 규칙 생성"""
    try:
        role_service = RoleAssignmentService(db)
        rule = role_service.create_employment_type_rule(
            rule_data.employment_type, rule_data.ward_id, rule_data.dict()
        )
        
        return {
            "message": "고용형태별 규칙이 생성되었습니다",
            "rule_id": rule.id,
            "employment_type": rule.employment_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"고용형태 규칙 생성 실패: {str(e)}"
        )

@router.get("/employment-rules/", response_model=List[Dict])
async def get_employment_type_rules(
    employment_type: Optional[str] = Query(None),
    ward_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """고용형태별 규칙 조회"""
    query = db.query(EmploymentTypeRule).filter(EmploymentTypeRule.is_active == True)
    
    if employment_type:
        query = query.filter(EmploymentTypeRule.employment_type == employment_type)
    
    if ward_id is not None:
        query = query.filter(
            (EmploymentTypeRule.ward_id == ward_id) | (EmploymentTypeRule.ward_id.is_(None))
        )
    
    rules = query.all()
    
    return [
        {
            "id": rule.id,
            "employment_type": rule.employment_type,
            "ward_id": rule.ward_id,
            "max_hours_per_day": rule.max_hours_per_day,
            "max_hours_per_week": rule.max_hours_per_week,
            "max_days_per_week": rule.max_days_per_week,
            "max_consecutive_days": rule.max_consecutive_days,
            "allowed_shift_types": rule.allowed_shift_types,
            "forbidden_shift_types": rule.forbidden_shift_types,
            "weekend_work_allowed": rule.weekend_work_allowed,
            "night_shift_allowed": rule.night_shift_allowed,
            "holiday_work_allowed": rule.holiday_work_allowed,
            "scheduling_priority": rule.scheduling_priority,
            "created_at": rule.created_at
        }
        for rule in rules
    ]

@router.post("/validate/", response_model=Dict)
async def validate_role_assignments(
    validation_request: RoleValidationRequest,
    db: Session = Depends(get_db)
):
    """스케줄의 역할별 배치 검증"""
    schedule = db.query(Schedule).filter(Schedule.id == validation_request.schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스케줄을 찾을 수 없습니다"
        )
    
    role_service = RoleAssignmentService(db)
    is_valid, violations = role_service.validate_role_assignments(schedule)
    
    # 위반사항을 심각도별로 분류
    violations_by_severity = {}
    for violation in violations:
        severity = violation.get("severity", "medium")
        violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
    
    return {
        "is_valid": is_valid,
        "total_violations": len(violations),
        "violations_by_severity": violations_by_severity,
        "violations": violations,
        "compliance_score": max(0, 100 - len(violations) * 5)
    }

@router.post("/defaults/{ward_id}", response_model=Dict)
async def create_default_role_settings(
    ward_id: int,
    db: Session = Depends(get_db)
):
    """기본 역할 설정 생성"""
    try:
        role_service = RoleAssignmentService(db)
        
        # 기본 역할별 제약조건 생성
        constraints = role_service.create_default_role_constraints(ward_id)
        
        # 기본 고용형태별 규칙 생성
        employment_rules = role_service.create_default_employment_rules(ward_id)
        
        return {
            "message": "기본 역할 설정이 생성되었습니다",
            "ward_id": ward_id,
            "role_constraints_created": len(constraints),
            "employment_rules_created": len(employment_rules)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기본 설정 생성 실패: {str(e)}"
        )

@router.get("/summary/{schedule_id}", response_model=Dict)
async def get_role_assignment_summary(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """역할별 배치 현황 요약"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스케줄을 찾을 수 없습니다"
        )
    
    role_service = RoleAssignmentService(db)
    summary = role_service.get_role_assignment_summary(schedule)
    
    return summary

@router.get("/employees/by-ward/{ward_id}", response_model=List[Dict])
async def get_employees_by_ward(
    ward_id: int,
    role: Optional[str] = Query(None),
    employment_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """병동별 직원 목록 조회 (역할/고용형태 필터링 가능)"""
    query = db.query(Employee).filter(
        Employee.ward_id == ward_id,
        Employee.is_active == True
    )
    
    if role:
        query = query.filter(Employee.role == role)
    
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)
    
    employees = query.all()
    
    return [
        {
            "id": emp.id,
            "employee_number": emp.employee_number,
            "name": emp.user.full_name,
            "role": emp.role,
            "employment_type": emp.employment_type,
            "skill_level": emp.skill_level,
            "years_experience": emp.years_experience,
            "can_work_alone": emp.can_work_alone,
            "requires_supervision": emp.requires_supervision,
            "can_supervise": emp.can_supervise,
            "specialization": emp.specialization,
            "allowed_shifts": emp.allowed_shifts,
            "max_hours_per_week": emp.max_hours_per_week
        }
        for emp in employees
    ]

@router.delete("/supervision-pairs/{pair_id}", response_model=Dict)
async def deactivate_supervision_pair(
    pair_id: int,
    db: Session = Depends(get_db)
):
    """감독 페어 비활성화"""
    pair = db.query(SupervisionPair).filter(SupervisionPair.id == pair_id).first()
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="감독 페어를 찾을 수 없습니다"
        )
    
    pair.is_active = False
    pair.end_date = datetime.utcnow()
    db.commit()
    
    return {
        "message": "감독 페어가 비활성화되었습니다",
        "pair_id": pair_id
    }