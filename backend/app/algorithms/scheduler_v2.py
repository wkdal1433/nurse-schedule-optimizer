"""
SOLID 원칙을 적용한 개선된 스케줄러
기존 거대한 scheduler.py (1197줄)를 SOLID 원칙에 따라 분리한 버전

이 파일은 하위 호환성을 제공하면서 새로운 분리된 아키텍처를 사용합니다.
"""

from typing import Dict, Any, List
from .scheduling import EnhancedNurseScheduler


class NurseScheduler:
    """
    하위 호환성을 위한 래퍼 클래스
    기존 API를 유지하면서 내부적으로는 새로운 분리된 컴포넌트들을 사용
    """

    def __init__(self, ward_id: int, month: int, year: int):
        """
        기존 생성자와 동일한 시그니처 유지
        """
        self.enhanced_scheduler = EnhancedNurseScheduler(ward_id, month, year)

        # 기존 속성들 호환성 유지
        self.ward_id = ward_id
        self.month = month
        self.year = year
        self.days_in_month = self.enhanced_scheduler.days_in_month
        self.shift_types = self.enhanced_scheduler.shift_types

    def generate_optimized_schedule(self, employees: List[Dict],
                                  constraints: Dict[str, Any],
                                  shift_requests: Dict[int, Dict[int, str]] = None) -> Dict[str, Any]:
        """
        기존 메서드 시그니처 유지
        내부적으로는 새로운 분리된 아키텍처 사용
        """
        # 새로운 아키텍처로 스케줄 생성
        schedule_result = self.enhanced_scheduler.generate_optimized_schedule(
            employees, constraints, shift_requests
        )

        # 기존 반환 형식으로 변환
        return schedule_result.to_dict()

    def _get_days_in_month(self, year: int, month: int) -> int:
        """기존 메서드 호환성 유지"""
        return self.enhanced_scheduler.get_days_in_month(year, month)


# 직접 import를 위한 함수들 (하위 호환성)
def create_scheduler(ward_id: int, month: int, year: int) -> NurseScheduler:
    """팩토리 함수 - 하위 호환성"""
    return NurseScheduler(ward_id, month, year)


def generate_schedule(ward_id: int, month: int, year: int,
                     employees: List[Dict], constraints: Dict[str, Any],
                     shift_requests: Dict[int, Dict[int, str]] = None) -> Dict[str, Any]:
    """편의 함수 - 하위 호환성"""
    scheduler = create_scheduler(ward_id, month, year)
    return scheduler.generate_optimized_schedule(employees, constraints, shift_requests)


# 이전 버전과의 호환성을 위한 상수들
SHIFT_TYPES = ["day", "evening", "night", "off"]

# Enum 호환성
class ShiftType:
    DAY = 0
    EVENING = 1
    NIGHT = 2
    OFF = 3


class ConstraintType:
    HARD = "hard"
    SOFT = "soft"


# 마이그레이션 가이드 출력
def print_migration_guide():
    """새로운 아키텍처 사용법 안내"""
    print("""
    🔄 SCHEDULER ARCHITECTURE IMPROVED!

    The monolithic scheduler.py (1197 lines) has been refactored following SOLID principles:

    ✅ NEW STRUCTURE:
    📁 scheduling/
    ├── entities.py              # Core types and enums
    ├── constraint_processor.py  # Constraint handling (SRP)
    ├── fitness_calculator.py    # Score calculation (SRP)
    ├── main_scheduler.py        # Main orchestrator
    └── optimizers/
        └── simulated_annealing.py  # SA algorithm (SRP)

    ✅ BENEFITS:
    - Single Responsibility: Each class has one job
    - Open/Closed: Easy to add new optimizers
    - Dependency Inversion: Abstract interfaces
    - Better testability and maintainability

    ✅ USAGE:
    # Old way (still works):
    from app.algorithms.scheduler import NurseScheduler

    # New way (recommended):
    from app.algorithms.scheduling import EnhancedNurseScheduler

    📖 All existing code continues to work unchanged!
    """)


if __name__ == "__main__":
    print_migration_guide()