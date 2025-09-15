"""
Value Object: EmploymentType
고용 형태 값 객체
"""
from enum import Enum


class EmploymentType(Enum):
    """고용 형태 열거형"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"

    @property
    def max_work_hours_per_week(self) -> int:
        """주당 최대 근무 시간"""
        if self == EmploymentType.FULL_TIME:
            return 40
        elif self == EmploymentType.PART_TIME:
            return 24
        else:  # CONTRACT
            return 32

    @property
    def requires_benefits(self) -> bool:
        """복리후생 대상 여부"""
        return self == EmploymentType.FULL_TIME

    def __str__(self) -> str:
        return {
            EmploymentType.FULL_TIME: "정규직",
            EmploymentType.PART_TIME: "시간제",
            EmploymentType.CONTRACT: "계약직"
        }[self]