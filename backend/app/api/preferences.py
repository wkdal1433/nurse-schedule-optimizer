"""
개인 선호도 및 요청 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date
from app.database.connection import get_db
from app.models.models import PreferenceTemplate, ShiftRequestV2, PreferenceScore, Employee
from app.services.preference_service import PreferenceService

router = APIRouter()

# Pydantic 모델들
class PreferenceTemplateCreate(BaseModel):
    preferred_shifts: List[str] = []
    avoided_shifts: List[str] = []
    max_night_shifts_per_month: int = 10
    max_weekend_shifts_per_month: int = 8
    preferred_patterns: List[str] = []
    avoided_patterns: List[str] = []
    max_consecutive_days: int = 3
    min_days_off_after_nights: int = 1
    cannot_work_alone: bool = False
    needs_senior_support: bool = False

class ShiftRequestCreate(BaseModel):
    start_date: str
    end_date: str
    request_type: str  # "vacation", "shift_preference", "avoid", "pattern_request"
    priority: str = "normal"
    shift_type: Optional[str] = None
    reason: str = ""
    medical_reason: bool = False
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict] = None
    flexibility_level: int = 1
    alternative_acceptable: bool = True

class RequestReview(BaseModel):
    status: str  # "approved", "denied", "partially_approved"
    admin_notes: str = ""

class PreferenceTemplateResponse(BaseModel):
    id: int
    employee_id: int
    preferred_shifts: List[str]
    avoided_shifts: List[str]
    max_night_shifts_per_month: int
    max_weekend_shifts_per_month: int
    preferred_patterns: List[str]
    avoided_patterns: List[str]
    max_consecutive_days: int
    min_days_off_after_nights: int
    cannot_work_alone: bool
    needs_senior_support: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ShiftRequestResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    start_date: datetime
    end_date: datetime
    request_type: str
    priority: str
    shift_type: Optional[str]
    reason: str
    medical_reason: bool
    is_recurring: bool
    recurrence_pattern: Optional[Dict]
    flexibility_level: int
    alternative_acceptable: bool
    status: str
    admin_notes: str
    created_at: datetime
    reviewed_at: Optional[datetime]

@router.post("/preferences/{employee_id}", response_model=Dict)
async def create_preference_template(
    employee_id: int,
    preferences: PreferenceTemplateCreate,
    db: Session = Depends(get_db)
):
    """간호사 선호도 템플릿 생성/수정"""
    try:
        # 직원 존재 확인
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직원을 찾을 수 없습니다"
            )
        
        preference_service = PreferenceService(db)
        template = preference_service.create_preference_template(
            employee_id, preferences.dict()
        )
        
        return {
            "message": "선호도가 설정되었습니다",
            "template_id": template.id,
            "employee_id": employee_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"선호도 설정 실패: {str(e)}"
        )

@router.get("/preferences/{employee_id}", response_model=Optional[PreferenceTemplateResponse])
async def get_employee_preferences(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """간호사 선호도 조회"""
    preference_service = PreferenceService(db)
    preferences = preference_service.get_employee_preferences(employee_id)
    
    if not preferences:
        return None
    
    return PreferenceTemplateResponse(
        id=preferences.id,
        employee_id=preferences.employee_id,
        preferred_shifts=preferences.preferred_shifts or [],
        avoided_shifts=preferences.avoided_shifts or [],
        max_night_shifts_per_month=preferences.max_night_shifts_per_month,
        max_weekend_shifts_per_month=preferences.max_weekend_shifts_per_month,
        preferred_patterns=preferences.preferred_patterns or [],
        avoided_patterns=preferences.avoided_patterns or [],
        max_consecutive_days=preferences.max_consecutive_days,
        min_days_off_after_nights=preferences.min_days_off_after_nights,
        cannot_work_alone=preferences.cannot_work_alone,
        needs_senior_support=preferences.needs_senior_support,
        is_active=preferences.is_active,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )

@router.post("/requests/{employee_id}", response_model=Dict)
async def submit_shift_request(
    employee_id: int,
    request: ShiftRequestCreate,
    db: Session = Depends(get_db)
):
    """근무 요청 제출"""
    try:
        # 직원 존재 확인
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="직원을 찾을 수 없습니다"
            )
        
        preference_service = PreferenceService(db)
        request_obj = preference_service.submit_shift_request(
            employee_id, request.dict()
        )
        
        return {
            "message": "요청이 제출되었습니다",
            "request_id": request_obj.id,
            "status": request_obj.status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요청 제출 실패: {str(e)}"
        )

@router.get("/requests/pending", response_model=List[ShiftRequestResponse])
async def get_pending_requests(
    ward_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """대기 중인 요청 조회"""
    preference_service = PreferenceService(db)
    requests = preference_service.get_pending_requests(ward_id)
    
    response = []
    for req in requests:
        response.append(ShiftRequestResponse(
            id=req.id,
            employee_id=req.employee_id,
            employee_name=req.employee.user.full_name,
            start_date=req.start_date,
            end_date=req.end_date,
            request_type=req.request_type,
            priority=req.priority,
            shift_type=req.shift_type,
            reason=req.reason,
            medical_reason=req.medical_reason,
            is_recurring=req.is_recurring,
            recurrence_pattern=req.recurrence_pattern,
            flexibility_level=req.flexibility_level,
            alternative_acceptable=req.alternative_acceptable,
            status=req.status,
            admin_notes=req.admin_notes or "",
            created_at=req.created_at,
            reviewed_at=req.reviewed_at
        ))
    
    return response

@router.put("/requests/{request_id}/review", response_model=Dict)
async def review_shift_request(
    request_id: int,
    review: RequestReview,
    reviewer_id: int,  # 실제로는 인증에서 가져와야 함
    db: Session = Depends(get_db)
):
    """근무 요청 검토"""
    try:
        preference_service = PreferenceService(db)
        reviewed_request = preference_service.review_request(
            request_id, reviewer_id, review.status, review.admin_notes
        )
        
        return {
            "message": "요청이 검토되었습니다",
            "request_id": reviewed_request.id,
            "status": reviewed_request.status,
            "reviewed_at": reviewed_request.reviewed_at
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요청 검토 실패: {str(e)}"
        )

@router.get("/requests/employee/{employee_id}", response_model=List[ShiftRequestResponse])
async def get_employee_requests(
    employee_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """개별 간호사의 요청 조회"""
    query = db.query(ShiftRequestV2).filter(
        ShiftRequestV2.employee_id == employee_id
    )
    
    if status:
        query = query.filter(ShiftRequestV2.status == status)
    
    requests = query.order_by(
        ShiftRequestV2.created_at.desc()
    ).limit(limit).all()
    
    response = []
    for req in requests:
        response.append(ShiftRequestResponse(
            id=req.id,
            employee_id=req.employee_id,
            employee_name=req.employee.user.full_name,
            start_date=req.start_date,
            end_date=req.end_date,
            request_type=req.request_type,
            priority=req.priority,
            shift_type=req.shift_type,
            reason=req.reason,
            medical_reason=req.medical_reason,
            is_recurring=req.is_recurring,
            recurrence_pattern=req.recurrence_pattern,
            flexibility_level=req.flexibility_level,
            alternative_acceptable=req.alternative_acceptable,
            status=req.status,
            admin_notes=req.admin_notes or "",
            created_at=req.created_at,
            reviewed_at=req.reviewed_at
        ))
    
    return response

@router.get("/fairness/{schedule_id}", response_model=Dict)
async def get_fairness_analysis(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """스케줄 공정성 분석"""
    from app.models.scheduling_models import Schedule
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스케줄을 찾을 수 없습니다"
        )
    
    preference_service = PreferenceService(db)
    analysis = preference_service.get_fairness_analysis(schedule)
    
    return analysis

@router.get("/statistics/requests", response_model=Dict)
async def get_request_statistics(
    ward_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """요청 통계 조회"""
    preference_service = PreferenceService(db)
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    stats = preference_service.get_request_statistics(ward_id, start_dt, end_dt)
    
    return stats

@router.get("/templates/defaults", response_model=Dict)
async def get_default_preference_template():
    """기본 선호도 템플릿 조회"""
    return {
        "preferred_shifts": ["day", "evening"],
        "avoided_shifts": ["night"],
        "max_night_shifts_per_month": 8,
        "max_weekend_shifts_per_month": 6,
        "preferred_patterns": ["day->off", "evening->off"],
        "avoided_patterns": ["night->day", "day->night"],
        "max_consecutive_days": 3,
        "min_days_off_after_nights": 1,
        "cannot_work_alone": False,
        "needs_senior_support": False
    }

@router.post("/preferences/bulk", response_model=Dict)
async def create_bulk_preferences(
    preferences_data: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """여러 간호사 선호도 일괄 설정"""
    preference_service = PreferenceService(db)
    created_count = 0
    errors = []
    
    for pref_data in preferences_data:
        try:
            employee_id = pref_data.pop("employee_id")
            preference_service.create_preference_template(employee_id, pref_data)
            created_count += 1
        except Exception as e:
            errors.append({
                "employee_id": pref_data.get("employee_id"),
                "error": str(e)
            })
    
    return {
        "message": f"{created_count}개 선호도가 설정되었습니다",
        "created_count": created_count,
        "errors": errors
    }

@router.get("/dashboard/{ward_id}", response_model=Dict)
async def get_preference_dashboard(
    ward_id: int,
    db: Session = Depends(get_db)
):
    """선호도 관리 대시보드 데이터"""
    preference_service = PreferenceService(db)
    
    # 대기 중인 요청
    pending_requests = preference_service.get_pending_requests(ward_id)
    
    # 최근 통계
    stats = preference_service.get_request_statistics(
        ward_id, 
        datetime.now().replace(day=1),  # 이번 달 시작
        datetime.now()
    )
    
    # 간호사별 선호도 설정 현황
    employees = db.query(Employee).filter(
        Employee.ward_id == ward_id,
        Employee.is_active == True
    ).all()
    
    preferences_set = 0
    for emp in employees:
        if preference_service.get_employee_preferences(emp.id):
            preferences_set += 1
    
    return {
        "ward_id": ward_id,
        "total_employees": len(employees),
        "preferences_set_count": preferences_set,
        "preferences_set_rate": (preferences_set / len(employees)) * 100 if employees else 0,
        "pending_requests": len(pending_requests),
        "urgent_requests": len([r for r in pending_requests if r.priority == "urgent"]),
        "medical_requests": len([r for r in pending_requests if r.medical_reason]),
        "monthly_stats": stats,
        "recent_requests": pending_requests[:5]  # 최근 5개만
    }