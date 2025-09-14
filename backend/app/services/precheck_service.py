"""
Pre-check Service for Schedule Generation
근무표 생성 전 인원 및 제약조건 검증 서비스
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from ..models.models import Employee, Ward, ShiftRequest
from ..models.scheduling_models import Schedule


class PreCheckResult:
    """Pre-check 결과를 담는 클래스"""

    def __init__(self):
        self.is_valid = True
        self.warnings = []
        self.errors = []
        self.staff_analysis = {}
        self.recommendations = []

    def add_error(self, message: str, category: str = "general"):
        """심각한 오류 추가 (근무표 생성 차단)"""
        self.is_valid = False
        self.errors.append({
            "message": message,
            "category": category,
            "severity": "error"
        })

    def add_warning(self, message: str, category: str = "general"):
        """경고 추가 (근무표 생성 가능하지만 주의 필요)"""
        self.warnings.append({
            "message": message,
            "category": category,
            "severity": "warning"
        })

    def add_recommendation(self, message: str):
        """개선 권고사항 추가"""
        self.recommendations.append(message)

    def to_dict(self):
        """결과를 딕셔너리로 변환"""
        return {
            "is_valid": self.is_valid,
            "can_generate": self.is_valid,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "staff_analysis": self.staff_analysis,
            "recommendations": self.recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }


class SchedulePreCheckService:
    """근무표 생성 전 검증 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def perform_precheck(self, ward_id: int, year: int, month: int) -> PreCheckResult:
        """
        종합 Pre-check 수행

        Args:
            ward_id: 병동 ID
            year: 연도
            month: 월

        Returns:
            PreCheckResult: 검증 결과
        """
        result = PreCheckResult()

        # 1. 병동 정보 검증
        ward = self._validate_ward(ward_id, result)
        if not ward:
            return result

        # 2. 직원 정보 검증
        employees = self._validate_staff_availability(ward_id, result)
        if not employees:
            return result

        # 3. 최소 인원 요구사항 검증
        self._check_minimum_staff_requirements(ward, employees, result)

        # 4. 역할별 인원 분포 검증
        self._check_role_distribution(employees, result)

        # 5. 경험 수준 분포 검증
        self._check_experience_distribution(employees, result)

        # 6. 해당 기간의 휴가/요청사항 검증
        self._check_leave_requests(ward_id, year, month, employees, result)

        # 7. 기존 근무표와의 충돌 검증
        self._check_existing_schedules(ward_id, year, month, result)

        # 8. 종합 분석 및 권고사항 생성
        self._generate_recommendations(ward, employees, result)

        return result

    def _validate_ward(self, ward_id: int, result: PreCheckResult) -> Optional[Ward]:
        """병동 정보 검증"""
        ward = self.db.query(Ward).filter(Ward.id == ward_id).first()

        if not ward:
            result.add_error(f"병동 ID {ward_id}를 찾을 수 없습니다.", "ward_validation")
            return None

        if not ward.is_active:
            result.add_error(f"병동 '{ward.name}'이 비활성 상태입니다.", "ward_validation")
            return None

        # 병동 규칙 검증
        if not ward.shift_rules:
            result.add_warning(f"병동 '{ward.name}'에 근무 규칙이 설정되지 않았습니다.", "ward_config")

        return ward

    def _validate_staff_availability(self, ward_id: int, result: PreCheckResult) -> List[Employee]:
        """직원 가용성 검증"""
        employees = self.db.query(Employee).filter(
            Employee.ward_id == ward_id,
            Employee.is_active == True
        ).all()

        if not employees:
            result.add_error(f"병동에 활성화된 직원이 없습니다.", "staff_availability")
            return []

        if len(employees) < 3:
            result.add_error(
                f"최소 3명의 직원이 필요하지만 현재 {len(employees)}명만 활성화되어 있습니다.",
                "staff_availability"
            )
            return employees

        # 직원 정보 완성도 검사
        incomplete_staff = []
        for emp in employees:
            issues = []
            if not emp.skill_level:
                issues.append("숙련도")
            if emp.years_experience is None:
                issues.append("경력")
            if not emp.employment_type:
                issues.append("고용형태")

            if issues:
                incomplete_staff.append(f"{emp.employee_number}: {', '.join(issues)}")

        if incomplete_staff:
            result.add_warning(
                f"다음 직원들의 정보가 불완전합니다: {'; '.join(incomplete_staff)}",
                "staff_data"
            )

        return employees

    def _check_minimum_staff_requirements(self, ward: Ward, employees: List[Employee], result: PreCheckResult):
        """최소 인원 요구사항 검증"""
        ward_rules = ward.shift_rules or {}

        # 기본 최소 인원 요구사항
        min_day_staff = ward_rules.get("min_day_staff", 3)
        min_evening_staff = ward_rules.get("min_evening_staff", 2)
        min_night_staff = ward_rules.get("min_night_staff", 2)

        total_staff = len(employees)

        # 일일 최대 필요 인원 계산
        max_daily_required = min_day_staff + min_evening_staff + min_night_staff

        if total_staff < max_daily_required:
            result.add_error(
                f"일일 최대 필요 인원({max_daily_required}명)보다 총 직원 수({total_staff}명)가 부족합니다.",
                "minimum_staff"
            )
        elif total_staff == max_daily_required:
            result.add_warning(
                f"총 직원 수({total_staff}명)가 일일 최대 필요 인원과 동일합니다. "
                f"휴가나 병가 시 근무표 생성이 어려울 수 있습니다.",
                "minimum_staff"
            )

        # 시프트별 최소 요구사항 저장
        result.staff_analysis["shift_requirements"] = {
            "day_shift": {"required": min_day_staff, "available": total_staff},
            "evening_shift": {"required": min_evening_staff, "available": total_staff},
            "night_shift": {"required": min_night_staff, "available": total_staff},
            "total_required_per_day": max_daily_required,
            "total_available": total_staff
        }

    def _check_role_distribution(self, employees: List[Employee], result: PreCheckResult):
        """역할별 인원 분포 검증"""
        role_counts = {}
        skill_counts = {"신입": 0, "중급": 0, "고급": 0}

        for emp in employees:
            # 역할별 카운트
            role = emp.role or "일반간호사"
            role_counts[role] = role_counts.get(role, 0) + 1

            # 숙련도별 카운트
            skill = emp.skill_level or "신입"
            if skill in skill_counts:
                skill_counts[skill] += 1

        # 수간호사 검증
        if role_counts.get("수간호사", 0) == 0:
            result.add_warning("수간호사가 배정되지 않았습니다.", "role_distribution")
        elif role_counts.get("수간호사", 0) > 1:
            result.add_warning(f"수간호사가 {role_counts['수간호사']}명 배정되었습니다. 일반적으로 1명이 적절합니다.", "role_distribution")

        # 신입간호사 비율 검증
        total_nurses = len(employees)
        new_nurses = skill_counts["신입"]
        if new_nurses / total_nurses > 0.3:  # 30% 이상
            result.add_warning(
                f"신입간호사 비율이 {new_nurses/total_nurses*100:.1f}%로 높습니다. "
                f"숙련된 간호사와의 페어링이 어려울 수 있습니다.",
                "role_distribution"
            )

        # 역할 분포 정보 저장
        result.staff_analysis["role_distribution"] = {
            "by_role": role_counts,
            "by_skill": skill_counts,
            "total_count": total_nurses,
            "new_nurse_ratio": new_nurses / total_nurses if total_nurses > 0 else 0
        }

    def _check_experience_distribution(self, employees: List[Employee], result: PreCheckResult):
        """경험 수준 분포 검증"""
        experience_groups = {"0-1년": 0, "2-5년": 0, "6-10년": 0, "10년+": 0}

        for emp in employees:
            years = emp.years_experience or 0
            if years <= 1:
                experience_groups["0-1년"] += 1
            elif years <= 5:
                experience_groups["2-5년"] += 1
            elif years <= 10:
                experience_groups["6-10년"] += 1
            else:
                experience_groups["10년+"] += 1

        total = len(employees)
        senior_nurses = experience_groups["6-10년"] + experience_groups["10년+"]

        if senior_nurses / total < 0.3:  # 30% 미만
            result.add_warning(
                f"6년 이상 경력 간호사가 {senior_nurses/total*100:.1f}%로 부족합니다. "
                f"야간 근무나 응급 상황 대응이 어려울 수 있습니다.",
                "experience_distribution"
            )

        result.staff_analysis["experience_distribution"] = experience_groups

    def _check_leave_requests(self, ward_id: int, year: int, month: int, employees: List[Employee], result: PreCheckResult):
        """휴가 및 근무 요청사항 검증"""
        # 해당 월의 시작일과 종료일 계산
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        days_in_month = (end_date - start_date).days

        # 승인된 휴가/근무 요청 조회
        shift_requests = self.db.query(ShiftRequest).filter(
            ShiftRequest.employee_id.in_([emp.id for emp in employees]),
            ShiftRequest.request_date >= start_date,
            ShiftRequest.request_date < end_date,
            ShiftRequest.status == "approved"
        ).all()

        leave_counts = {}
        work_requests = {}

        for req in shift_requests:
            emp_id = req.employee_id
            if req.request_type == "leave":
                leave_counts[emp_id] = leave_counts.get(emp_id, 0) + 1
            else:
                work_requests[emp_id] = work_requests.get(emp_id, 0) + 1

        # 과도한 휴가 요청 검증
        excessive_leave = []
        for emp_id, leave_days in leave_counts.items():
            if leave_days > days_in_month * 0.3:  # 월의 30% 이상
                emp = next((e for e in employees if e.id == emp_id), None)
                if emp:
                    excessive_leave.append(f"{emp.employee_number} ({leave_days}일)")

        if excessive_leave:
            result.add_warning(
                f"다음 직원들의 휴가 요청이 많습니다: {', '.join(excessive_leave)}",
                "leave_requests"
            )

        # 전체 가용 인력 분석
        total_leave_days = sum(leave_counts.values())
        total_possible_days = len(employees) * days_in_month
        leave_ratio = total_leave_days / total_possible_days if total_possible_days > 0 else 0

        if leave_ratio > 0.2:  # 20% 이상
            result.add_warning(
                f"전체 가용 인력의 {leave_ratio*100:.1f}%가 휴가 예정입니다. "
                f"근무표 생성이 어려울 수 있습니다.",
                "leave_requests"
            )

        result.staff_analysis["leave_analysis"] = {
            "total_leave_days": total_leave_days,
            "leave_ratio": leave_ratio,
            "days_in_month": days_in_month,
            "employees_with_leave": len(leave_counts),
            "work_requests_count": len(work_requests)
        }

    def _check_existing_schedules(self, ward_id: int, year: int, month: int, result: PreCheckResult):
        """기존 근무표 충돌 검증"""
        existing_schedule = self.db.query(Schedule).filter(
            Schedule.ward_id == ward_id,
            Schedule.year == year,
            Schedule.month == month
        ).first()

        if existing_schedule:
            if existing_schedule.status == "published":
                result.add_error(
                    f"{year}년 {month}월 근무표가 이미 발행되었습니다.",
                    "schedule_conflict"
                )
            elif existing_schedule.status == "approved":
                result.add_warning(
                    f"{year}년 {month}월 근무표가 이미 승인되었습니다. "
                    f"새로 생성 시 기존 근무표가 대체됩니다.",
                    "schedule_conflict"
                )
            else:
                result.add_warning(
                    f"{year}년 {month}월 임시 근무표가 존재합니다. "
                    f"새로 생성 시 기존 근무표가 대체됩니다.",
                    "schedule_conflict"
                )

    def _generate_recommendations(self, ward: Ward, employees: List[Employee], result: PreCheckResult):
        """종합 분석 및 권고사항 생성"""
        total_staff = len(employees)

        # 인력 충원 권고
        if total_staff < 8:
            result.add_recommendation(f"안정적인 근무표 운영을 위해 최소 8명 이상의 인력 충원을 권장합니다. (현재: {total_staff}명)")

        # 신입간호사 교육 권고
        new_nurses = sum(1 for emp in employees if (emp.skill_level or "신입") == "신입")
        if new_nurses > total_staff * 0.3:
            result.add_recommendation("신입간호사 비율이 높습니다. 충분한 교육과 멘토링 시스템 구축을 권장합니다.")

        # 야간 근무 전담 인력 권고
        night_capable = sum(1 for emp in employees if (emp.years_experience or 0) >= 2)
        if night_capable < 4:
            result.add_recommendation("야간 근무 가능 인력이 부족합니다. 2년 이상 경력자 충원을 권장합니다.")

        # 병동 규칙 최적화 권고
        ward_rules = ward.shift_rules or {}
        if not ward_rules.get("max_consecutive_days"):
            result.add_recommendation("연속 근무일 제한 규칙 설정을 권장합니다.")

        if not ward_rules.get("max_night_shifts_per_month"):
            result.add_recommendation("월간 야간 근무 제한 규칙 설정을 권장합니다.")


def get_precheck_service(db: Session) -> SchedulePreCheckService:
    """Pre-check 서비스 인스턴스 생성"""
    return SchedulePreCheckService(db)