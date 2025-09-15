"""
스케줄링 알고리즘 모듈
SOLID 원칙에 따라 기능별로 분리된 스케줄링 컴포넌트들
"""

from .entities import (
    ShiftType,
    ConstraintType,
    NeighborhoodType,
    OptimizationPhase,
    SchedulingParams,
    ScheduleResult
)

from .constraint_processor import ConstraintProcessor
from .fitness_calculator import FitnessCalculator
from .main_scheduler import EnhancedNurseScheduler
from .optimizers.simulated_annealing import SimulatedAnnealingOptimizer

# 하위 호환성을 위한 별칭 (기존 코드가 NurseScheduler를 사용할 경우)
NurseScheduler = EnhancedNurseScheduler

__all__ = [
    'ShiftType',
    'ConstraintType',
    'NeighborhoodType',
    'OptimizationPhase',
    'SchedulingParams',
    'ScheduleResult',
    'ConstraintProcessor',
    'FitnessCalculator',
    'EnhancedNurseScheduler',
    'NurseScheduler',  # 하위 호환성
    'SimulatedAnnealingOptimizer'
]