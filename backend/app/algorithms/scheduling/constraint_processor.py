"""
제약조건 처리기
Single Responsibility: 제약조건 전처리, 분석, 검증만 담당
"""
import copy
from typing import Dict, Any, List
from collections import defaultdict

from .entities import ConstraintType


class ConstraintProcessor:
    """제약조건 전처리 및 분석을 담당하는 클래스"""

    def __init__(self):
        self.constraint_weights = {
            'min_nurses_per_shift': 100.0,
            'max_consecutive_days': 50.0,
            'rest_after_night': 75.0,
            'weekend_coverage': 30.0,
            'skill_distribution': 25.0,
            'shift_preference': 10.0,
            'work_life_balance': 15.0
        }

    def preprocess_constraints(self, constraints: Dict[str, Any],
                               employees: List[Dict]) -> Dict[str, Any]:
        """제약조건 전처리 및 분석"""
        processed = copy.deepcopy(constraints)

        # 직원별 역할 및 고용형태 분석
        processed['employee_roles'] = {}
        processed['employment_types'] = {}
        processed['experience_levels'] = {}

        for emp in employees:
            emp_id = emp['id']
            processed['employee_roles'][emp_id] = emp.get('role', 'staff_nurse')
            processed['employment_types'][emp_id] = emp.get('employment_type', 'full_time')
            processed['experience_levels'][emp_id] = emp.get('experience_level', 1)

        # 역할별 직원 수 계산
        role_counts = defaultdict(int)
        for role in processed['employee_roles'].values():
            role_counts[role] += 1
        processed['role_distribution'] = dict(role_counts)

        # 경험 수준별 분포
        exp_distribution = defaultdict(int)
        for exp in processed['experience_levels'].values():
            exp_level = self._categorize_experience(exp)
            exp_distribution[exp_level] += 1
        processed['experience_distribution'] = dict(exp_distribution)

        # 제약조건 우선순위 설정
        processed['constraint_priorities'] = self._set_constraint_priorities(processed)

        # 하드/소프트 제약조건 분류
        processed['hard_constraints'] = self._extract_hard_constraints(processed)
        processed['soft_constraints'] = self._extract_soft_constraints(processed)

        return processed

    def validate_constraints(self, schedule: Dict[int, Dict[int, str]],
                           employees: List[Dict],
                           constraints: Dict[str, Any]) -> Dict[str, Any]:
        """제약조건 위반 검증"""
        violations = {}

        # 하드 제약조건 검증
        hard_violations = self._check_hard_constraints(schedule, employees, constraints)
        violations['hard'] = hard_violations

        # 소프트 제약조건 검증
        soft_violations = self._check_soft_constraints(schedule, employees, constraints)
        violations['soft'] = soft_violations

        # 총 위반 점수 계산
        violations['total_score'] = self._calculate_violation_score(
            hard_violations, soft_violations
        )

        return violations

    def _categorize_experience(self, years: int) -> str:
        """경험 연수를 범주로 분류"""
        if years <= 1:
            return 'junior'
        elif years <= 3:
            return 'intermediate'
        elif years <= 7:
            return 'senior'
        else:
            return 'expert'

    def _set_constraint_priorities(self, constraints: Dict[str, Any]) -> Dict[str, int]:
        """제약조건 우선순위 설정"""
        priorities = {
            'min_nurses_per_shift': 1,  # 최우선
            'rest_after_night': 2,
            'max_consecutive_days': 3,
            'skill_distribution': 4,
            'weekend_coverage': 5,
            'shift_preference': 6,
            'work_life_balance': 7
        }
        return priorities

    def _extract_hard_constraints(self, constraints: Dict[str, Any]) -> List[str]:
        """하드 제약조건 추출"""
        hard_constraints = [
            'min_nurses_per_shift',
            'rest_after_night',
            'max_consecutive_days'
        ]

        # 추가 하드 제약조건이 있다면 포함
        if constraints.get('mandatory_rest_days'):
            hard_constraints.append('mandatory_rest_days')

        return hard_constraints

    def _extract_soft_constraints(self, constraints: Dict[str, Any]) -> List[str]:
        """소프트 제약조건 추출"""
        soft_constraints = [
            'shift_preference',
            'weekend_coverage',
            'skill_distribution',
            'work_life_balance'
        ]
        return soft_constraints

    def _check_hard_constraints(self, schedule: Dict[int, Dict[int, str]],
                              employees: List[Dict],
                              constraints: Dict[str, Any]) -> Dict[str, List[str]]:
        """하드 제약조건 위반 검사"""
        violations = {}

        # 최소 간호사 수 제약조건 검사
        min_nurse_violations = self._check_min_nurses_per_shift(
            schedule, constraints.get('min_nurses_per_shift', 3)
        )
        if min_nurse_violations:
            violations['min_nurses_per_shift'] = min_nurse_violations

        # 야간 후 휴식 제약조건 검사
        rest_violations = self._check_rest_after_night(schedule)
        if rest_violations:
            violations['rest_after_night'] = rest_violations

        # 연속 근무일 제약조건 검사
        consecutive_violations = self._check_max_consecutive_days(
            schedule, constraints.get('max_consecutive_days', 5)
        )
        if consecutive_violations:
            violations['max_consecutive_days'] = consecutive_violations

        return violations

    def _check_soft_constraints(self, schedule: Dict[int, Dict[int, str]],
                              employees: List[Dict],
                              constraints: Dict[str, Any]) -> Dict[str, List[str]]:
        """소프트 제약조건 위반 검사"""
        violations = {}

        # 선호도 제약조건 검사
        preference_violations = self._check_shift_preferences(
            schedule, constraints.get('shift_preferences', {})
        )
        if preference_violations:
            violations['shift_preference'] = preference_violations

        # 스킬 분포 제약조건 검사
        skill_violations = self._check_skill_distribution(schedule, employees)
        if skill_violations:
            violations['skill_distribution'] = skill_violations

        return violations

    def _check_min_nurses_per_shift(self, schedule: Dict[int, Dict[int, str]],
                                   min_nurses: int) -> List[str]:
        """교대별 최소 간호사 수 검사"""
        violations = []

        for day in schedule:
            day_schedule = schedule[day]
            shift_counts = defaultdict(int)

            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    shift_counts[shift] += 1

            for shift_type in ['day', 'evening', 'night']:
                if shift_counts[shift_type] < min_nurses:
                    violations.append(
                        f"Day {day}, {shift_type} shift: {shift_counts[shift_type]} nurses "
                        f"(minimum required: {min_nurses})"
                    )

        return violations

    def _check_rest_after_night(self, schedule: Dict[int, Dict[int, str]]) -> List[str]:
        """야간 근무 후 휴식 제약조건 검사"""
        violations = []
        days = sorted(schedule.keys())

        for i in range(len(days) - 1):
            current_day = days[i]
            next_day = days[i + 1]

            for nurse_id in schedule[current_day]:
                if (schedule[current_day][nurse_id] == 'night' and
                    schedule[next_day].get(nurse_id) != 'off'):
                    violations.append(
                        f"Nurse {nurse_id}: no rest after night shift on day {current_day}"
                    )

        return violations

    def _check_max_consecutive_days(self, schedule: Dict[int, Dict[int, str]],
                                   max_days: int) -> List[str]:
        """최대 연속 근무일 제약조건 검사"""
        violations = []
        days = sorted(schedule.keys())

        # 각 간호사별로 연속 근무일 계산
        nurse_consecutive = defaultdict(int)

        for day in days:
            for nurse_id, shift in schedule[day].items():
                if shift != 'off':
                    nurse_consecutive[nurse_id] += 1
                    if nurse_consecutive[nurse_id] > max_days:
                        violations.append(
                            f"Nurse {nurse_id}: {nurse_consecutive[nurse_id]} consecutive days "
                            f"(maximum allowed: {max_days})"
                        )
                else:
                    nurse_consecutive[nurse_id] = 0

        return violations

    def _check_shift_preferences(self, schedule: Dict[int, Dict[int, str]],
                               preferences: Dict[int, List[str]]) -> List[str]:
        """근무 선호도 제약조건 검사"""
        violations = []

        for day, day_schedule in schedule.items():
            for nurse_id, shift in day_schedule.items():
                if nurse_id in preferences and shift != 'off':
                    preferred_shifts = preferences[nurse_id]
                    if shift not in preferred_shifts:
                        violations.append(
                            f"Nurse {nurse_id} on day {day}: assigned {shift} "
                            f"(prefers: {', '.join(preferred_shifts)})"
                        )

        return violations

    def _check_skill_distribution(self, schedule: Dict[int, Dict[int, str]],
                                employees: List[Dict]) -> List[str]:
        """스킬 분포 제약조건 검사"""
        violations = []

        # 경험 수준별 간호사 매핑
        experience_map = {}
        for emp in employees:
            experience_map[emp['id']] = emp.get('experience_level', 1)

        for day, day_schedule in schedule.items():
            shift_experience = defaultdict(list)

            for nurse_id, shift in day_schedule.items():
                if shift != 'off':
                    exp_level = experience_map.get(nurse_id, 1)
                    shift_experience[shift].append(exp_level)

            # 각 교대별로 경험 분포 검사
            for shift_type, experiences in shift_experience.items():
                if experiences:
                    senior_count = sum(1 for exp in experiences if exp >= 5)
                    total_count = len(experiences)

                    # 최소 1명의 시니어가 있어야 함 (3명 이상 근무 시)
                    if total_count >= 3 and senior_count == 0:
                        violations.append(
                            f"Day {day}, {shift_type} shift: no senior nurse present"
                        )

        return violations

    def _calculate_violation_score(self, hard_violations: Dict[str, List[str]],
                                 soft_violations: Dict[str, List[str]]) -> float:
        """제약조건 위반 점수 계산"""
        total_score = 0.0

        # 하드 제약조건 위반 (높은 페널티)
        for constraint_type, violations in hard_violations.items():
            weight = self.constraint_weights.get(constraint_type, 50.0)
            total_score += len(violations) * weight

        # 소프트 제약조건 위반 (낮은 페널티)
        for constraint_type, violations in soft_violations.items():
            weight = self.constraint_weights.get(constraint_type, 10.0)
            total_score += len(violations) * weight * 0.5  # 소프트 제약조건은 50% 가중치

        return total_score