from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from ..database.connection import get_db
from ..models.models import Employee, Ward, ShiftRequest
from ..models.scheduling_models import Schedule
from ..algorithms.scheduler import NurseScheduler
from ..services.precheck_service import get_precheck_service
from pydantic import BaseModel

router = APIRouter()

class ScheduleCreateRequest(BaseModel):
    ward_id: int
    month: int
    year: int
    constraints: Optional[dict] = {}
    force_generate: Optional[bool] = False  # Pre-check 실패 시에도 강제 생성
class PreCheckRequest(BaseModel):
    ward_id: int
    month: int
    year: int

class ScheduleResponse(BaseModel):
    id: int
    ward_id: int
    month: int
    year: int
    schedule_data: dict
    total_score: float
    status: str
    created_at: datetime

@router.post("/precheck", response_model=dict)
async def precheck_schedule_generation(
    request: PreCheckRequest,
    db: Session = Depends(get_db)
):
    """근무표 생성 전 사전 검증"""

    precheck_service = get_precheck_service(db)
    result = precheck_service.perform_precheck(
        ward_id=request.ward_id,
        year=request.year,
        month=request.month
    )

    return {
        "success": True,
        "precheck_result": result.to_dict()
    }

@router.post("/generate", response_model=dict)
async def generate_schedule(
    request: ScheduleCreateRequest,
    db: Session = Depends(get_db)
):
    """새로운 근무표 생성"""

    # 1. Pre-check 수행 (force_generate가 False인 경우만)
    if not request.force_generate:
        precheck_service = get_precheck_service(db)
        precheck_result = precheck_service.perform_precheck(
            ward_id=request.ward_id,
            year=request.year,
            month=request.month
        )

        if not precheck_result.is_valid:
            return {
                "success": False,
                "message": "Pre-check failed. Schedule generation blocked.",
                "precheck_result": precheck_result.to_dict(),
                "force_generate_required": True
            }

    # 2. 병동 정보 확인
    ward = db.query(Ward).filter(Ward.id == request.ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    # 3. 해당 병동의 직원들 조회
    employees = db.query(Employee).filter(
        Employee.ward_id == request.ward_id,
        Employee.is_active == True
    ).all()
    
    if len(employees) < 3:
        raise HTTPException(status_code=400, detail="Insufficient number of employees (minimum 3 required)")
    
    # 직원 정보를 딕셔너리 형태로 변환
    employees_data = []
    for emp in employees:
        employees_data.append({
            "id": emp.id,
            "user_id": emp.user_id,
            "employee_number": emp.employee_number,
            "skill_level": emp.skill_level,
            "years_experience": emp.years_experience,
            "preferences": emp.preferences or {},
            "user": {
                "full_name": f"Employee {emp.employee_number}"  # User 관계가 없으므로 임시
            }
        })
    
    # 4. 해당 기간의 근무 요청사항 조회
    start_date = datetime(request.year, request.month, 1)
    if request.month == 12:
        end_date = datetime(request.year + 1, 1, 1)
    else:
        end_date = datetime(request.year, request.month + 1, 1)
    
    shift_requests = db.query(ShiftRequest).filter(
        ShiftRequest.employee_id.in_([emp.id for emp in employees]),
        ShiftRequest.request_date >= start_date,
        ShiftRequest.request_date < end_date,
        ShiftRequest.status == "approved"
    ).all()
    
    # 근무 요청사항을 딕셔너리 형태로 변환
    requests_data = []
    for req in shift_requests:
        requests_data.append({
            "employee_id": req.employee_id,
            "request_date": req.request_date,
            "shift_type": req.shift_type,
            "request_type": req.request_type,
            "reason": req.reason
        })
    
    # 5. 제약조건 설정 (병동 규칙 + 요청 제약조건)
    ward_rules = ward.shift_rules or {}
    constraints = {
        **ward_rules,
        **request.constraints,
        "required_staff": {
            "day": ward_rules.get("min_day_staff", 3),
            "evening": ward_rules.get("min_evening_staff", 2), 
            "night": ward_rules.get("min_night_staff", 1)
        }
    }
    
    # 6. 스케줄러 실행
    try:
        scheduler = NurseScheduler(request.ward_id, request.month, request.year)
        schedule_result = scheduler.generate_schedule(
            employees_data, constraints, requests_data
        )
        
        # 7. 데이터베이스에 저장
        new_schedule = Schedule(
            ward_id=request.ward_id,
            month=request.month,
            year=request.year,
            schedule_data=schedule_result["schedule_data"],
            total_score=schedule_result["total_score"],
            status="draft"
        )
        
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        return {
            "success": True,
            "message": "Schedule generated successfully",
            "schedule_id": new_schedule.id,
            "total_score": schedule_result["total_score"],
            "statistics": schedule_result["statistics"],
            "schedule_data": schedule_result["schedule_data"]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate schedule: {str(e)}")

@router.get("/")
async def get_schedules(
    ward_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """근무표 목록 조회"""
    
    query = db.query(Schedule)
    
    if ward_id:
        query = query.filter(Schedule.ward_id == ward_id)
    if year:
        query = query.filter(Schedule.year == year)
    if month:
        query = query.filter(Schedule.month == month)
    if status:
        query = query.filter(Schedule.status == status)
    
    schedules = query.order_by(Schedule.created_at.desc()).all()
    
    return [
        {
            "id": schedule.id,
            "ward_id": schedule.ward_id,
            "month": schedule.month,
            "year": schedule.year,
            "total_score": schedule.total_score,
            "status": schedule.status,
            "created_at": schedule.created_at
        }
        for schedule in schedules
    ]

@router.get("/{schedule_id}")
async def get_schedule_detail(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """특정 근무표 상세 조회"""
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # 병동 정보도 함께 반환
    ward = db.query(Ward).filter(Ward.id == schedule.ward_id).first()
    
    return {
        "id": schedule.id,
        "ward": {
            "id": ward.id,
            "name": ward.name,
            "description": ward.description
        },
        "month": schedule.month,
        "year": schedule.year,
        "schedule_data": schedule.schedule_data,
        "total_score": schedule.total_score,
        "status": schedule.status,
        "created_at": schedule.created_at,
        "approved_at": schedule.approved_at
    }

@router.put("/{schedule_id}/status")
async def update_schedule_status(
    schedule_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """근무표 상태 업데이트 (draft -> approved -> published)"""
    
    if status not in ["draft", "approved", "published"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.status = status
    if status == "approved":
        schedule.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(schedule)
    
    return {
        "success": True,
        "message": f"Schedule status updated to {status}",
        "schedule_id": schedule.id,
        "status": schedule.status
    }

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """근무표 삭제"""
    
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule.status == "published":
        raise HTTPException(status_code=400, detail="Cannot delete published schedule")
    
    db.delete(schedule)
    db.commit()
    
    return {
        "success": True,
        "message": "Schedule deleted successfully"
    }

@router.get("/precheck/{ward_id}/{year}/{month}")
async def get_precheck_result(
    ward_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """특정 병동/기간에 대한 Pre-check 결과 조회"""

    precheck_service = get_precheck_service(db)
    result = precheck_service.perform_precheck(
        ward_id=ward_id,
        year=year,
        month=month
    )

    return {
        "success": True,
        "ward_id": ward_id,
        "year": year,
        "month": month,
        "precheck_result": result.to_dict()
    }

@router.get("/status")
async def schedules_status():
    return {"message": "Schedule generation system is ready"}
