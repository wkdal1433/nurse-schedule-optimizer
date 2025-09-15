"""
Simulated Annealing 최적화 알고리즘
Single Responsibility: SA 알고리즘 구현만 담당
"""
import random
import math
import copy
from typing import Dict, Any, List

from ..entities import SchedulingParams
from ..fitness_calculator import FitnessCalculator


class SimulatedAnnealingOptimizer:
    """Enhanced Simulated Annealing 최적화기"""

    def __init__(self, params: SchedulingParams = None):
        self.params = params or SchedulingParams()
        self.fitness_calculator = FitnessCalculator(self.params)

        # SA 특화 파라미터
        self.current_temp = self.params.initial_temp
        self.reheat_count = 0
        self.stagnation_counter = 0
        self.best_score_history = []

    def optimize(self, initial_schedule: Dict[int, Dict[int, str]],
                employees: List[Dict],
                constraints: Dict[str, Any],
                shift_requests: Dict[int, Dict[int, str]] = None) -> Dict[int, Dict[int, str]]:
        """Enhanced Simulated Annealing 최적화 실행"""

        current_schedule = copy.deepcopy(initial_schedule)
        best_schedule = copy.deepcopy(current_schedule)

        current_score = self.fitness_calculator.calculate_fitness(
            current_schedule, employees, constraints, shift_requests
        )
        best_score = current_score

        self.current_temp = self.params.initial_temp
        iteration = 0

        print(f"🔥 Starting Enhanced SA with initial score: {current_score:.2f}")

        while (self.current_temp > self.params.final_temp and
               iteration < self.params.max_iterations):

            # 이웃 해 생성
            neighbor_schedule = self._generate_neighbor(current_schedule, employees)
            neighbor_score = self.fitness_calculator.calculate_fitness(
                neighbor_schedule, employees, constraints, shift_requests
            )

            # 수용 여부 결정
            if self._should_accept(current_score, neighbor_score):
                current_schedule = neighbor_schedule
                current_score = neighbor_score

                # 최상 해 업데이트
                if neighbor_score > best_score:
                    best_schedule = copy.deepcopy(neighbor_schedule)
                    best_score = neighbor_score
                    self.stagnation_counter = 0
                    print(f"🎯 New best score: {best_score:.2f} at iteration {iteration}")
                else:
                    self.stagnation_counter += 1
            else:
                self.stagnation_counter += 1

            # 재가열 메커니즘
            if (self.stagnation_counter >= self.params.reheat_threshold and
                self.reheat_count < 3):
                self._reheat()
                print(f"🔄 Reheating #{self.reheat_count} at iteration {iteration}")

            # 온도 감소
            self._cool_down()
            iteration += 1

            # 진행상황 출력
            if iteration % 500 == 0:
                print(f"SA Progress: Iteration {iteration}, Temp: {self.current_temp:.3f}, "
                      f"Current: {current_score:.2f}, Best: {best_score:.2f}")

        print(f"🏁 SA completed after {iteration} iterations")
        return best_schedule

    def _generate_neighbor(self, schedule: Dict[int, Dict[int, str]],
                          employees: List[Dict]) -> Dict[int, Dict[int, str]]:
        """이웃 해 생성 - 다양한 이웃 연산 적용"""
        neighbor = copy.deepcopy(schedule)

        # 온도에 따른 이웃 연산 선택
        if self.current_temp > self.params.initial_temp * 0.7:
            # 높은 온도: 큰 변화
            operation = random.choices(
                ['single_swap', 'shift_rotation', 'block_move'],
                weights=[0.3, 0.4, 0.3]
            )[0]
        elif self.current_temp > self.params.initial_temp * 0.3:
            # 중간 온도: 중간 변화
            operation = random.choices(
                ['single_swap', 'shift_rotation', 'employee_swap'],
                weights=[0.4, 0.4, 0.2]
            )[0]
        else:
            # 낮은 온도: 작은 변화
            operation = random.choices(
                ['single_swap', 'shift_rotation'],
                weights=[0.6, 0.4]
            )[0]

        if operation == 'single_swap':
            self._single_swap(neighbor)
        elif operation == 'shift_rotation':
            self._shift_rotation(neighbor)
        elif operation == 'block_move':
            self._block_move(neighbor)
        elif operation == 'employee_swap':
            self._employee_swap(neighbor)

        return neighbor

    def _single_swap(self, schedule: Dict[int, Dict[int, str]]):
        """단일 교대 변경"""
        days = list(schedule.keys())
        day = random.choice(days)

        if schedule[day]:
            nurse_id = random.choice(list(schedule[day].keys()))
            current_shift = schedule[day][nurse_id]

            # 다른 교대로 변경
            shift_options = ['day', 'evening', 'night', 'off']
            new_shift = random.choice([s for s in shift_options if s != current_shift])
            schedule[day][nurse_id] = new_shift

    def _shift_rotation(self, schedule: Dict[int, Dict[int, str]]):
        """교대 순환 변경"""
        days = list(schedule.keys())

        if len(days) >= 3:
            # 연속된 3일 선택
            start_day = random.choice(days[:-2])
            rotation_days = [start_day, start_day + 1, start_day + 2]

            # 해당 기간에 근무하는 간호사 선택
            common_nurses = set(schedule[rotation_days[0]].keys())
            for day in rotation_days[1:]:
                common_nurses &= set(schedule[day].keys())

            if common_nurses:
                nurse_id = random.choice(list(common_nurses))

                # 교대 순환 적용
                shifts = [schedule[day][nurse_id] for day in rotation_days]
                rotated_shifts = [shifts[-1]] + shifts[:-1]

                for i, day in enumerate(rotation_days):
                    schedule[day][nurse_id] = rotated_shifts[i]

    def _block_move(self, schedule: Dict[int, Dict[int, str]]):
        """블록 이동 (연속 근무 패턴 이동)"""
        days = sorted(schedule.keys())

        if len(days) >= 4:
            # 2-3일 블록 선택
            block_size = random.randint(2, 3)
            start_day = random.choice(days[:-block_size])
            source_days = list(range(start_day, start_day + block_size))

            # 이동할 위치 선택
            possible_targets = [d for d in days[:-block_size]
                              if d not in range(start_day - 1, start_day + block_size + 1)]

            if possible_targets:
                target_start = random.choice(possible_targets)
                target_days = list(range(target_start, target_start + block_size))

                # 공통 간호사 찾기
                common_nurses = set(schedule[source_days[0]].keys())
                for day in source_days[1:] + target_days:
                    if day in schedule:
                        common_nurses &= set(schedule[day].keys())

                if common_nurses:
                    nurse_id = random.choice(list(common_nurses))

                    # 블록 교환
                    source_pattern = [schedule[day][nurse_id] for day in source_days]
                    target_pattern = [schedule[day][nurse_id] for day in target_days]

                    for i, day in enumerate(source_days):
                        schedule[day][nurse_id] = target_pattern[i]
                    for i, day in enumerate(target_days):
                        schedule[day][nurse_id] = source_pattern[i]

    def _employee_swap(self, schedule: Dict[int, Dict[int, str]]):
        """두 간호사의 특정 기간 교대 교환"""
        days = list(schedule.keys())

        if len(days) >= 2:
            # 2-4일 기간 선택
            period_length = random.randint(2, min(4, len(days)))
            start_day = random.choice(days[:-period_length + 1])
            period_days = list(range(start_day, start_day + period_length))

            # 해당 기간의 공통 간호사들
            common_nurses = set(schedule[period_days[0]].keys())
            for day in period_days[1:]:
                common_nurses &= set(schedule[day].keys())

            if len(common_nurses) >= 2:
                nurse1, nurse2 = random.sample(list(common_nurses), 2)

                # 교대 패턴 교환
                for day in period_days:
                    schedule[day][nurse1], schedule[day][nurse2] = \
                        schedule[day][nurse2], schedule[day][nurse1]

    def _should_accept(self, current_score: float, neighbor_score: float) -> bool:
        """수용 여부 결정 (Metropolis criterion)"""
        if neighbor_score > current_score:
            return True

        if self.current_temp <= 0:
            return False

        # 온도에 따른 확률적 수용
        delta = neighbor_score - current_score
        probability = math.exp(delta / self.current_temp)
        return random.random() < probability

    def _cool_down(self):
        """온도 감소"""
        # Geometric cooling with adaptive rate
        adaptive_rate = self.params.cooling_rate

        # 정체 상태면 더 빠르게 냉각
        if self.stagnation_counter > 50:
            adaptive_rate *= 0.98

        self.current_temp *= adaptive_rate

    def _reheat(self):
        """재가열 메커니즘"""
        self.current_temp = min(
            self.params.initial_temp * self.params.reheat_factor,
            self.current_temp * 5.0
        )
        self.reheat_count += 1
        self.stagnation_counter = 0

        print(f"🔥 Reheated to temperature: {self.current_temp:.2f}")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """최적화 통계 반환"""
        return {
            'final_temperature': self.current_temp,
            'reheat_count': self.reheat_count,
            'stagnation_counter': self.stagnation_counter,
            'algorithm': 'Enhanced_Simulated_Annealing'
        }