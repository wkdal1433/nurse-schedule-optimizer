"""
스케줄링 관련 핵심 엔티티 및 Enum 정의
Single Responsibility: 스케줄링 도메인의 기본 타입들 정의
"""
from enum import Enum
from typing import Dict, Any, List
from datetime import datetime


class ShiftType(Enum):
    """근무 타입 정의"""
    DAY = 0
    EVENING = 1
    NIGHT = 2
    OFF = 3


class ConstraintType(Enum):
    """제약조건 타입 정의"""
    HARD = "hard"
    SOFT = "soft"


class NeighborhoodType(Enum):
    """최적화 이웃 탐색 타입 정의"""
    SINGLE_SWAP = "single_swap"
    SHIFT_ROTATION = "shift_rotation"
    BLOCK_MOVE = "block_move"
    EMPLOYEE_SWAP = "employee_swap"


class OptimizationPhase(Enum):
    """최적화 단계 정의"""
    CSP_INITIAL = "CSP_Initial"
    ENHANCED_SA = "Enhanced_SA"
    TABU_SEARCH = "Tabu_Search"
    MULTI_NEIGHBORHOOD_LS = "Multi_Neighborhood_LS"


class SchedulingParams:
    """스케줄링 알고리즘 파라미터"""

    def __init__(self):
        # Enhanced 알고리즘 파라미터
        self.initial_temp = 1000.0
        self.final_temp = 0.01
        self.cooling_rate = 0.985  # 더 느린 냉각
        self.max_iterations = 5000  # 더 많은 반복
        self.reheat_threshold = 100  # 재가열 임계값
        self.reheat_factor = 2.0    # 재가열 배수

        # Tabu Search 파라미터
        self.tabu_tenure = 7
        self.tabu_max_iterations = 1000
        self.diversification_threshold = 50

        # Multi-neighborhood 파라미터
        self.local_search_iterations = 500
        self.neighborhood_weights = {
            NeighborhoodType.SINGLE_SWAP: 0.3,
            NeighborhoodType.SHIFT_ROTATION: 0.25,
            NeighborhoodType.BLOCK_MOVE: 0.25,
            NeighborhoodType.EMPLOYEE_SWAP: 0.2
        }

        # 제약조건 가중치
        self.constraint_weights = {
            'min_nurses_per_shift': 100.0,
            'max_consecutive_days': 50.0,
            'rest_after_night': 75.0,
            'weekend_coverage': 30.0,
            'skill_distribution': 25.0,
            'shift_preference': 10.0,
            'work_life_balance': 15.0
        }


class ScheduleResult:
    """스케줄링 결과를 담는 클래스"""

    def __init__(self, schedule: Dict[int, Dict[int, str]],
                 constraint_report: Dict[str, Any],
                 optimization_details: Dict[str, Any]):
        self.schedule = schedule
        self.constraint_report = constraint_report
        self.optimization_details = optimization_details
        self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return {
            'schedule': self.schedule,
            'constraint_report': self.constraint_report,
            'optimization_details': self.optimization_details,
            'created_at': self.created_at.isoformat()
        }