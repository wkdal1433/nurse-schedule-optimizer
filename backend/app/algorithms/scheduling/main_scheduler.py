"""
메인 스케줄러
Single Responsibility: 분리된 컴포넌트들을 조합하여 전체 최적화 프로세스 오케스트레이션
Open/Closed Principle: 새로운 최적화 알고리즘 추가 시 확장 가능
"""
import copy
from typing import Dict, Any, List
from datetime import datetime
import calendar

from .entities import SchedulingParams, ScheduleResult, OptimizationPhase
from .constraint_processor import ConstraintProcessor
from .fitness_calculator import FitnessCalculator
from .optimizers.simulated_annealing import SimulatedAnnealingOptimizer


class EnhancedNurseScheduler:
    """
    개선된 간호사 스케줄러
    SOLID 원칙을 적용하여 각 컴포넌트를 분리하고 조합
    """

    def __init__(self, ward_id: int, month: int, year: int):
        self.ward_id = ward_id
        self.month = month
        self.year = year
        self.days_in_month = calendar.monthrange(year, month)[1]

        # 분리된 컴포넌트들 초기화
        self.params = SchedulingParams()
        self.constraint_processor = ConstraintProcessor()
        self.fitness_calculator = FitnessCalculator(self.params)

        # 최적화 알고리즘들 (Strategy Pattern 적용 가능)
        self.sa_optimizer = SimulatedAnnealingOptimizer(self.params)

        # 근무 유형
        self.shift_types = ["day", "evening", "night", "off"]

    def generate_optimized_schedule(self, employees: List[Dict],
                                  constraints: Dict[str, Any],
                                  shift_requests: Dict[int, Dict[int, str]] = None) -> ScheduleResult:
        """
        최적화된 스케줄 생성
        Template Method Pattern을 사용하여 최적화 프로세스 정의
        """
        print(f"🚀 Starting Enhanced Nurse Scheduling for Ward {self.ward_id}")
        print(f"📅 Period: {self.year}-{self.month:02d} ({self.days_in_month} days)")
        print(f"👥 Employees: {len(employees)}")

        # 1. 제약조건 전처리
        processed_constraints = self.constraint_processor.preprocess_constraints(
            constraints, employees
        )
        print("✅ Constraints preprocessed")

        # 2. 초기 해 생성
        initial_schedule = self._generate_initial_schedule(employees, processed_constraints)
        initial_score = self.fitness_calculator.calculate_fitness(
            initial_schedule, employees, processed_constraints, shift_requests
        )
        print(f"✅ Initial schedule generated with score: {initial_score:.2f}")

        # 3. 최적화 실행 (여러 단계)
        optimization_history = []
        current_schedule = initial_schedule

        # Phase 1: Simulated Annealing
        current_schedule = self._run_optimization_phase(
            OptimizationPhase.ENHANCED_SA,
            current_schedule,
            employees,
            processed_constraints,
            shift_requests,
            optimization_history
        )

        # Phase 2: Tabu Search (향후 추가 예정)
        # current_schedule = self._run_optimization_phase(
        #     OptimizationPhase.TABU_SEARCH,
        #     current_schedule,
        #     employees,
        #     processed_constraints,
        #     shift_requests,
        #     optimization_history
        # )

        # 4. 최종 검증
        final_score = self.fitness_calculator.calculate_fitness(
            current_schedule, employees, processed_constraints, shift_requests
        )

        # 5. 제약조건 검증 보고서 생성
        constraint_report = self.constraint_processor.validate_constraints(
            current_schedule, employees, processed_constraints
        )

        # 6. 결과 생성
        result = ScheduleResult(
            schedule=self._format_schedule(current_schedule, employees),
            constraint_report=constraint_report,
            optimization_details={
                'algorithm_phases': [phase.value for phase in optimization_history],
                'final_score': final_score,
                'constraint_violations': constraint_report.get('total_score', 0),
                'optimization_time': datetime.now().isoformat()
            }
        )

        print(f"✅ Final optimization completed with score: {final_score:.2f}")
        return result

    def _generate_initial_schedule(self, employees: List[Dict],
                                 constraints: Dict[str, Any]) -> Dict[int, Dict[int, str]]:
        """
        초기 스케줄 생성
        향후 CSP 기반 알고리즘으로 개선 예정
        """
        schedule = {}
        employee_ids = [emp['id'] for emp in employees]
        min_nurses_per_shift = constraints.get('min_nurses_per_shift', 3)

        print("🎲 Generating initial schedule using greedy approach...")

        for day in range(1, self.days_in_month + 1):
            schedule[day] = {}

            # 각 교대별로 최소 인원 배치
            available_employees = employee_ids.copy()

            for shift_type in ['day', 'evening', 'night']:
                shift_employees = available_employees[:min_nurses_per_shift]
                for emp_id in shift_employees:
                    schedule[day][emp_id] = shift_type
                available_employees = available_employees[min_nurses_per_shift:]

            # 나머지 직원들은 휴무
            for emp_id in available_employees:
                schedule[day][emp_id] = 'off'

            # 일부 직원들 섞기 (다양성 확보)
            if day > 1:
                self._randomize_assignments(schedule[day], min_nurses_per_shift)

        return schedule

    def _randomize_assignments(self, day_schedule: Dict[int, str], min_nurses: int):
        """일일 스케줄의 일부를 무작위로 조정"""
        import random

        nurses_by_shift = {'day': [], 'evening': [], 'night': [], 'off': []}
        for nurse_id, shift in day_schedule.items():
            nurses_by_shift[shift].append(nurse_id)

        # 각 교대에서 1명씩 선택하여 순환
        if all(len(nurses) >= 1 for nurses in [nurses_by_shift['day'],
                                              nurses_by_shift['evening'],
                                              nurses_by_shift['night']]):

            shifts = ['day', 'evening', 'night']
            selected_nurses = []
            for shift in shifts:
                if nurses_by_shift[shift]:
                    selected_nurses.append(random.choice(nurses_by_shift[shift]))

            # 순환 교대
            if len(selected_nurses) == 3:
                rotated_shifts = [shifts[-1]] + shifts[:-1]
                for i, nurse_id in enumerate(selected_nurses):
                    day_schedule[nurse_id] = rotated_shifts[i]

    def _run_optimization_phase(self, phase: OptimizationPhase,
                               schedule: Dict[int, Dict[int, str]],
                               employees: List[Dict],
                               constraints: Dict[str, Any],
                               shift_requests: Dict[int, Dict[int, str]],
                               history: List[OptimizationPhase]) -> Dict[int, Dict[int, str]]:
        """최적화 단계 실행"""

        print(f"🔄 Running optimization phase: {phase.value}")

        if phase == OptimizationPhase.ENHANCED_SA:
            optimized_schedule = self.sa_optimizer.optimize(
                schedule, employees, constraints, shift_requests
            )
        else:
            # 다른 알고리즘들은 향후 추가
            print(f"⚠️ Optimization phase {phase.value} not implemented yet")
            optimized_schedule = schedule

        # 점수 계산 및 보고
        score = self.fitness_calculator.calculate_fitness(
            optimized_schedule, employees, constraints, shift_requests
        )
        print(f"✅ {phase.value} completed with score: {score:.2f}")

        history.append(phase)
        return optimized_schedule

    def _format_schedule(self, schedule: Dict[int, Dict[int, str]],
                        employees: List[Dict]) -> Dict[str, Any]:
        """스케줄을 최종 형태로 포맷팅"""

        # 직원 정보 매핑
        employee_map = {emp['id']: emp for emp in employees}

        formatted_schedule = {}
        employee_summaries = {}

        # 일별 스케줄 포맷팅
        for day, day_schedule in schedule.items():
            date_str = f"{self.year}-{self.month:02d}-{day:02d}"
            formatted_schedule[date_str] = {}

            for nurse_id, shift in day_schedule.items():
                nurse_info = employee_map.get(nurse_id, {})
                formatted_schedule[date_str][str(nurse_id)] = {
                    'shift': shift,
                    'nurse_name': nurse_info.get('name', f'Nurse_{nurse_id}'),
                    'nurse_role': nurse_info.get('role', 'staff_nurse'),
                    'experience_level': nurse_info.get('experience_level', 1)
                }

        # 직원별 요약 통계
        for emp in employees:
            emp_id = emp['id']
            work_days = sum(1 for day_sched in schedule.values()
                          if day_sched.get(emp_id) != 'off')

            shift_counts = {'day': 0, 'evening': 0, 'night': 0, 'off': 0}
            for day_sched in schedule.values():
                shift = day_sched.get(emp_id, 'off')
                shift_counts[shift] += 1

            employee_summaries[str(emp_id)] = {
                'name': emp.get('name', f'Nurse_{emp_id}'),
                'total_work_days': work_days,
                'shift_distribution': shift_counts,
                'workload_percentage': round((work_days / self.days_in_month) * 100, 1)
            }

        return {
            'ward_id': self.ward_id,
            'period': f"{self.year}-{self.month:02d}",
            'days_in_month': self.days_in_month,
            'daily_schedules': formatted_schedule,
            'employee_summaries': employee_summaries,
            'generated_at': datetime.now().isoformat()
        }

    def get_days_in_month(self, year: int, month: int) -> int:
        """월의 일수 계산"""
        return calendar.monthrange(year, month)[1]

    def add_optimizer(self, phase: OptimizationPhase, optimizer):
        """새로운 최적화 알고리즘 추가 (Open/Closed Principle)"""
        # 향후 다른 최적화 알고리즘 추가 시 사용
        pass