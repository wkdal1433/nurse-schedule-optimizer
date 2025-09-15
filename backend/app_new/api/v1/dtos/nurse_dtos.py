"""
DTOs: Nurse Data Transfer Objects
간호사 관련 요청/응답 DTO
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NurseRoleDTO(str, Enum):
    """간호사 역할 DTO"""
    HEAD_NURSE = "head_nurse"
    STAFF_NURSE = "staff_nurse"
    NEW_NURSE = "new_nurse"


class EmploymentTypeDTO(str, Enum):
    """고용 형태 DTO"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"


class CreateNurseRequestDTO(BaseModel):
    """간호사 생성 요청 DTO"""
    employee_number: str = Field(..., min_length=3, max_length=20, description="직원번호")
    full_name: str = Field(..., min_length=2, max_length=50, description="이름")
    role: NurseRoleDTO = Field(..., description="역할")
    employment_type: EmploymentTypeDTO = Field(..., description="고용형태")
    experience_years: int = Field(..., ge=0, le=50, description="경력연수")
    skill_level: Optional[int] = Field(None, ge=1, le=5, description="숙련도 (1-5)")
    ward_id: int = Field(..., gt=0, description="병동 ID")

    @validator('full_name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('이름은 공백일 수 없습니다')
        return v.strip()

    @validator('employee_number')
    def validate_employee_number(cls, v):
        if not v.isalnum():
            raise ValueError('직원번호는 영숫자만 포함할 수 있습니다')
        return v

    class Config:
        schema_extra = {
            "example": {
                "employee_number": "N001",
                "full_name": "김간호사",
                "role": "staff_nurse",
                "employment_type": "full_time",
                "experience_years": 5,
                "skill_level": 3,
                "ward_id": 1
            }
        }


class UpdateNurseRequestDTO(BaseModel):
    """간호사 수정 요청 DTO"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=50)
    role: Optional[NurseRoleDTO] = None
    employment_type: Optional[EmploymentTypeDTO] = None
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    skill_level: Optional[int] = Field(None, ge=1, le=5)
    ward_id: Optional[int] = Field(None, gt=0)

    class Config:
        schema_extra = {
            "example": {
                "full_name": "김수간호사",
                "role": "head_nurse",
                "experience_years": 8
            }
        }


class NurseResponseDTO(BaseModel):
    """간호사 응답 DTO"""
    id: int
    employee_number: str
    full_name: str
    role: NurseRoleDTO
    employment_type: EmploymentTypeDTO
    experience_years: int
    skill_level: int
    ward_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "employee_number": "N001",
                "full_name": "김간호사",
                "role": "staff_nurse",
                "employment_type": "full_time",
                "experience_years": 5,
                "skill_level": 3,
                "ward_id": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00"
            }
        }


class NurseListResponseDTO(BaseModel):
    """간호사 목록 응답 DTO"""
    nurses: List[NurseResponseDTO]
    total_count: int
    page: int = 1
    page_size: int = 20

    class Config:
        schema_extra = {
            "example": {
                "nurses": [],
                "total_count": 25,
                "page": 1,
                "page_size": 20
            }
        }


class SchedulingValidationRequestDTO(BaseModel):
    """스케줄링 검증 요청 DTO"""
    ward_id: int = Field(..., gt=0)
    min_nurses_per_shift: int = Field(..., gt=0, le=20)
    shift_types: List[str] = Field(..., min_items=1)

    class Config:
        schema_extra = {
            "example": {
                "ward_id": 1,
                "min_nurses_per_shift": 3,
                "shift_types": ["DAY", "EVENING", "NIGHT"]
            }
        }


class SchedulingValidationResponseDTO(BaseModel):
    """스케줄링 검증 응답 DTO"""
    sufficient_total_staff: bool
    sufficient_full_time: bool
    sufficient_night_staff: bool
    sufficient_supervisors: bool
    details: Dict[str, int]
    recommendations: Optional[List[str]] = None

    class Config:
        schema_extra = {
            "example": {
                "sufficient_total_staff": True,
                "sufficient_full_time": True,
                "sufficient_night_staff": False,
                "sufficient_supervisors": True,
                "details": {
                    "active_count": 12,
                    "required_count": 9,
                    "night_capable_count": 2,
                    "supervisor_count": 3
                },
                "recommendations": [
                    "야간 근무 가능 간호사를 추가로 배치하세요"
                ]
            }
        }


class ErrorResponseDTO(BaseModel):
    """에러 응답 DTO"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "error_code": "BUSINESS_RULE_VIOLATION",
                "message": "직원번호가 이미 존재합니다",
                "details": {
                    "field": "employee_number",
                    "value": "N001"
                }
            }
        }