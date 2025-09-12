from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from app.database.connection import get_db
from app.services.pattern_validation_service import PatternValidationService
from app.models.models import (
    ShiftPattern, PatternViolation, FatigueScore, PatternRecommendation,
    Employee
)
from app.models.scheduling_models import Schedule, ShiftAssignment

router = APIRouter()

# Pydantic 스키마들
class ShiftPatternCreate(BaseModel):
    pattern_name: str
    pattern_type: str
    description: Optional[str] = None
    sequence_length: int = 2
    pattern_definition: dict
    penalty_score: float = 0.0
    severity: str = "medium"
    ward_id: Optional[int] = None
    role_specific: Optional[List[str]] = None

class ShiftPatternResponse(BaseModel):
    id: int
    pattern_name: str
    pattern_type: str
    description: Optional[str]
    penalty_score: float
    severity: str
    is_active: bool
    
    class Config:
        from_attributes = True

class PatternValidationRequest(BaseModel):
    employee_id: int
    assignments: List[dict]  # [{"shift_date": "2024-01-01", "shift_type": "day"}, ...]
    period_start: date
    period_end: date

class PatternValidationResponse(BaseModel):
    employee_id: int
    is_valid: bool
    total_penalty: float
    violations: List[dict]
    pattern_score: float
    recommendations: List[str]

class SchedulePatternValidationResponse(BaseModel):
    schedule_id: int
    is_valid: bool
    total_violations: int
    employee_results: List[dict]
    overall_score: float
    summary: str

class FatigueAnalysisRequest(BaseModel):
    employee_id: int
    period_start: date
    period_end: date

class FatigueAnalysisResponse(BaseModel):
    employee_id: int
    total_fatigue_score: float
    risk_level: str
    recommendations: List[str]
    rest_days_needed: int

# 패턴 검증 서비스 인스턴스
pattern_service = PatternValidationService()

@router.post("/patterns/", response_model=ShiftPatternResponse)
def create_shift_pattern(
    pattern: ShiftPatternCreate,
    db: Session = Depends(get_db)
):
    """새로운 근무 패턴 규칙 생성"""
    try:
        db_pattern = ShiftPattern(
            pattern_name=pattern.pattern_name,
            pattern_type=pattern.pattern_type,
            description=pattern.description,
            sequence_length=pattern.sequence_length,
            pattern_definition=pattern.pattern_definition,
            penalty_score=pattern.penalty_score,
            severity=pattern.severity,
            ward_id=pattern.ward_id,
            role_specific=pattern.role_specific
        )
        
        db.add(db_pattern)
        db.commit()
        db.refresh(db_pattern)
        
        return db_pattern
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"패턴 생성 중 오류 발생: {str(e)}"
        )

@router.get("/patterns/", response_model=List[ShiftPatternResponse])
def get_shift_patterns(
    ward_id: Optional[int] = None,
    pattern_type: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """근무 패턴 규칙 목록 조회"""
    try:
        query = db.query(ShiftPattern).filter(ShiftPattern.is_active == is_active)
        
        if ward_id is not None:
            query = query.filter(
                (ShiftPattern.ward_id == ward_id) | (ShiftPattern.ward_id.is_(None))
            )
        
        if pattern_type:
            query = query.filter(ShiftPattern.pattern_type == pattern_type)
        
        patterns = query.all()
        return patterns
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"패턴 조회 중 오류 발생: {str(e)}"
        )

@router.put("/patterns/{pattern_id}")
def update_shift_pattern(
    pattern_id: int,
    pattern: ShiftPatternCreate,
    db: Session = Depends(get_db)
):
    """근무 패턴 규칙 수정"""
    try:
        db_pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
        
        if not db_pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="패턴을 찾을 수 없습니다"
            )
        
        # 업데이트
        for key, value in pattern.dict(exclude_unset=True).items():
            setattr(db_pattern, key, value)
        
        db.commit()
        db.refresh(db_pattern)
        
        return {"message": "패턴이 성공적으로 수정되었습니다", "pattern": db_pattern}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"패턴 수정 중 오류 발생: {str(e)}"
        )

@router.delete("/patterns/{pattern_id}")
def delete_shift_pattern(
    pattern_id: int,
    db: Session = Depends(get_db)
):
    """근무 패턴 규칙 삭제 (비활성화)"""
    try:
        db_pattern = db.query(ShiftPattern).filter(ShiftPattern.id == pattern_id).first()
        
        if not db_pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="패턴을 찾을 수 없습니다"
            )
        
        db_pattern.is_active = False
        db.commit()
        
        return {"message": "패턴이 성공적으로 삭제되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"패턴 삭제 중 오류 발생: {str(e)}"
        )

@router.post("/validate/employee", response_model=PatternValidationResponse)
def validate_employee_pattern(
    request: PatternValidationRequest,
    db: Session = Depends(get_db)
):
    """직원별 근무 패턴 검증"""
    try:
        # 직원 존재 확인
        employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직원을 찾을 수 없습니다"
            )
        
        # 패턴 검증 실행
        result = pattern_service.validate_employee_pattern(
            db=db,
            employee_id=request.employee_id,
            assignments=request.assignments,
            period_start=datetime.combine(request.period_start, datetime.min.time()),
            period_end=datetime.combine(request.period_end, datetime.min.time())
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"직원 패턴 검증 중 오류 발생: {str(e)}"
        )

@router.post("/validate/schedule/{schedule_id}", response_model=SchedulePatternValidationResponse)
def validate_schedule_patterns(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """전체 스케줄의 패턴 검증"""
    try:
        # 스케줄 존재 확인
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="스케줄을 찾을 수 없습니다"
            )
        
        # 스케줄 패턴 검증 실행
        result = pattern_service.validate_schedule_patterns(db=db, schedule_id=schedule_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스케줄 패턴 검증 중 오류 발생: {str(e)}"
        )

@router.get("/violations/schedule/{schedule_id}")
def get_pattern_violations(
    schedule_id: int,
    resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """스케줄의 패턴 위반사항 조회"""
    try:
        query = db.query(PatternViolation).filter(PatternViolation.schedule_id == schedule_id)
        
        if resolved is not None:
            query = query.filter(PatternViolation.is_resolved == resolved)
        
        if severity:
            query = query.filter(PatternViolation.severity == severity)
        
        violations = query.all()
        
        violation_list = []
        for violation in violations:
            violation_data = {
                "id": violation.id,
                "employee_id": violation.employee_id,
                "pattern_name": violation.pattern.pattern_name if violation.pattern else "Unknown",
                "violation_date_start": violation.violation_date_start.isoformat(),
                "violation_date_end": violation.violation_date_end.isoformat(),
                "violation_sequence": violation.violation_sequence,
                "description": violation.description,
                "severity": violation.severity,
                "penalty_score": violation.penalty_score,
                "is_resolved": violation.is_resolved,
                "resolution_method": violation.resolution_method
            }
            violation_list.append(violation_data)
        
        return {
            "schedule_id": schedule_id,
            "total_violations": len(violation_list),
            "violations": violation_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"위반사항 조회 중 오류 발생: {str(e)}"
        )

@router.post("/violations/{violation_id}/resolve")
def resolve_pattern_violation(
    violation_id: int,
    resolution_method: str,
    resolution_notes: Optional[str] = None,
    resolver_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """패턴 위반사항 해결 처리"""
    try:
        violation = db.query(PatternViolation).filter(PatternViolation.id == violation_id).first()
        
        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="위반사항을 찾을 수 없습니다"
            )
        
        violation.is_resolved = True
        violation.resolution_method = resolution_method
        violation.resolution_notes = resolution_notes
        violation.resolved_at = datetime.utcnow()
        violation.resolved_by = resolver_id
        
        db.commit()
        
        return {"message": "위반사항이 성공적으로 해결 처리되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"위반사항 해결 처리 중 오류 발생: {str(e)}"
        )

@router.post("/fatigue/analyze", response_model=FatigueAnalysisResponse)
def analyze_employee_fatigue(
    request: FatigueAnalysisRequest,
    db: Session = Depends(get_db)
):
    """직원 피로도 분석"""
    try:
        # 직원 존재 확인
        employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직원을 찾을 수 없습니다"
            )
        
        # 해당 기간의 최근 피로도 점수 조회
        fatigue_score = db.query(FatigueScore).filter(
            FatigueScore.employee_id == request.employee_id,
            FatigueScore.period_start <= request.period_start,
            FatigueScore.period_end >= request.period_end
        ).order_by(FatigueScore.calculation_date.desc()).first()
        
        if fatigue_score:
            return {
                "employee_id": request.employee_id,
                "total_fatigue_score": fatigue_score.total_fatigue_score,
                "risk_level": fatigue_score.risk_level,
                "recommendations": fatigue_score.recommendations or [],
                "rest_days_needed": fatigue_score.rest_days_needed
            }
        else:
            # 기본 응답 (실제로는 동적 계산 로직 구현)
            return {
                "employee_id": request.employee_id,
                "total_fatigue_score": 0.0,
                "risk_level": "low",
                "recommendations": ["피로도 데이터가 없습니다. 최근 근무 기록을 확인하세요."],
                "rest_days_needed": 0
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"피로도 분석 중 오류 발생: {str(e)}"
        )

@router.get("/statistics/ward/{ward_id}")
def get_pattern_statistics(
    ward_id: int,
    period_start: date,
    period_end: date,
    db: Session = Depends(get_db)
):
    """병동별 패턴 통계"""
    try:
        # 패턴 통계 생성
        stats = pattern_service.get_pattern_statistics(
            db=db,
            ward_id=ward_id,
            period_start=datetime.combine(period_start, datetime.min.time()),
            period_end=datetime.combine(period_end, datetime.min.time())
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"패턴 통계 조회 중 오류 발생: {str(e)}"
        )

@router.get("/recommendations/schedule/{schedule_id}")
def get_pattern_recommendations(
    schedule_id: int,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """스케줄의 패턴 개선 권장사항 조회"""
    try:
        query = db.query(PatternRecommendation).filter(
            PatternRecommendation.schedule_id == schedule_id
        )
        
        if priority:
            query = query.filter(PatternRecommendation.priority == priority)
        
        if status:
            query = query.filter(PatternRecommendation.status == status)
        
        recommendations = query.all()
        
        rec_list = []
        for rec in recommendations:
            rec_data = {
                "id": rec.id,
                "employee_id": rec.employee_id,
                "recommendation_type": rec.recommendation_type,
                "priority": rec.priority,
                "current_pattern": rec.current_pattern,
                "recommended_pattern": rec.recommended_pattern,
                "fatigue_improvement": rec.fatigue_improvement,
                "pattern_score_improvement": rec.pattern_score_improvement,
                "implementation_difficulty": rec.implementation_difficulty,
                "estimated_impact": rec.estimated_impact,
                "status": rec.status
            }
            rec_list.append(rec_data)
        
        return {
            "schedule_id": schedule_id,
            "total_recommendations": len(rec_list),
            "recommendations": rec_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"권장사항 조회 중 오류 발생: {str(e)}"
        )

@router.post("/defaults/ward/{ward_id}")
def create_default_patterns(
    ward_id: int,
    db: Session = Depends(get_db)
):
    """병동의 기본 패턴 규칙 생성"""
    try:
        default_patterns = [
            {
                "pattern_name": "day_to_night",
                "pattern_type": "forbidden",
                "description": "Day 근무 다음날 Night 근무 금지",
                "sequence_length": 2,
                "pattern_definition": {"sequence": ["day", "night"], "consecutive": True},
                "penalty_score": -30.0,
                "severity": "high",
                "ward_id": ward_id
            },
            {
                "pattern_name": "excessive_nights",
                "pattern_type": "forbidden",
                "description": "연속 3일 이상 Night 근무 금지",
                "sequence_length": 4,
                "pattern_definition": {"sequence": ["night", "night", "night", "night"], "consecutive": True},
                "penalty_score": -30.0,
                "severity": "high",
                "ward_id": ward_id
            },
            {
                "pattern_name": "no_rest_after_nights",
                "pattern_type": "discouraged",
                "description": "Night 근무 후 바로 다음날 근무 지양",
                "sequence_length": 2,
                "pattern_definition": {"sequence": ["night", "*"], "gap_days": 0},
                "penalty_score": -25.0,
                "severity": "medium",
                "ward_id": ward_id
            },
            {
                "pattern_name": "weekend_overload",
                "pattern_type": "discouraged",
                "description": "주말 연속 근무 지양",
                "sequence_length": 2,
                "pattern_definition": {"weekend_consecutive": True},
                "penalty_score": -20.0,
                "severity": "low",
                "ward_id": ward_id
            }
        ]
        
        created_patterns = []
        for pattern_data in default_patterns:
            # 이미 존재하는지 확인
            existing = db.query(ShiftPattern).filter(
                ShiftPattern.pattern_name == pattern_data["pattern_name"],
                ShiftPattern.ward_id == ward_id
            ).first()
            
            if not existing:
                db_pattern = ShiftPattern(**pattern_data)
                db.add(db_pattern)
                created_patterns.append(pattern_data["pattern_name"])
        
        db.commit()
        
        return {
            "message": f"{len(created_patterns)}개의 기본 패턴이 생성되었습니다",
            "created_patterns": created_patterns
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기본 패턴 생성 중 오류 발생: {str(e)}"
        )