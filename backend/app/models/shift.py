"""
시프트 관련 데이터 모델
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, time


class ShiftType(str, Enum):
    """시프트 유형"""
    DAY = "day"      # 주간 (08:00-16:00)
    EVENING = "evening"  # 오후 (16:00-24:00)
    NIGHT = "night"    # 야간 (24:00-08:00)
    OFF = "off"       # 휴무


class ShiftStatus(str, Enum):
    """시프트 상태"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EMERGENCY_CHANGED = "emergency_changed"


class Department(str, Enum):
    """부서"""
    ICU = "icu"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    PEDIATRICS = "pediatrics"
    INTERNAL_MEDICINE = "internal_medicine"
    GENERAL = "general"


class Shift(BaseModel):
    """시프트 모델"""
    id: Optional[int] = None
    date: datetime
    shift_type: ShiftType
    department: Department
    start_time: time
    end_time: time
    required_nurses: int
    assigned_nurses: List[int] = []  # nurse_ids
    head_nurse_id: Optional[int] = None
    minimum_experience_level: str = "junior"
    requires_senior_nurse: bool = False
    status: ShiftStatus = ShiftStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ShiftAssignment(BaseModel):
    """시프트 배정"""
    id: Optional[int] = None
    shift_id: int
    nurse_id: int
    role_in_shift: str = "staff"  # "head", "staff", "support"
    assignment_score: Optional[float] = None
    is_emergency_assignment: bool = False
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None


class ShiftTemplate(BaseModel):
    """시프트 템플릿 (반복되는 시프트 패턴)"""
    id: Optional[int] = None
    name: str
    department: Department
    day_of_week: int  # 0=Monday, 1=Tuesday, ...
    shift_type: ShiftType
    start_time: time
    end_time: time
    required_nurses: int
    minimum_experience_level: str = "junior"
    requires_senior_nurse: bool = False
    is_active: bool = True


class ShiftRule(BaseModel):
    """시프트 규칙"""
    id: Optional[int] = None
    name: str
    description: str
    rule_type: str  # "hard", "soft"
    department: Optional[Department] = None
    max_consecutive_days: int = 5
    max_consecutive_nights: int = 2
    min_rest_hours_between_shifts: int = 8
    max_weekly_hours: int = 40
    min_weekly_rest_days: int = 1
    penalty_score: int = 100
    is_active: bool = True


class ShiftCreateRequest(BaseModel):
    """시프트 생성 요청"""
    date: datetime
    shift_type: ShiftType
    department: Department
    start_time: time
    end_time: time
    required_nurses: int
    head_nurse_id: Optional[int] = None
    minimum_experience_level: str = "junior"
    requires_senior_nurse: bool = False
    notes: Optional[str] = None


class ShiftUpdateRequest(BaseModel):
    """시프트 수정 요청"""
    shift_type: Optional[ShiftType] = None
    required_nurses: Optional[int] = None
    assigned_nurses: Optional[List[int]] = None
    head_nurse_id: Optional[int] = None
    minimum_experience_level: Optional[str] = None
    requires_senior_nurse: Optional[bool] = None
    status: Optional[ShiftStatus] = None
    notes: Optional[str] = None


class ShiftAssignmentRequest(BaseModel):
    """시프트 배정 요청"""
    nurse_id: int
    role_in_shift: str = "staff"
    is_emergency_assignment: bool = False


class EmergencyOverrideRequest(BaseModel):
    """응급 상황 오버라이드 요청"""
    shift_id: int
    original_nurse_id: Optional[int] = None
    replacement_nurse_id: int
    reason: str
    override_by: str  # 관리자 ID 또는 이름
    emergency_type: str  # "illness", "absence", "emergency"


class ShiftResponse(BaseModel):
    """시프트 응답 모델"""
    id: int
    date: datetime
    shift_type: ShiftType
    department: Department
    start_time: time
    end_time: time
    required_nurses: int
    assigned_nurses: List[Dict[str, Any]]  # 간호사 정보 포함
    head_nurse_id: Optional[int] = None
    head_nurse_name: Optional[str] = None
    minimum_experience_level: str
    requires_senior_nurse: bool
    status: ShiftStatus
    notes: Optional[str] = None
    assignment_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None