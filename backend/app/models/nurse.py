"""
간호사 관련 데이터 모델
"""
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class EmploymentType(str, Enum):
    """고용 형태"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"


class NurseRole(str, Enum):
    """간호사 역할"""
    HEAD_NURSE = "head_nurse"
    STAFF_NURSE = "staff_nurse"
    NEW_NURSE = "new_nurse"
    EDUCATION_COORDINATOR = "education_coordinator"


class ExperienceLevel(str, Enum):
    """경험 수준"""
    SENIOR = "senior"  # 5년 이상
    INTERMEDIATE = "intermediate"  # 2-5년
    JUNIOR = "junior"  # 2년 미만


class Nurse(BaseModel):
    """간호사 모델"""
    id: Optional[int] = None
    name: str
    employee_id: str
    role: NurseRole
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    years_of_experience: int
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NursePreference(BaseModel):
    """간호사 개인 선호도"""
    id: Optional[int] = None
    nurse_id: int
    prefer_day_shift: bool = True
    prefer_evening_shift: bool = True
    prefer_night_shift: bool = False
    max_consecutive_days: int = 5
    max_consecutive_nights: int = 2
    preferred_days_off: List[int] = []  # 0=Monday, 1=Tuesday, ...
    avoid_patterns: List[str] = []  # ["day_to_night", "consecutive_nights_over_2"]


class NurseRequest(BaseModel):
    """간호사 요청 (휴가, 특정 시프트 회피 등)"""
    id: Optional[int] = None
    nurse_id: int
    request_type: str  # "vacation", "sick_leave", "avoid_shift", "prefer_shift"
    start_date: datetime
    end_date: datetime
    shift_type: Optional[str] = None  # "day", "evening", "night"
    reason: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "rejected"
    created_at: Optional[datetime] = None


class NurseCreateRequest(BaseModel):
    """간호사 생성 요청"""
    name: str
    employee_id: str
    role: NurseRole
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    years_of_experience: int
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None


class NurseUpdateRequest(BaseModel):
    """간호사 정보 수정 요청"""
    name: Optional[str] = None
    role: Optional[NurseRole] = None
    employment_type: Optional[EmploymentType] = None
    experience_level: Optional[ExperienceLevel] = None
    years_of_experience: Optional[int] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class NurseResponse(BaseModel):
    """간호사 응답 모델"""
    id: int
    name: str
    employee_id: str
    role: NurseRole
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    years_of_experience: int
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None