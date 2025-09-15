"""
근무 시간 계산 유틸리티
Single Responsibility: 근무 시간 계산만 담당
"""
from typing import Dict


class ShiftCalculator:
    """근무 시간 계산기"""

    def __init__(self):
        self.shift_hours_map = {
            'day': 8,
            'evening': 8,
            'night': 8,
            'off': 0,
            'half_day': 4,
            'overtime': 12
        }

    def get_shift_hours(self, shift_type: str) -> int:
        """근무 타입별 시간 반환"""
        return self.shift_hours_map.get(shift_type.lower(), 8)

    def calculate_weekly_hours(self, assignments: list) -> int:
        """주간 총 근무시간 계산"""
        return sum(self.get_shift_hours(assignment.shift_type)
                  for assignment in assignments)

    def calculate_monthly_hours(self, assignments: list) -> int:
        """월간 총 근무시간 계산"""
        return sum(self.get_shift_hours(assignment.shift_type)
                  for assignment in assignments)

    def is_overtime_shift(self, shift_type: str) -> bool:
        """초과 근무 여부 확인"""
        return shift_type.lower() in ['overtime', 'double_shift']

    def get_shift_duration_minutes(self, shift_type: str) -> int:
        """근무 시간을 분 단위로 반환"""
        return self.get_shift_hours(shift_type) * 60

    def add_custom_shift_type(self, shift_type: str, hours: int):
        """커스텀 근무 타입 추가"""
        self.shift_hours_map[shift_type.lower()] = hours

    def get_all_shift_types(self) -> Dict[str, int]:
        """모든 근무 타입과 시간 반환"""
        return self.shift_hours_map.copy()