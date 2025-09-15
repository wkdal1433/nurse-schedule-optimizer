"""
Domain Service: SchedulingRulesService
스케줄링 규칙 도메인 서비스 - 복잡한 비즈니스 로직
"""
from typing import List, Dict
from datetime import datetime, timedelta

from ..entities.nurse import Nurse, NurseRole
from ..value_objects.employment_type import EmploymentType


class SchedulingRulesService:
    """스케줄링 규칙 도메인 서비스"""

    def validate_minimum_staff_requirement(
        self,
        nurses: List[Nurse],
        min_nurses_per_shift: int,
        shift_types: List[str]
    ) -> Dict[str, bool]:
        """최소 인력 요구사항 검증"""
        active_nurses = [n for n in nurses if n.is_active]
        full_time_nurses = [n for n in active_nurses if n.employment_type == EmploymentType.FULL_TIME]

        # 전체 필요 인력 (교대 * 최소인원)
        total_required = min_nurses_per_shift * len(shift_types)

        # 야간 근무 가능 인력
        night_capable = [n for n in active_nurses if n.can_work_night_shift()]

        # 감독 가능 인력
        supervisors = [n for n in active_nurses if n.can_supervise()]

        return {
            "sufficient_total_staff": len(active_nurses) >= total_required,
            "sufficient_full_time": len(full_time_nurses) >= min_nurses_per_shift,
            "sufficient_night_staff": len(night_capable) >= min_nurses_per_shift,
            "sufficient_supervisors": len(supervisors) >= 1,
            "details": {
                "active_count": len(active_nurses),
                "required_count": total_required,
                "night_capable_count": len(night_capable),
                "supervisor_count": len(supervisors)
            }
        }

    def calculate_workload_distribution(self, nurses: List[Nurse]) -> Dict[int, float]:
        """간호사별 업무 부하 계산"""
        workload = {}

        for nurse in nurses:
            if not nurse.is_active:
                workload[nurse.id] = 0.0
                continue

            base_load = 1.0

            # 경력에 따른 조정
            if nurse.experience_level.years < 1:
                base_load *= 0.7  # 신입 간호사는 부하 감소
            elif nurse.experience_level.years > 10:
                base_load *= 1.2  # 베테랑은 부하 증가

            # 역할에 따른 조정
            if nurse.role == NurseRole.HEAD_NURSE:
                base_load *= 1.3  # 수간호사는 관리 업무 추가
            elif nurse.role == NurseRole.NEW_NURSE:
                base_load *= 0.6  # 신입간호사는 부하 감소

            # 고용형태에 따른 조정
            if nurse.employment_type == EmploymentType.PART_TIME:
                base_load *= 0.6  # 시간제는 부하 감소

            workload[nurse.id] = base_load

        return workload

    def check_scheduling_conflicts(
        self,
        nurse: Nurse,
        proposed_shifts: List[str],
        current_schedule: Dict[str, str]
    ) -> List[str]:
        """스케줄링 충돌 검사"""
        conflicts = []

        # 연속 근무일 검사
        consecutive_days = self._count_consecutive_work_days(
            nurse, proposed_shifts, current_schedule
        )
        max_consecutive = nurse.get_max_consecutive_work_days()

        if consecutive_days > max_consecutive:
            conflicts.append(
                f"연속 근무일 초과: {consecutive_days}일 > {max_consecutive}일"
            )

        # 야간 근무 빈도 검사
        night_shifts = [s for s in proposed_shifts if s == "NIGHT"]
        max_night_shifts = nurse.get_max_night_shifts_per_week()

        if len(night_shifts) > max_night_shifts:
            conflicts.append(
                f"주간 야간 근무 초과: {len(night_shifts)}회 > {max_night_shifts}회"
            )

        # 신입 간호사 야간 근무 검사
        if nurse.role == NurseRole.NEW_NURSE and "NIGHT" in proposed_shifts:
            if not nurse.can_work_night_shift():
                conflicts.append("신입 간호사는 야간 근무 불가")

        return conflicts

    def _count_consecutive_work_days(
        self,
        nurse: Nurse,
        proposed_shifts: List[str],
        current_schedule: Dict[str, str]
    ) -> int:
        """연속 근무일 계산"""
        # 실제 구현에서는 날짜별 스케줄을 분석하여 연속 근무일을 계산
        # 여기서는 간단히 OFF가 아닌 날들을 카운트
        consecutive = 0
        max_consecutive = 0

        for shift in proposed_shifts:
            if shift != "OFF":
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0

        return max_consecutive