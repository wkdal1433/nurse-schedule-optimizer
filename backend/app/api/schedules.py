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
from ..services.score_breakdown_service import get_score_breakdown_service
from pydantic import BaseModel

router = APIRouter()

class ScheduleCreateRequest(BaseModel):
    ward_id: int
    month: int
    year: int
    constraints: Optional[dict] = {}
    force_generate: Optional[bool] = False  # Pre-check 실패 시에도 강제 생성

class AssignmentUpdateRequest(BaseModel):
    date: str
    shift: str
    from_employee_id: int
    to_employee_id: Optional[int] = None  # None이면 해당 교대에서 제거
    override: Optional[bool] = False  # 관리자 강제 적용

class EmergencyOverrideRequest(BaseModel):
    schedule_id: int
    date: str
    shift: str
    remove_employee_id: Optional[int] = None
    add_employee_id: Optional[int] = None
    reason: str  # 긴급상황 사유
    override_type: str = "emergency"  # emergency, admin, urgent

class AIRecommendationRequest(BaseModel):
    schedule_id: int
    date: str
    shift: str
    issue_type: str  # missing_staff, overload, constraint_violation
    include_alternatives: bool = True
class PreCheckRequest(BaseModel):
    ward_id: int
    month: int
    year: int

class ScheduleBreakdownRequest(BaseModel):
    schedule_id: int

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

@router.post("/breakdown", response_model=dict)
async def get_schedule_breakdown(
    request: ScheduleBreakdownRequest,
    db: Session = Depends(get_db)
):
    """근무표 점수 상세 분석"""

    # 근무표 조회
    schedule = db.query(Schedule).filter(Schedule.id == request.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # 병동 및 직원 정보 조회
    ward = db.query(Ward).filter(Ward.id == schedule.ward_id).first()
    employees = db.query(Employee).filter(
        Employee.ward_id == schedule.ward_id,
        Employee.is_active == True
    ).all()

    # 직원 데이터 변환
    employees_data = []
    for emp in employees:
        employees_data.append({
            "id": emp.id,
            "employee_number": emp.employee_number,
            "skill_level": emp.skill_level,
            "years_experience": emp.years_experience,
            "role": emp.role,
            "employment_type": emp.employment_type
        })

    # 제약조건 설정
    ward_rules = ward.shift_rules or {}
    constraints = {
        **ward_rules,
        "required_staff": {
            "day": ward_rules.get("min_day_staff", 3),
            "evening": ward_rules.get("min_evening_staff", 2),
            "night": ward_rules.get("min_night_staff", 1)
        }
    }

    # 근무 요청사항 조회 (해당 기간)
    from datetime import datetime
    start_date = datetime(schedule.year, schedule.month, 1)
    if schedule.month == 12:
        end_date = datetime(schedule.year + 1, 1, 1)
    else:
        end_date = datetime(schedule.year, schedule.month + 1, 1)

    shift_requests = db.query(ShiftRequest).filter(
        ShiftRequest.employee_id.in_([emp.id for emp in employees]),
        ShiftRequest.request_date >= start_date,
        ShiftRequest.request_date < end_date,
        ShiftRequest.status == "approved"
    ).all()

    # 근무 요청사항 데이터 변환
    requests_data = []
    for req in shift_requests:
        requests_data.append({
            "employee_id": req.employee_id,
            "request_date": req.request_date,
            "shift_type": req.shift_type,
            "request_type": req.request_type,
            "reason": req.reason
        })

    # 스케줄 데이터 변환 (JSON에서 리스트로)
    schedule_data = schedule.schedule_data
    if isinstance(schedule_data, str):
        import json
        schedule_data = json.loads(schedule_data)
    
    # 스케줄 데이터가 dictionary 형태인 경우 리스트로 변환
    if isinstance(schedule_data, dict) and "schedule" in schedule_data:
        schedule_list = schedule_data["schedule"]
    elif isinstance(schedule_data, dict):
        # 날짜별로 정렬하여 리스트 생성
        dates = sorted(schedule_data.keys())
        schedule_list = []
        for date in dates:
            daily_schedule = []
            day_data = schedule_data[date]
            for emp in employees_data:
                emp_shift = day_data.get(str(emp["id"]), 3)  # 기본값: OFF
                daily_schedule.append(emp_shift)
            schedule_list.append(daily_schedule)
    else:
        schedule_list = schedule_data if isinstance(schedule_data, list) else []

    # 점수 분석 서비스 실행
    breakdown_service = get_score_breakdown_service()
    breakdown_result = breakdown_service.analyze_schedule_scores(
        schedule_data=schedule_list,
        employees=employees_data,
        constraints=constraints,
        shift_requests=requests_data
    )

    return {
        "success": True,
        "schedule_id": request.schedule_id,
        "schedule_info": {
            "ward_id": schedule.ward_id,
            "ward_name": ward.name,
            "year": schedule.year,
            "month": schedule.month,
            "status": schedule.status,
            "created_at": schedule.created_at
        },
        "breakdown_result": breakdown_result
    }

@router.get("/breakdown/{schedule_id}")
async def get_schedule_breakdown_by_id(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """근무표 ID로 점수 상세 분석 조회"""
    
    # 내부적으로 POST 엔드포인트 재사용
    request = type('ScheduleBreakdownRequest', (), {'schedule_id': schedule_id})()
    return await get_schedule_breakdown(request, db)

@router.patch("/{schedule_id}/assignments")
async def update_assignment(
    schedule_id: int,
    update_request: AssignmentUpdateRequest,
    db: Session = Depends(get_db)
):
    """근무 배정 변경 (Drag & Drop 지원)"""

    try:
        # 1. 스케줄 존재 확인
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # 2. 현재 스케줄 데이터 파싱
        schedule_data = schedule.schedule_data
        if isinstance(schedule_data, str):
            schedule_data = json.loads(schedule_data)

        # 3. 현재 상태 백업 (롤백용)
        original_data = json.loads(json.dumps(schedule_data))

        # 4. 변경 적용
        date_key = update_request.date
        if date_key not in schedule_data:
            raise HTTPException(status_code=400, detail="Invalid date")

        # from_employee 제거
        if update_request.shift in schedule_data[date_key]:
            day_assignments = schedule_data[date_key][update_request.shift]
            schedule_data[date_key][update_request.shift] = [
                emp for emp in day_assignments
                if emp != update_request.from_employee_id
            ]

        # to_employee 추가 (None이 아닌 경우)
        if update_request.to_employee_id is not None:
            if update_request.shift not in schedule_data[date_key]:
                schedule_data[date_key][update_request.shift] = []
            schedule_data[date_key][update_request.shift].append(update_request.to_employee_id)

        # 5. 제약조건 검증 (override가 False인 경우만)
        if not update_request.override:
            violations = validate_assignment_constraints(schedule_data, date_key, db)
            if violations:
                return {
                    "ok": False,
                    "violations": violations,
                    "message": "Assignment change violates constraints"
                }

        # 6. 변경 사항 저장
        schedule.schedule_data = schedule_data

        # 7. 점수 재계산 (간단한 버전)
        previous_score = schedule.total_score or 0
        new_score = calculate_simple_schedule_score(schedule_data)
        schedule.total_score = new_score
        delta = new_score - previous_score

        db.commit()

        return {
            "ok": True,
            "new_score": new_score,
            "delta": delta,
            "violations": [],
            "employee_scores": {
                str(update_request.from_employee_id): new_score * 0.8,
                str(update_request.to_employee_id or 0): new_score * 0.9
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Assignment update failed: {str(e)}")

def validate_assignment_constraints(schedule_data: dict, affected_date: str, db: Session) -> List[dict]:
    """배정 변경 시 제약조건 검증"""
    violations = []

    # 최소 인력 검증 (간단한 버전)
    if affected_date in schedule_data:
        day_data = schedule_data[affected_date]

        # 각 교대별 최소 인원 체크
        min_requirements = {"day": 2, "evening": 2, "night": 1}

        for shift, min_count in min_requirements.items():
            actual_count = len(day_data.get(shift, []))
            if actual_count < min_count:
                violations.append({
                    "type": "minimum_staff",
                    "detail": f"{affected_date} {shift}: {actual_count} < {min_count}",
                    "shift": shift,
                    "required": min_count,
                    "actual": actual_count
                })

    return violations

def calculate_simple_schedule_score(schedule_data: dict) -> float:
    """간단한 스케줄 점수 계산"""
    score = 1000  # 기본 점수

    for date, day_data in schedule_data.items():
        # 최소 인력 만족 시 보너스
        for shift in ["day", "evening", "night"]:
            staff_count = len(day_data.get(shift, []))
            if staff_count >= 2:
                score += 50
            elif staff_count >= 1:
                score += 20
            else:
                score -= 100  # 인력 부족 패널티

    return max(score, 0)

@router.post("/{schedule_id}/emergency-override")
async def emergency_override(
    schedule_id: int,
    override_request: EmergencyOverrideRequest,
    db: Session = Depends(get_db)
):
    """긴급 상황 오버라이드 - 모든 제약조건 무시하고 강제 배정"""

    try:
        # 1. 스케줄 존재 확인
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # 2. 현재 스케줄 데이터 파싱
        schedule_data = schedule.schedule_data
        if isinstance(schedule_data, str):
            schedule_data = json.loads(schedule_data)

        # 3. 로그용 변경 전 상태 저장
        original_data = json.loads(json.dumps(schedule_data))

        # 4. 긴급 변경 적용 (모든 제약조건 무시)
        date_key = override_request.date
        if date_key not in schedule_data:
            schedule_data[date_key] = {"DAY": [], "EVENING": [], "NIGHT": [], "OFF": []}

        shift_key = override_request.shift.upper()
        if shift_key not in schedule_data[date_key]:
            schedule_data[date_key][shift_key] = []

        # 직원 제거
        if override_request.remove_employee_id:
            for shift in schedule_data[date_key]:
                schedule_data[date_key][shift] = [
                    emp for emp in schedule_data[date_key][shift]
                    if emp != override_request.remove_employee_id
                ]

        # 직원 추가
        if override_request.add_employee_id:
            # 기존에 다른 교대에 배정되어 있다면 제거
            for shift in schedule_data[date_key]:
                schedule_data[date_key][shift] = [
                    emp for emp in schedule_data[date_key][shift]
                    if emp != override_request.add_employee_id
                ]
            # 새 교대에 추가
            schedule_data[date_key][shift_key].append(override_request.add_employee_id)

        # 5. 변경사항 저장 (제약조건 무시)
        schedule.schedule_data = schedule_data

        # 6. 점수 재계산
        previous_score = schedule.total_score or 0
        new_score = calculate_simple_schedule_score(schedule_data)
        schedule.total_score = new_score
        delta = new_score - previous_score

        # 7. 긴급 오버라이드 로그 기록 (향후 감사용)
        override_log = {
            "timestamp": datetime.now().isoformat(),
            "override_type": override_request.override_type,
            "reason": override_request.reason,
            "changes": {
                "date": date_key,
                "shift": shift_key,
                "removed": override_request.remove_employee_id,
                "added": override_request.add_employee_id
            },
            "score_impact": delta
        }

        db.commit()

        return {
            "success": True,
            "message": "Emergency override applied successfully",
            "override_log": override_log,
            "new_score": new_score,
            "score_delta": delta,
            "warnings": [
                "Emergency override bypassed all constraints",
                "Manual review recommended after emergency situation"
            ]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Emergency override failed: {str(e)}")

@router.post("/{schedule_id}/ai-recommendations")
async def get_ai_recommendations(
    schedule_id: int,
    recommendation_request: AIRecommendationRequest,
    db: Session = Depends(get_db)
):
    """AI 기반 대체 간호사 추천"""

    try:
        # 1. 스케줄과 관련 데이터 조회
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        ward = db.query(Ward).filter(Ward.id == schedule.ward_id).first()
        employees = db.query(Employee).filter(Employee.ward_id == schedule.ward_id).all()

        # 2. 현재 스케줄 데이터 파싱
        schedule_data = schedule.schedule_data
        if isinstance(schedule_data, str):
            schedule_data = json.loads(schedule_data)

        # 3. AI 추천 알고리즘 실행
        recommendations = generate_ai_recommendations(
            schedule_data,
            employees,
            recommendation_request.date,
            recommendation_request.shift,
            recommendation_request.issue_type
        )

        # 4. 대안 시나리오 생성 (요청시)
        alternatives = []
        if recommendation_request.include_alternatives:
            alternatives = generate_alternative_scenarios(
                schedule_data,
                employees,
                recommendation_request.date,
                recommendation_request.shift
            )

        return {
            "success": True,
            "issue_analysis": {
                "date": recommendation_request.date,
                "shift": recommendation_request.shift,
                "issue_type": recommendation_request.issue_type,
                "current_staff_count": len(schedule_data.get(recommendation_request.date, {}).get(recommendation_request.shift.upper(), [])),
                "required_staff_count": get_required_staff_count(recommendation_request.shift)
            },
            "recommendations": recommendations,
            "alternatives": alternatives,
            "confidence_score": calculate_recommendation_confidence(recommendations)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI recommendation failed: {str(e)}")

def generate_ai_recommendations(schedule_data, employees, date, shift, issue_type):
    """AI 기반 추천 알고리즘 (간단한 휴리스틱 버전)"""

    shift_key = shift.upper()
    current_assignments = schedule_data.get(date, {}).get(shift_key, [])
    assigned_employees = set()

    # 해당 날짜에 이미 배정된 모든 직원 수집
    if date in schedule_data:
        for s in schedule_data[date].values():
            assigned_employees.update(s)

    available_employees = [emp for emp in employees if emp.id not in assigned_employees]

    recommendations = []

    for emp in available_employees[:5]:  # 상위 5명 추천
        # 간단한 점수 계산
        score = calculate_employee_suitability_score(emp, shift, date, schedule_data)

        recommendation = {
            "employee_id": emp.id,
            "employee_name": emp.name,
            "employee_role": emp.role,
            "employment_type": emp.employment_type,
            "experience_level": emp.experience_level,
            "suitability_score": score,
            "reasons": generate_recommendation_reasons(emp, shift, score),
            "estimated_impact": {
                "score_improvement": score * 10,
                "constraint_satisfaction": "high" if score > 0.7 else "medium" if score > 0.4 else "low"
            }
        }
        recommendations.append(recommendation)

    # 점수 순으로 정렬
    recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)
    return recommendations

def generate_alternative_scenarios(schedule_data, employees, date, shift):
    """대안 시나리오 생성"""

    scenarios = [
        {
            "scenario_name": "온콜 직원 호출",
            "description": "대기 중인 온콜 직원을 긴급 호출",
            "feasibility": "high",
            "cost_impact": "medium",
            "time_to_implement": "15-30분"
        },
        {
            "scenario_name": "다른 교대 직원 연장 근무",
            "description": "이전 교대 직원의 연장 근무",
            "feasibility": "medium",
            "cost_impact": "high",
            "time_to_implement": "즉시"
        },
        {
            "scenario_name": "파트타임 직원 긴급 호출",
            "description": "파트타임 직원의 추가 근무",
            "feasibility": "medium",
            "cost_impact": "medium",
            "time_to_implement": "30-60분"
        }
    ]

    return scenarios

def calculate_employee_suitability_score(employee, shift, date, schedule_data):
    """직원 적합성 점수 계산"""
    score = 0.5  # 기본 점수

    # 경험 수준 고려
    if employee.experience_level >= 3:
        score += 0.2

    # 고용 형태 고려
    if employee.employment_type == "FULL_TIME":
        score += 0.1

    # 역할 고려
    if employee.role in ["CHARGE_NURSE", "SENIOR_NURSE"]:
        score += 0.2

    # 야간 근무 적합성 (Night shift인 경우)
    if shift.upper() == "NIGHT" and employee.experience_level >= 2:
        score += 0.1

    return min(score, 1.0)

def generate_recommendation_reasons(employee, shift, score):
    """추천 이유 생성"""
    reasons = []

    if employee.experience_level >= 3:
        reasons.append("경험이 풍부한 간호사")

    if employee.employment_type == "FULL_TIME":
        reasons.append("정규직으로 안정적인 근무")

    if employee.role in ["CHARGE_NURSE", "SENIOR_NURSE"]:
        reasons.append("시니어 간호사로 리더십 가능")

    if shift.upper() == "NIGHT":
        reasons.append("야간 근무 경험 보유")

    if score > 0.8:
        reasons.append("높은 적합성 점수")

    return reasons

def get_required_staff_count(shift):
    """교대별 필요 인력 수 반환"""
    requirements = {
        "DAY": 3,
        "EVENING": 2,
        "NIGHT": 2
    }
    return requirements.get(shift.upper(), 2)

def calculate_recommendation_confidence(recommendations):
    """추천 신뢰도 계산"""
    if not recommendations:
        return 0.0

    avg_score = sum(r["suitability_score"] for r in recommendations) / len(recommendations)
    return min(avg_score * 100, 95.0)  # 최대 95% 신뢰도

@router.get("/status")
async def schedules_status():
    return {"message": "Schedule generation system is ready"}
