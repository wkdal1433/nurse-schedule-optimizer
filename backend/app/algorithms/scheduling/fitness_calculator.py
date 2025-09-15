"""
Fitness 계산기
Single Responsibility: 스케줄의 품질 점수 계산만 담당
"""
import math
from typing import Dict, Any, List
from collections import defaultdict, Counter

from .entities import SchedulingParams


class FitnessCalculator:
    """스케줄 품질 점수 계산을 담당하는 클래스"""

    def __init__(self, params: SchedulingParams = None):
        self.params = params or SchedulingParams()

    def calculate_fitness(self, schedule: Dict[int, Dict[int, str]],
                         employees: List[Dict],
                         constraints: Dict[str, Any],
                         shift_requests: Dict[int, Dict[int, str]] = None) -> float:
        """전체 fitness 점수 계산"""
        total_score = 0.0

        # 1. 하드 제약조건 점수
        hard_score = self._calculate_hard_constraint_score(
            schedule, employees, constraints
        )
        total_score += hard_score

        # 2. 소프트 제약조건 점수
        soft_score = self._calculate_soft_constraint_score(
            schedule, employees, constraints
        )
        total_score += soft_score

        # 3. 선호도 점수
        if shift_requests:
            preference_score = self._calculate_preference_score(schedule, shift_requests)
            total_score += preference_score

        # 4. 균형 점수 (공정성)
        balance_score = self._calculate_balance_score(schedule, employees)
        total_score += balance_score

        # 5. 품질 보너스
        quality_bonus = self._calculate_quality_bonus(schedule, employees, constraints)
        total_score += quality_bonus

        return total_score

    def _calculate_hard_constraint_score(self, schedule: Dict[int, Dict[int, str]],
                                       employees: List[Dict],
                                       constraints: Dict[str, Any]) -> float:
        """하드 제약조건 점수 계산 (위반 시 큰 페널티)"""
        penalty = 0.0

        # 최소 간호사 수 제약조건
        penalty += self._check_min_nurses_penalty(
            schedule, constraints.get('min_nurses_per_shift', 3)
        )

        # 야간 후 휴식 제약조건
        penalty += self._check_rest_after_night_penalty(schedule)

        # 최대 연속 근무일 제약조건
        penalty += self._check_max_consecutive_penalty(
            schedule, constraints.get('max_consecutive_days', 5)
        )

        # 주말 최소 커버리지
        penalty += self._check_weekend_coverage_penalty(schedule, constraints)

        # 스킬 분포 제약조건
        penalty += self._check_skill_distribution_penalty(schedule, employees)

        return -penalty  # 페널티를 음수로 반환

    def _calculate_soft_constraint_score(self, schedule: Dict[int, Dict[int, str]],
                                       employees: List[Dict],
                                       constraints: Dict[str, Any]) -> float:
        """소프트 제약조건 점수 계산"""
        score = 0.0

        # 근무 시간 균등 분배
        score += self._calculate_workload_balance_score(schedule)

        # 주말 근무 공정성
        score += self._calculate_weekend_fairness_score(schedule)

        # 야간 근무 분배
        score += self._calculate_night_shift_distribution_score(schedule)

        # 휴일 분배
        score += self._calculate_rest_day_distribution_score(schedule)

        return score

    def _calculate_preference_score(self, schedule: Dict[int, Dict[int, str]],
                                  shift_requests: Dict[int, Dict[int, str]]) -> float:
        """선호도 만족 점수 계산"""
        score = 0.0
        total_requests = 0
        satisfied_requests = 0

        for day, day_schedule in schedule.items():
            if day in shift_requests:
                for nurse_id, assigned_shift in day_schedule.items():
                    if nurse_id in shift_requests[day]:
                        total_requests += 1
                        requested_shift = shift_requests[day][nurse_id]

                        if assigned_shift == requested_shift:
                            satisfied_requests += 1
                            score += self.params.constraint_weights['shift_preference']
                        elif (requested_shift == 'off' and assigned_shift != 'off') or \
                             (requested_shift != 'off' and assigned_shift == 'off'):
                            # 정반대 할당은 더 큰 페널티
                            score -= self.params.constraint_weights['shift_preference'] * 2

        # 선호도 만족률 보너스
        if total_requests > 0:
            satisfaction_rate = satisfied_requests / total_requests
            score += satisfaction_rate * 50  # 보너스 점수

        return score

    def _calculate_balance_score(self, schedule: Dict[int, Dict[int, str]],
                               employees: List[Dict]) -> float:
        """근무 균형 점수 계산"""
        score = 0.0

        # 간호사별 근무 시간 계산
        nurse_workload = defaultdict(int)
        nurse_shift_counts = defaultdict(lambda: defaultdict(int))

        for day_schedule in schedule.values():
            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    nurse_workload[nurse_id] += 1
                    nurse_shift_counts[nurse_id][shift] += 1

        # 근무량 표준편차 계산 (낮을수록 좋음)
        workloads = list(nurse_workload.values())
        if workloads:
            mean_workload = sum(workloads) / len(workloads)
            variance = sum((w - mean_workload) ** 2 for w in workloads) / len(workloads)
            std_dev = math.sqrt(variance)
            score -= std_dev * 5  # 표준편차가 클수록 페널티

        # 교대별 균등 분배
        for nurse_id, shift_counts in nurse_shift_counts.items():
            total_shifts = sum(shift_counts.values())
            if total_shifts > 0:
                # 각 교대의 비율 계산
                for shift_type in ['day', 'evening', 'night']:
                    ratio = shift_counts[shift_type] / total_shifts
                    # 특정 교대에 너무 집중되지 않도록
                    if ratio > 0.7:  # 70% 이상
                        score -= (ratio - 0.7) * 30

        return score

    def _calculate_quality_bonus(self, schedule: Dict[int, Dict[int, str]],
                               employees: List[Dict],
                               constraints: Dict[str, Any]) -> float:
        """고품질 스케줄에 대한 보너스 점수"""
        bonus = 0.0

        # 경험자와 신입 적절한 배치 보너스
        bonus += self._calculate_experience_mix_bonus(schedule, employees)

        # 연속성 보너스 (적당한 연속 근무)
        bonus += self._calculate_continuity_bonus(schedule)

        # 커버리지 완성도 보너스
        bonus += self._calculate_coverage_completeness_bonus(schedule, constraints)

        return bonus

    def _check_min_nurses_penalty(self, schedule: Dict[int, Dict[int, str]],
                                min_nurses: int) -> float:
        """최소 간호사 수 위반 페널티"""
        penalty = 0.0

        for day, day_schedule in schedule.items():
            shift_counts = defaultdict(int)
            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    shift_counts[shift] += 1

            for shift_type in ['day', 'evening', 'night']:
                shortage = max(0, min_nurses - shift_counts[shift_type])
                if shortage > 0:
                    penalty += shortage * self.params.constraint_weights['min_nurses_per_shift']

        return penalty

    def _check_rest_after_night_penalty(self, schedule: Dict[int, Dict[int, str]]) -> float:
        """야간 후 휴식 위반 페널티"""
        penalty = 0.0
        days = sorted(schedule.keys())

        for i in range(len(days) - 1):
            current_day = days[i]
            next_day = days[i + 1]

            for nurse_id in schedule[current_day]:
                if (schedule[current_day][nurse_id] == 'night' and
                    schedule[next_day].get(nurse_id) != 'off'):
                    penalty += self.params.constraint_weights['rest_after_night']

        return penalty

    def _check_max_consecutive_penalty(self, schedule: Dict[int, Dict[int, str]],
                                     max_days: int) -> float:
        """최대 연속 근무일 위반 페널티"""
        penalty = 0.0
        days = sorted(schedule.keys())

        nurse_consecutive = defaultdict(int)
        for day in days:
            for nurse_id, shift in schedule[day].items():
                if shift != 'off':
                    nurse_consecutive[nurse_id] += 1
                    if nurse_consecutive[nurse_id] > max_days:
                        excess_days = nurse_consecutive[nurse_id] - max_days
                        penalty += excess_days * self.params.constraint_weights['max_consecutive_days']
                else:
                    nurse_consecutive[nurse_id] = 0

        return penalty

    def _check_weekend_coverage_penalty(self, schedule: Dict[int, Dict[int, str]],
                                      constraints: Dict[str, Any]) -> float:
        """주말 커버리지 부족 페널티"""
        penalty = 0.0
        days = sorted(schedule.keys())

        # 주말 (토요일=5, 일요일=6)로 가정
        weekend_days = [day for day in days if day % 7 in [5, 6]]

        min_weekend_nurses = constraints.get('min_weekend_nurses', 2)

        for day in weekend_days:
            day_schedule = schedule[day]
            working_nurses = sum(1 for shift in day_schedule.values() if shift != 'off')

            if working_nurses < min_weekend_nurses:
                shortage = min_weekend_nurses - working_nurses
                penalty += shortage * self.params.constraint_weights['weekend_coverage']

        return penalty

    def _check_skill_distribution_penalty(self, schedule: Dict[int, Dict[int, str]],
                                        employees: List[Dict]) -> float:
        """스킬 분포 부적절 페널티"""
        penalty = 0.0

        # 경험 수준 매핑
        experience_map = {}
        for emp in employees:
            experience_map[emp['id']] = emp.get('experience_level', 1)

        for day, day_schedule in schedule.items():
            shift_experience = defaultdict(list)

            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    exp_level = experience_map.get(nurse_id, 1)
                    shift_experience[shift].append(exp_level)

            # 각 교대별 경험 분포 검사
            for shift_type, experiences in shift_experience.items():
                if len(experiences) >= 3:  # 3명 이상일 때만 검사
                    senior_count = sum(1 for exp in experiences if exp >= 5)
                    if senior_count == 0:
                        penalty += self.params.constraint_weights['skill_distribution']

        return penalty

    def _calculate_workload_balance_score(self, schedule: Dict[int, Dict[int, str]]) -> float:
        """근무량 균형 점수"""
        nurse_workdays = defaultdict(int)

        for day_schedule in schedule.values():
            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    nurse_workdays[nurse_id] += 1

        if not nurse_workdays:
            return 0.0

        workdays = list(nurse_workdays.values())
        mean_workdays = sum(workdays) / len(workdays)
        variance = sum((w - mean_workdays) ** 2 for w in workdays) / len(workdays)

        # 분산이 작을수록 높은 점수
        balance_score = max(0, 50 - variance)
        return balance_score

    def _calculate_weekend_fairness_score(self, schedule: Dict[int, Dict[int, str]]) -> float:
        """주말 근무 공정성 점수"""
        days = sorted(schedule.keys())
        weekend_days = [day for day in days if day % 7 in [5, 6]]

        nurse_weekend_count = defaultdict(int)

        for day in weekend_days:
            for nurse_id, shift in schedule[day].items():
                if shift != 'off':
                    nurse_weekend_count[nurse_id] += 1

        if not nurse_weekend_count:
            return 0.0

        weekend_counts = list(nurse_weekend_count.values())
        mean_weekend = sum(weekend_counts) / len(weekend_counts)
        variance = sum((w - mean_weekend) ** 2 for w in weekend_counts) / len(weekend_counts)

        fairness_score = max(0, 30 - variance * 2)
        return fairness_score

    def _calculate_night_shift_distribution_score(self, schedule: Dict[int, Dict[int, str]]) -> float:
        """야간 근무 분배 점수"""
        nurse_night_count = defaultdict(int)

        for day_schedule in schedule.values():
            for nurse_id, shift in day_schedule.items():
                if shift == 'night':
                    nurse_night_count[nurse_id] += 1

        if not nurse_night_count:
            return 0.0

        night_counts = list(nurse_night_count.values())
        mean_nights = sum(night_counts) / len(night_counts)
        variance = sum((n - mean_nights) ** 2 for n in night_counts) / len(night_counts)

        distribution_score = max(0, 25 - variance)
        return distribution_score

    def _calculate_rest_day_distribution_score(self, schedule: Dict[int, Dict[int, str]]) -> float:
        """휴무일 분배 점수"""
        nurse_rest_count = defaultdict(int)

        for day_schedule in schedule.values():
            for nurse_id, shift in day_schedule.items():
                if shift == 'off':
                    nurse_rest_count[nurse_id] += 1

        if not nurse_rest_count:
            return 0.0

        rest_counts = list(nurse_rest_count.values())
        mean_rest = sum(rest_counts) / len(rest_counts)
        variance = sum((r - mean_rest) ** 2 for r in rest_counts) / len(rest_counts)

        rest_score = max(0, 20 - variance)
        return rest_score

    def _calculate_experience_mix_bonus(self, schedule: Dict[int, Dict[int, str]],
                                      employees: List[Dict]) -> float:
        """경험자-신입 적절한 혼합 보너스"""
        bonus = 0.0

        experience_map = {}
        for emp in employees:
            experience_map[emp['id']] = emp.get('experience_level', 1)

        for day_schedule in schedule.values():
            shift_experience = defaultdict(list)

            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    exp_level = experience_map.get(nurse_id, 1)
                    shift_experience[shift].append(exp_level)

            # 각 교대별로 적절한 경험 혼합 보너스
            for shift_type, experiences in shift_experience.items():
                if len(experiences) >= 2:
                    senior_count = sum(1 for exp in experiences if exp >= 5)
                    junior_count = sum(1 for exp in experiences if exp <= 2)

                    # 시니어와 주니어가 적절히 섞여있으면 보너스
                    if senior_count >= 1 and junior_count >= 1:
                        bonus += 5

        return bonus

    def _calculate_continuity_bonus(self, schedule: Dict[int, Dict[int, str]]) -> float:
        """적당한 연속 근무 보너스"""
        bonus = 0.0
        days = sorted(schedule.keys())

        nurse_consecutive = defaultdict(int)
        for day in days:
            for nurse_id, shift in schedule[day].items():
                if shift != 'off':
                    nurse_consecutive[nurse_id] += 1
                else:
                    consecutive_days = nurse_consecutive[nurse_id]
                    # 2-4일 연속 근무는 좋음
                    if 2 <= consecutive_days <= 4:
                        bonus += consecutive_days * 2
                    nurse_consecutive[nurse_id] = 0

        return bonus

    def _calculate_coverage_completeness_bonus(self, schedule: Dict[int, Dict[int, str]],
                                             constraints: Dict[str, Any]) -> float:
        """커버리지 완성도 보너스"""
        bonus = 0.0
        min_nurses = constraints.get('min_nurses_per_shift', 3)

        total_coverage_score = 0
        total_shifts = 0

        for day_schedule in schedule.values():
            shift_counts = defaultdict(int)
            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    shift_counts[shift] += 1

            for shift_type in ['day', 'evening', 'night']:
                coverage_ratio = min(1.0, shift_counts[shift_type] / min_nurses)
                total_coverage_score += coverage_ratio
                total_shifts += 1

        if total_shifts > 0:
            average_coverage = total_coverage_score / total_shifts
            # 높은 커버리지 달성 시 보너스
            if average_coverage >= 0.95:
                bonus += 50
            elif average_coverage >= 0.90:
                bonus += 30

        return bonus