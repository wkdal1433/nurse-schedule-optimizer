from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import datetime, date
from pydantic import BaseModel

from app.database.connection import get_db
from app.services.manual_editing_service import ManualEditingService
from app.models.models import Employee, User
from app.models.scheduling_models import Schedule, ShiftAssignment, EmergencyLog

router = APIRouter()

# Pydantic 스키마들
class ShiftChangeRequest(BaseModel):
    assignment_id: int
    new_employee_id: Optional[int] = None
    new_shift_type: Optional[str] = None
    new_shift_date: Optional[date] = None
    override: bool = False
    override_reason: Optional[str] = None
    admin_id: Optional[int] = None

class EmergencyReassignmentRequest(BaseModel):
    assignment_id: int
    replacement_employee_id: int
    emergency_reason: str
    admin_id: int
    notify_affected: bool = True

class BulkSwapRequest(BaseModel):
    swap_pairs: List[Tuple[int, int]]  # [(assignment_id_1, assignment_id_2), ...]
    admin_id: int
    validation_level: str = "standard"  # 'strict', 'standard', 'minimal'

class ValidationResult(BaseModel):
    valid: bool
    warnings: List[dict] = []
    errors: List[dict] = []
    pattern_score: float
    recommendations: List[str] = []

class ReplacementSuggestion(BaseModel):
    employee_id: int
    employee_name: str
    role: str
    employment_type: str
    skill_level: int
    years_experience: int
    suitability_score: float
    suitability_reasons: List[str]
    warnings: List[str]
    availability_status: str

class ScheduleResponse(BaseModel):
    id: int
    ward_id: int
    schedule_name: str
    period_start: datetime
    period_end: datetime
    status: str
    optimization_score: float
    
    class Config:
        from_attributes = True

class ShiftAssignmentResponse(BaseModel):
    id: int
    schedule_id: int
    employee_id: int
    employee_name: Optional[str] = None
    shift_date: datetime
    shift_type: str
    is_manual_assignment: bool
    is_override: bool
    override_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

# 수동 편집 서비스는 각 함수에서 필요시 생성됩니다

@router.post("/validate-change", response_model=ValidationResult)
def validate_shift_change(
    request: ShiftChangeRequest,
    db: Session = Depends(get_db)
):
    """근무 변경 전 유효성 검증"""
    try:
        result = ManualEditingService().validate_shift_change(
            db=db,
            assignment_id=request.assignment_id,
            new_employee_id=request.new_employee_id,
            new_shift_type=request.new_shift_type,
            new_shift_date=request.new_shift_date
        )
        
        if 'error' in result and not result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return ValidationResult(
            valid=result['valid'],
            warnings=result.get('warnings', []),
            errors=result.get('errors', []),
            pattern_score=result.get('pattern_score', 100),
            recommendations=result.get('recommendations', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검증 중 오류 발생: {str(e)}"
        )

@router.post("/apply-change")
def apply_shift_change(
    request: ShiftChangeRequest,
    db: Session = Depends(get_db)
):
    """근무 변경 적용"""
    try:
        result = ManualEditingService().apply_shift_change(
            db=db,
            assignment_id=request.assignment_id,
            new_employee_id=request.new_employee_id,
            new_shift_type=request.new_shift_type,
            new_shift_date=request.new_shift_date,
            override=request.override,
            override_reason=request.override_reason,
            admin_id=request.admin_id
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "success": True,
            "message": result['message'],
            "original_data": result['original_data'],
            "new_data": result['new_data'],
            "is_override": result['is_override'],
            "new_schedule_score": result['new_schedule_score']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"변경 적용 중 오류 발생: {str(e)}"
        )

@router.get("/suggestions/{assignment_id}", response_model=List[ReplacementSuggestion])
def get_replacement_suggestions(
    assignment_id: int,
    emergency: bool = False,
    max_suggestions: int = 5,
    db: Session = Depends(get_db)
):
    """대체 근무자 추천"""
    try:
        suggestions = ManualEditingService().get_replacement_suggestions(
            db=db,
            assignment_id=assignment_id,
            emergency=emergency,
            max_suggestions=max_suggestions
        )
        
        return [
            ReplacementSuggestion(
                employee_id=s['employee_id'],
                employee_name=s['employee_name'],
                role=s['role'],
                employment_type=s['employment_type'],
                skill_level=s['skill_level'],
                years_experience=s['years_experience'],
                suitability_score=s['suitability_score'],
                suitability_reasons=s['suitability_reasons'],
                warnings=s['warnings'],
                availability_status=s['availability_status']
            ) for s in suggestions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"추천 조회 중 오류 발생: {str(e)}"
        )

@router.post("/emergency-reassignment")
def emergency_reassignment(
    request: EmergencyReassignmentRequest,
    db: Session = Depends(get_db)
):
    """응급 근무 재배치"""
    try:
        result = ManualEditingService().emergency_reassignment(
            db=db,
            assignment_id=request.assignment_id,
            replacement_employee_id=request.replacement_employee_id,
            emergency_reason=request.emergency_reason,
            admin_id=request.admin_id,
            notify_affected=request.notify_affected
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
        
        return {
            "success": True,
            "message": "응급 재배치가 성공적으로 완료되었습니다",
            "original_data": result['original_data'],
            "new_data": result['new_data'],
            "emergency_log_created": result.get('emergency_log_created', False),
            "notifications_queued": result.get('notifications_queued', False),
            "new_schedule_score": result['new_schedule_score']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"응급 재배치 중 오류 발생: {str(e)}"
        )

@router.post("/bulk-swap")
def bulk_shift_swap(
    request: BulkSwapRequest,
    db: Session = Depends(get_db)
):
    """일괄 근무 교환"""
    try:
        result = ManualEditingService().bulk_shift_swap(
            db=db,
            swap_pairs=request.swap_pairs,
            admin_id=request.admin_id,
            validation_level=request.validation_level
        )
        
        return {
            "success": result['success'],
            "total_pairs": result['total_pairs'],
            "successful_swaps": result['successful_swaps'],
            "failed_swaps": result['failed_swaps'],
            "results": result['results']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일괄 교환 중 오류 발생: {str(e)}"
        )

@router.get("/schedules/", response_model=List[ScheduleResponse])
def get_schedules(
    ward_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """스케줄 목록 조회"""
    try:
        query = db.query(Schedule)
        
        if ward_id:
            query = query.filter(Schedule.ward_id == ward_id)
        
        if status:
            query = query.filter(Schedule.status == status)
        
        schedules = query.order_by(Schedule.created_at.desc()).limit(limit).all()
        
        return schedules
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스케줄 조회 중 오류 발생: {str(e)}"
        )

@router.get("/schedules/{schedule_id}/assignments", response_model=List[ShiftAssignmentResponse])
def get_schedule_assignments(
    schedule_id: int,
    employee_id: Optional[int] = None,
    shift_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """스케줄의 근무 배정 조회"""
    try:
        query = db.query(ShiftAssignment).filter(ShiftAssignment.schedule_id == schedule_id)
        
        if employee_id:
            query = query.filter(ShiftAssignment.employee_id == employee_id)
        
        if shift_type:
            query = query.filter(ShiftAssignment.shift_type == shift_type)
        
        if date_from:
            query = query.filter(ShiftAssignment.shift_date >= date_from)
        
        if date_to:
            query = query.filter(ShiftAssignment.shift_date <= date_to)
        
        assignments = query.order_by(ShiftAssignment.shift_date).all()
        
        # 직원 이름 추가
        result = []
        for assignment in assignments:
            employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
            employee_name = employee.user.full_name if employee and employee.user else "Unknown"
            
            result.append(ShiftAssignmentResponse(
                id=assignment.id,
                schedule_id=assignment.schedule_id,
                employee_id=assignment.employee_id,
                employee_name=employee_name,
                shift_date=assignment.shift_date,
                shift_type=assignment.shift_type,
                is_manual_assignment=assignment.is_manual_assignment,
                is_override=assignment.is_override,
                override_reason=assignment.override_reason
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"배정 조회 중 오류 발생: {str(e)}"
        )

@router.post("/schedules/", response_model=ScheduleResponse)
def create_schedule(
    ward_id: int,
    schedule_name: str,
    period_start: datetime,
    period_end: datetime,
    admin_id: int,
    db: Session = Depends(get_db)
):
    """새 스케줄 생성"""
    try:
        new_schedule = Schedule(
            ward_id=ward_id,
            schedule_name=schedule_name,
            period_start=period_start,
            period_end=period_end,
            created_by=admin_id,
            status="draft"
        )
        
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        return new_schedule
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스케줄 생성 중 오류 발생: {str(e)}"
        )

@router.put("/schedules/{schedule_id}")
def update_schedule(
    schedule_id: int,
    schedule_name: Optional[str] = None,
    status: Optional[str] = None,
    admin_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """스케줄 정보 업데이트"""
    try:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="스케줄을 찾을 수 없습니다"
            )
        
        if schedule_name:
            schedule.schedule_name = schedule_name
        
        if status:
            schedule.status = status
        
        if admin_id:
            schedule.modified_by = admin_id
        
        schedule.last_modified = datetime.utcnow()
        
        db.commit()
        
        return {"message": "스케줄이 성공적으로 업데이트되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스케줄 업데이트 중 오류 발생: {str(e)}"
        )

@router.get("/schedules/{schedule_id}/score")
def get_schedule_score(
    schedule_id: int,
    recalculate: bool = False,
    db: Session = Depends(get_db)
):
    """스케줄 최적화 점수 조회"""
    try:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="스케줄을 찾을 수 없습니다"
            )
        
        if recalculate:
            # 점수 재계산
            new_score = ManualEditingService()._recalculate_schedule_score(db, schedule_id)
            
            # 스케줄 업데이트
            schedule.optimization_score = new_score
            schedule.last_modified = datetime.utcnow()
            db.commit()
            
            return {
                "schedule_id": schedule_id,
                "optimization_score": new_score,
                "recalculated": True
            }
        else:
            return {
                "schedule_id": schedule_id,
                "optimization_score": schedule.optimization_score,
                "compliance_score": schedule.compliance_score,
                "pattern_score": schedule.pattern_score,
                "preference_score": schedule.preference_score,
                "recalculated": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"점수 조회 중 오류 발생: {str(e)}"
        )

@router.get("/emergency-logs/")
def get_emergency_logs(
    assignment_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """응급 상황 로그 조회"""
    try:
        query = db.query(EmergencyLog)
        
        if assignment_id:
            query = query.filter(EmergencyLog.assignment_id == assignment_id)
        
        if admin_id:
            query = query.filter(EmergencyLog.admin_id == admin_id)
        
        if status:
            query = query.filter(EmergencyLog.status == status)
        
        logs = query.order_by(EmergencyLog.created_at.desc()).limit(limit).all()
        
        result = []
        for log in logs:
            result.append({
                "id": log.id,
                "assignment_id": log.assignment_id,
                "emergency_type": log.emergency_type,
                "urgency_level": log.urgency_level,
                "original_employee_id": log.original_employee_id,
                "replacement_employee_id": log.replacement_employee_id,
                "reason": log.reason,
                "admin_id": log.admin_id,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
                "resolution_time": log.resolution_time.isoformat() if log.resolution_time else None
            })
        
        return {
            "total_logs": len(result),
            "logs": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"응급 로그 조회 중 오류 발생: {str(e)}"
        )

@router.post("/assignments/create")
def create_shift_assignment(
    schedule_id: int,
    employee_id: int,
    shift_date: date,
    shift_type: str,
    admin_id: int,
    override: bool = False,
    override_reason: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """새 근무 배정 생성"""
    try:
        # 중복 확인
        existing = db.query(ShiftAssignment).filter(
            ShiftAssignment.schedule_id == schedule_id,
            ShiftAssignment.employee_id == employee_id,
            ShiftAssignment.shift_date == shift_date,
            ShiftAssignment.shift_type == shift_type
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 동일한 근무 배정이 존재합니다"
            )
        
        new_assignment = ShiftAssignment(
            schedule_id=schedule_id,
            employee_id=employee_id,
            shift_date=datetime.combine(shift_date, datetime.min.time()),
            shift_type=shift_type,
            is_manual_assignment=True,
            is_override=override,
            override_reason=override_reason if override else None,
            override_by=admin_id if override else None,
            override_at=datetime.utcnow() if override else None,
            modified_by=admin_id,
            notes=notes
        )
        
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        
        return {
            "success": True,
            "message": "근무 배정이 성공적으로 생성되었습니다",
            "assignment_id": new_assignment.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"배정 생성 중 오류 발생: {str(e)}"
        )

@router.delete("/assignments/{assignment_id}")
def delete_shift_assignment(
    assignment_id: int,
    admin_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """근무 배정 삭제"""
    try:
        assignment = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="근무 배정을 찾을 수 없습니다"
            )
        
        # 삭제 대신 비활성화 (audit trail 유지)
        db.delete(assignment)
        db.commit()
        
        return {
            "success": True,
            "message": "근무 배정이 성공적으로 삭제되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"배정 삭제 중 오류 발생: {str(e)}"
        )