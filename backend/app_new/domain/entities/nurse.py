"""
Domain Entity: Nurse
간호사 핵심 비즈니스 엔티티
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from datetime import datetime

from ..value_objects.experience_level import ExperienceLevel
from ..value_objects.employment_type import EmploymentType


class NurseRole(Enum):
    HEAD_NURSE = "head_nurse"
    STAFF_NURSE = "staff_nurse"
    NEW_NURSE = "new_nurse"


@dataclass
class Nurse:
    """간호사 도메인 엔티티 - 순수 비즈니스 로직"""

    id: Optional[int]
    employee_number: str
    full_name: str
    role: NurseRole
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    ward_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """비즈니스 규칙 검증"""
        self._validate_business_rules()

    def _validate_business_rules(self):
        """비즈니스 규칙 검증"""
        if not self.employee_number or len(self.employee_number) < 3:
            raise ValueError("직원번호는 최소 3자리 이상이어야 합니다")

        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("이름은 최소 2글자 이상이어야 합니다")

        if self.experience_level.years < 0:
            raise ValueError("경력은 0년 이상이어야 합니다")

    def can_work_night_shift(self) -> bool:
        """야간 근무 가능 여부 판단"""
        if self.role == NurseRole.NEW_NURSE and self.experience_level.years < 1:
            return False
        return self.is_active

    def can_supervise(self) -> bool:
        """감독 업무 가능 여부"""
        return self.role == NurseRole.HEAD_NURSE or (
            self.role == NurseRole.STAFF_NURSE and self.experience_level.years >= 3
        )

    def get_max_consecutive_work_days(self) -> int:
        """최대 연속 근무일 수"""
        if self.employment_type == EmploymentType.PART_TIME:
            return 3
        elif self.role == NurseRole.NEW_NURSE:
            return 4
        else:
            return 5

    def get_max_night_shifts_per_week(self) -> int:
        """주당 최대 야간 근무 횟수"""
        if self.employment_type == EmploymentType.PART_TIME:
            return 2
        elif self.role == NurseRole.NEW_NURSE:
            return 1
        else:
            return 3