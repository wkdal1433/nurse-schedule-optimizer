"""
점수 상세 분석 서비스 (Score Breakdown Service)
근무표 평가 점수의 세부 항목별 분석 및 설명 제공
"""

from typing import Dict, List, Any, Tuple
import json
from datetime import datetime
from enum import Enum


class ScoreCategory(Enum):
    """점수 카테고리"""
    LEGAL_COMPLIANCE = "legal_compliance"        # 법적 준수
    STAFFING_SAFETY = "staffing_safety"          # 인력 안전
    ROLE_COMPLIANCE = "role_compliance"          # 역할 준수
    PATTERN_QUALITY = "pattern_quality"          # 근무 패턴 품질
    PREFERENCE_SATISFACTION = "preference_satisfaction"  # 선호도 충족
    FAIRNESS = "fairness"                        # 공평성
    COVERAGE_QUALITY = "coverage_quality"        # 커버리지 품질


class ScoreBreakdownService:
    """점수 세부 분석 서비스"""

    def __init__(self):
        # 점수 가중치 (scheduler.py와 동일)
        self.constraint_weights = {
            "legal_compliance": 1000,
            "staffing_safety": 500,
            "role_compliance": 50,
            "pattern_penalty": 30,
            "preference_bonus": 20,
            "preference_penalty": 10,
            "compliance_bonus": 100
        }

        # 점수 설명 사전
        self.score_explanations = self._initialize_score_explanations()

        # 개선 제안 템플릿
        self.improvement_suggestions = self._initialize_improvement_suggestions()

    def analyze_schedule_scores(self, schedule_data: List[List[int]],
                              employees: List[Dict],
                              constraints: Dict[str, Any],
                              shift_requests: List[Dict] = None) -> Dict[str, Any]:
        """
        근무표 점수 세부 분석

        Returns:
            상세 점수 분석 결과
        """
        if shift_requests is None:
            shift_requests = []

        breakdown = {
            "total_score": 0.0,
            "category_scores": {},
            "detailed_analysis": {},
            "improvement_suggestions": [],
            "rule_compliance": {},
            "statistics": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        # 1. 법적 준수 점수 분석
        legal_analysis = self._analyze_legal_compliance(schedule_data, employees, constraints)
        breakdown["category_scores"]["legal_compliance"] = legal_analysis
        breakdown["total_score"] += legal_analysis["weighted_score"]

        # 2. 인력 안전 점수 분석
        safety_analysis = self._analyze_staffing_safety(schedule_data, constraints)
        breakdown["category_scores"]["staffing_safety"] = safety_analysis
        breakdown["total_score"] += safety_analysis["weighted_score"]

        # 3. 역할 준수 점수 분석
        role_analysis = self._analyze_role_compliance(schedule_data, employees, constraints)
        breakdown["category_scores"]["role_compliance"] = role_analysis
        breakdown["total_score"] += role_analysis["weighted_score"]

        # 4. 근무 패턴 품질 분석
        pattern_analysis = self._analyze_pattern_quality(schedule_data, employees)
        breakdown["category_scores"]["pattern_quality"] = pattern_analysis
        breakdown["total_score"] += pattern_analysis["weighted_score"]

        # 5. 선호도 충족 분석
        preference_analysis = self._analyze_preference_satisfaction(schedule_data, employees, shift_requests)
        breakdown["category_scores"]["preference_satisfaction"] = preference_analysis
        breakdown["total_score"] += preference_analysis["weighted_score"]

        # 6. 공평성 분석
        fairness_analysis = self._analyze_fairness(schedule_data, employees)
        breakdown["category_scores"]["fairness"] = fairness_analysis
        breakdown["total_score"] += fairness_analysis["weighted_score"]

        # 7. 커버리지 품질 분석
        coverage_analysis = self._analyze_coverage_quality(schedule_data, constraints)
        breakdown["category_scores"]["coverage_quality"] = coverage_analysis
        breakdown["total_score"] += coverage_analysis["weighted_score"]

        # 8. 종합 개선 제안 생성
        breakdown["improvement_suggestions"] = self._generate_improvement_suggestions(breakdown["category_scores"])

        # 9. 통계 정보 계산
        breakdown["statistics"] = self._calculate_breakdown_statistics(breakdown["category_scores"])

        return breakdown

    def _analyze_legal_compliance(self, schedule: List[List[int]],
                                 employees: List[Dict],
                                 constraints: Dict[str, Any]) -> Dict[str, Any]:
        """법적 준수 항목 상세 분석"""
        analysis = {
            "category": "법적 준수",
            "weight": self.constraint_weights["legal_compliance"],
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        violation_count = 0
        compliance_details = {}

        for emp_idx, emp in enumerate(employees):
            emp_violations = []

            # 1. 연속 근무일 제한 검사 (최대 5일)
            max_consecutive = self._check_consecutive_work_days(schedule, emp_idx)
            if max_consecutive > 5:
                violation_count += (max_consecutive - 5)
                emp_violations.append({
                    "rule": "연속 근무일 제한",
                    "violation": f"최대 {max_consecutive}일 연속 근무 (한계: 5일)",
                    "severity": "high",
                    "penalty": -50 * (max_consecutive - 5)
                })

            # 2. 연속 야간 근무 제한 검사 (최대 3일)
            max_consecutive_night = self._check_consecutive_night_shifts(schedule, emp_idx)
            if max_consecutive_night > 3:
                violation_count += (max_consecutive_night - 3)
                emp_violations.append({
                    "rule": "연속 야간근무 제한",
                    "violation": f"최대 {max_consecutive_night}일 연속 야간근무 (한계: 3일)",
                    "severity": "high",
                    "penalty": -75 * (max_consecutive_night - 3)
                })

            # 3. 주간 휴식 보장 검사 (7일에 1회 이상)
            weekly_rest_violations = self._check_weekly_rest(schedule, emp_idx)
            if weekly_rest_violations > 0:
                violation_count += weekly_rest_violations
                emp_violations.append({
                    "rule": "주간 휴식 보장",
                    "violation": f"{weekly_rest_violations}주간 휴식 부족",
                    "severity": "medium",
                    "penalty": -30 * weekly_rest_violations
                })

            # 4. 근무시간 제한 검사 (주 40시간)
            weekly_hours_violation = self._check_weekly_hours(schedule, emp_idx, emp)
            if weekly_hours_violation > 0:
                violation_count += 1
                emp_violations.append({
                    "rule": "법정 근무시간 준수",
                    "violation": f"주당 {40 + weekly_hours_violation}시간 근무 (법적 한계: 40시간)",
                    "severity": "high",
                    "penalty": -100
                })

            if emp_violations:
                analysis["violations"].extend([{
                    "employee_id": emp["id"],
                    "employee_name": emp.get("employee_number", f"직원{emp_idx+1}"),
                    "violations": emp_violations
                }])

        # 점수 계산
        base_score = 100.0  # 기본 점수
        penalty_score = violation_count * -10  # 위반당 -10점
        analysis["raw_score"] = max(0, base_score + penalty_score)
        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        # 준수율 계산
        total_checks = len(employees) * 4  # 직원별 4개 법적 요구사항
        compliance_rate = max(0, 1 - (violation_count / max(total_checks, 1)))

        analysis["compliance_items"] = {
            "total_violations": violation_count,
            "compliance_rate": compliance_rate * 100,
            "total_employees_checked": len(employees),
            "legal_requirements_count": 4
        }

        analysis["details"] = {
            "explanation": self.score_explanations["legal_compliance"],
            "calculation": f"기본점수(100) + 위반페널티({penalty_score}) = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    def _analyze_staffing_safety(self, schedule: List[List[int]], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """인력 안전 항목 상세 분석"""
        analysis = {
            "category": "인력 안전",
            "weight": self.constraint_weights["staffing_safety"],
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        required_staff = constraints.get("required_staff", {"day": 3, "evening": 2, "night": 1})
        shift_names = ["day", "evening", "night"]

        violations = []
        total_shortfall = 0
        days_with_issues = 0

        for day_idx, day_schedule in enumerate(schedule):
            daily_violations = []

            for shift_type in range(3):  # day, evening, night
                actual_count = day_schedule.count(shift_type)
                required_count = required_staff.get(shift_names[shift_type], 1)

                if actual_count < required_count:
                    shortfall = required_count - actual_count
                    total_shortfall += shortfall

                    daily_violations.append({
                        "shift": shift_names[shift_type],
                        "required": required_count,
                        "actual": actual_count,
                        "shortfall": shortfall,
                        "severity": "high" if shortfall >= 2 else "medium"
                    })

            if daily_violations:
                days_with_issues += 1
                violations.append({
                    "day": day_idx + 1,
                    "violations": daily_violations
                })

        # 점수 계산
        base_score = 100.0
        penalty_score = total_shortfall * -20  # 부족한 인원당 -20점
        analysis["raw_score"] = max(0, base_score + penalty_score)
        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        analysis["violations"] = violations
        analysis["compliance_items"] = {
            "days_with_staffing_issues": days_with_issues,
            "total_days": len(schedule),
            "total_staff_shortfall": total_shortfall,
            "safety_compliance_rate": max(0, 1 - (days_with_issues / len(schedule))) * 100
        }

        analysis["details"] = {
            "explanation": self.score_explanations["staffing_safety"],
            "calculation": f"기본점수(100) + 인력부족페널티({penalty_score}) = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    def _analyze_role_compliance(self, schedule: List[List[int]],
                                employees: List[Dict],
                                constraints: Dict[str, Any]) -> Dict[str, Any]:
        """역할 준수 항목 상세 분석"""
        analysis = {
            "category": "역할 준수",
            "weight": self.constraint_weights["role_compliance"],
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        # 신입간호사-선임간호사 페어링 검사
        new_nurse_violations = 0
        role_violations = []

        for emp_idx, emp in enumerate(employees):
            skill_level = emp.get("skill_level", "중급")
            years_experience = emp.get("years_experience", 2)

            # 신입간호사 야간근무 단독 배치 검사
            if skill_level == "신입" or years_experience <= 1:
                night_alone_days = self._check_new_nurse_night_alone(schedule, emp_idx, employees)
                if night_alone_days > 0:
                    new_nurse_violations += night_alone_days
                    role_violations.append({
                        "employee_id": emp["id"],
                        "employee_name": emp.get("employee_number", f"직원{emp_idx+1}"),
                        "violation": f"신입간호사 야간근무 {night_alone_days}일 단독 배치",
                        "severity": "medium",
                        "penalty": -15 * night_alone_days
                    })

        # 점수 계산
        base_score = 100.0
        penalty_score = new_nurse_violations * -15
        analysis["raw_score"] = max(0, base_score + penalty_score)
        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        analysis["violations"] = role_violations
        analysis["compliance_items"] = {
            "new_nurse_violations": new_nurse_violations,
            "role_compliance_rate": max(0, 1 - (new_nurse_violations / max(len(schedule) * len(employees), 1))) * 100
        }

        analysis["details"] = {
            "explanation": self.score_explanations["role_compliance"],
            "calculation": f"기본점수(100) + 역할위반페널티({penalty_score}) = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    def _analyze_pattern_quality(self, schedule: List[List[int]], employees: List[Dict]) -> Dict[str, Any]:
        """근무 패턴 품질 상세 분석"""
        analysis = {
            "category": "근무 패턴 품질",
            "weight": self.constraint_weights["pattern_penalty"],
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        pattern_violations = []
        total_bad_patterns = 0

        for emp_idx, emp in enumerate(employees):
            emp_violations = []

            # 나쁜 근무 패턴 검사 (Day→Night, Evening→Day 등)
            bad_patterns = self._check_bad_shift_patterns(schedule, emp_idx)
            total_bad_patterns += len(bad_patterns)

            if bad_patterns:
                emp_violations.extend([{
                    "pattern": pattern["type"],
                    "day": pattern["day"],
                    "description": pattern["description"],
                    "severity": "medium",
                    "penalty": -5
                } for pattern in bad_patterns])

            if emp_violations:
                pattern_violations.append({
                    "employee_id": emp["id"],
                    "employee_name": emp.get("employee_number", f"직원{emp_idx+1}"),
                    "violations": emp_violations
                })

        # 점수 계산
        base_score = 100.0
        penalty_score = total_bad_patterns * -5
        analysis["raw_score"] = max(0, base_score + penalty_score)
        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        analysis["violations"] = pattern_violations
        analysis["compliance_items"] = {
            "total_bad_patterns": total_bad_patterns,
            "pattern_quality_rate": max(0, 1 - (total_bad_patterns / max(len(schedule) * len(employees), 1))) * 100
        }

        analysis["details"] = {
            "explanation": self.score_explanations["pattern_quality"],
            "calculation": f"기본점수(100) + 패턴페널티({penalty_score}) = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    def _analyze_preference_satisfaction(self, schedule: List[List[int]],
                                       employees: List[Dict],
                                       shift_requests: List[Dict]) -> Dict[str, Any]:
        """선호도 충족 상세 분석"""
        analysis = {
            "category": "선호도 충족",
            "weight": self.constraint_weights["preference_bonus"],
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        satisfied_preferences = 0
        total_preferences = len(shift_requests)
        preference_details = []

        # 근무 요청사항 만족도 계산
        for request in shift_requests:
            emp_id = request.get("employee_id")
            request_date = request.get("request_date")
            requested_shift = request.get("shift_type", "off")
            request_type = request.get("request_type", "preference")

            # 해당 날짜의 실제 배정 확인
            day_index = self._get_day_index_from_date(request_date)
            emp_index = self._get_employee_index(employees, emp_id)

            if day_index is not None and emp_index is not None and day_index < len(schedule):
                actual_shift = schedule[day_index][emp_index]
                shift_names = ["day", "evening", "night", "off"]

                is_satisfied = (
                    (requested_shift == "off" and actual_shift == 3) or
                    (requested_shift == "day" and actual_shift == 0) or
                    (requested_shift == "evening" and actual_shift == 1) or
                    (requested_shift == "night" and actual_shift == 2)
                )

                if is_satisfied:
                    satisfied_preferences += 1

                preference_details.append({
                    "employee_id": emp_id,
                    "date": str(request_date),
                    "requested": requested_shift,
                    "assigned": shift_names[actual_shift],
                    "satisfied": is_satisfied,
                    "type": request_type
                })

        # 점수 계산
        if total_preferences > 0:
            satisfaction_rate = satisfied_preferences / total_preferences
            analysis["raw_score"] = satisfaction_rate * 100
        else:
            satisfaction_rate = 1.0
            analysis["raw_score"] = 100.0

        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        analysis["compliance_items"] = {
            "total_preferences": total_preferences,
            "satisfied_preferences": satisfied_preferences,
            "satisfaction_rate": satisfaction_rate * 100,
            "preference_details": preference_details[:10]  # 최대 10개만 표시
        }

        analysis["details"] = {
            "explanation": self.score_explanations["preference_satisfaction"],
            "calculation": f"충족률({satisfaction_rate:.2%}) × 100 = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    def _analyze_fairness(self, schedule: List[List[int]], employees: List[Dict]) -> Dict[str, Any]:
        """공평성 상세 분석"""
        analysis = {
            "category": "공평성",
            "weight": 50,  # 공평성 가중치
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        # 야간근무 분포 분석
        night_shift_counts = []
        weekend_counts = []

        for emp_idx, emp in enumerate(employees):
            night_count = 0
            weekend_count = 0

            for day_idx, day_schedule in enumerate(schedule):
                if day_schedule[emp_idx] == 2:  # night shift
                    night_count += 1

                # 주말 근무 (단순화: 토요일=6, 일요일=0으로 가정)
                if day_idx % 7 in [0, 6] and day_schedule[emp_idx] < 3:  # 주말에 근무
                    weekend_count += 1

            night_shift_counts.append(night_count)
            weekend_counts.append(weekend_count)

        # 공평성 점수 계산 (표준편차 기반)
        night_fairness = self._calculate_fairness_score(night_shift_counts)
        weekend_fairness = self._calculate_fairness_score(weekend_counts)

        analysis["raw_score"] = (night_fairness + weekend_fairness) / 2
        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        analysis["compliance_items"] = {
            "night_shift_distribution": {
                "min": min(night_shift_counts) if night_shift_counts else 0,
                "max": max(night_shift_counts) if night_shift_counts else 0,
                "average": sum(night_shift_counts) / len(night_shift_counts) if night_shift_counts else 0,
                "fairness_score": night_fairness
            },
            "weekend_distribution": {
                "min": min(weekend_counts) if weekend_counts else 0,
                "max": max(weekend_counts) if weekend_counts else 0,
                "average": sum(weekend_counts) / len(weekend_counts) if weekend_counts else 0,
                "fairness_score": weekend_fairness
            }
        }

        analysis["details"] = {
            "explanation": self.score_explanations["fairness"],
            "calculation": f"(야간공평성{night_fairness:.1f} + 주말공평성{weekend_fairness:.1f}) / 2 = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    def _analyze_coverage_quality(self, schedule: List[List[int]], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """커버리지 품질 상세 분석"""
        analysis = {
            "category": "커버리지 품질",
            "weight": self.constraint_weights["compliance_bonus"],
            "raw_score": 0.0,
            "weighted_score": 0.0,
            "violations": [],
            "compliance_items": {},
            "details": {}
        }

        required_staff = constraints.get("required_staff", {"day": 3, "evening": 2, "night": 1})
        shift_names = ["day", "evening", "night"]

        perfect_coverage_days = 0
        over_coverage_bonus = 0

        for day_schedule in schedule:
            day_perfect = True

            for shift_type in range(3):
                actual_count = day_schedule.count(shift_type)
                required_count = required_staff.get(shift_names[shift_type], 1)

                if actual_count < required_count:
                    day_perfect = False
                elif actual_count > required_count:
                    over_coverage_bonus += (actual_count - required_count) * 5  # 초과 인력당 +5점

            if day_perfect:
                perfect_coverage_days += 1

        # 점수 계산
        coverage_rate = perfect_coverage_days / len(schedule) if schedule else 0
        base_score = coverage_rate * 100
        analysis["raw_score"] = min(100, base_score + over_coverage_bonus)
        analysis["weighted_score"] = analysis["raw_score"] * analysis["weight"]

        analysis["compliance_items"] = {
            "perfect_coverage_days": perfect_coverage_days,
            "total_days": len(schedule),
            "coverage_rate": coverage_rate * 100,
            "over_coverage_bonus": over_coverage_bonus
        }

        analysis["details"] = {
            "explanation": self.score_explanations["coverage_quality"],
            "calculation": f"완벽커버리지율({coverage_rate:.2%}) × 100 + 초과보너스({over_coverage_bonus}) = {analysis['raw_score']:.1f}",
            "weight_applied": f"{analysis['raw_score']:.1f} × {analysis['weight']} = {analysis['weighted_score']:.0f}"
        }

        return analysis

    # =============== 헬퍼 메소드들 ===============

    def _check_consecutive_work_days(self, schedule: List[List[int]], emp_idx: int) -> int:
        """연속 근무일 계산"""
        max_consecutive = 0
        current_consecutive = 0

        for day_schedule in schedule:
            if day_schedule[emp_idx] < 3:  # 근무 (OFF가 아님)
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def _check_consecutive_night_shifts(self, schedule: List[List[int]], emp_idx: int) -> int:
        """연속 야간근무 계산"""
        max_consecutive_night = 0
        current_consecutive_night = 0

        for day_schedule in schedule:
            if day_schedule[emp_idx] == 2:  # 야간 근무
                current_consecutive_night += 1
                max_consecutive_night = max(max_consecutive_night, current_consecutive_night)
            else:
                current_consecutive_night = 0

        return max_consecutive_night

    def _check_weekly_rest(self, schedule: List[List[int]], emp_idx: int) -> int:
        """주간 휴식 위반 계산"""
        violations = 0
        days_count = len(schedule)

        # 7일 단위로 체크
        for week_start in range(0, days_count, 7):
            week_end = min(week_start + 7, days_count)
            week_rest_days = 0

            for day_idx in range(week_start, week_end):
                if schedule[day_idx][emp_idx] == 3:  # OFF
                    week_rest_days += 1

            if week_rest_days == 0:  # 일주일 동안 휴무가 없음
                violations += 1

        return violations

    def _check_weekly_hours(self, schedule: List[List[int]], emp_idx: int, emp: Dict) -> int:
        """주간 근무시간 위반 계산 (간단화)"""
        # 근무 시간: day=8h, evening=8h, night=8h로 가정
        total_work_days = 0
        for day_schedule in schedule:
            if day_schedule[emp_idx] < 3:  # 근무일
                total_work_days += 1

        # 월 근무시간을 주 평균으로 환산
        weeks_in_month = len(schedule) / 7
        average_weekly_hours = (total_work_days * 8) / weeks_in_month if weeks_in_month > 0 else 0

        return max(0, average_weekly_hours - 40)

    def _check_new_nurse_night_alone(self, schedule: List[List[int]], new_nurse_idx: int, employees: List[Dict]) -> int:
        """신입간호사 야간근무 단독 배치 일수 계산"""
        alone_nights = 0

        for day_schedule in schedule:
            if day_schedule[new_nurse_idx] == 2:  # 신입간호사가 야간근무
                # 같은 날 야간근무하는 선임간호사가 있는지 확인
                has_senior = False
                for emp_idx, emp in enumerate(employees):
                    if (emp_idx != new_nurse_idx and
                        day_schedule[emp_idx] == 2 and  # 야간근무
                        emp.get("years_experience", 0) > 2):  # 선임간호사
                        has_senior = True
                        break

                if not has_senior:
                    alone_nights += 1

        return alone_nights

    def _check_bad_shift_patterns(self, schedule: List[List[int]], emp_idx: int) -> List[Dict]:
        """나쁜 근무 패턴 검사"""
        bad_patterns = []
        shift_names = ["주간", "저녁", "야간", "휴무"]

        for day_idx in range(len(schedule) - 1):
            current_shift = schedule[day_idx][emp_idx]
            next_shift = schedule[day_idx + 1][emp_idx]

            # 나쁜 패턴 정의
            if (current_shift == 0 and next_shift == 2) or (current_shift == 2 and next_shift == 0):  # Day->Night, Night->Day
                bad_patterns.append({
                    "type": f"{shift_names[current_shift]}→{shift_names[next_shift]}",
                    "day": day_idx + 1,
                    "description": "피로도 증가 패턴"
                })

        return bad_patterns

    def _get_day_index_from_date(self, date) -> int:
        """날짜로부터 일 인덱스 계산 (단순화)"""
        if hasattr(date, 'day'):
            return date.day - 1
        return None

    def _get_employee_index(self, employees: List[Dict], emp_id: int) -> int:
        """직원 ID로부터 인덱스 찾기"""
        for idx, emp in enumerate(employees):
            if emp.get("id") == emp_id:
                return idx
        return None

    def _calculate_fairness_score(self, counts: List[int]) -> float:
        """공평성 점수 계산 (표준편차 기반)"""
        if not counts or len(counts) <= 1:
            return 100.0

        mean_count = sum(counts) / len(counts)
        variance = sum((x - mean_count) ** 2 for x in counts) / len(counts)
        std_dev = variance ** 0.5

        # 표준편차가 작을수록 공평함 (최대 100점)
        if mean_count == 0:
            return 100.0

        fairness_score = max(0, 100 - (std_dev / mean_count * 100))
        return fairness_score

    def _generate_improvement_suggestions(self, category_scores: Dict) -> List[Dict]:
        """카테고리별 점수를 기반으로 개선 제안 생성"""
        suggestions = []

        for category, analysis in category_scores.items():
            if analysis["raw_score"] < 70:  # 70점 미만인 경우 개선 제안
                suggestion = self.improvement_suggestions.get(category, {})
                if suggestion:
                    suggestions.append({
                        "category": analysis["category"],
                        "current_score": analysis["raw_score"],
                        "priority": "high" if analysis["raw_score"] < 50 else "medium",
                        "suggestions": suggestion.get("suggestions", []),
                        "expected_improvement": suggestion.get("expected_improvement", "점수 향상")
                    })

        return suggestions

    def _calculate_breakdown_statistics(self, category_scores: Dict) -> Dict:
        """점수 분석 통계 계산"""
        scores = [analysis["raw_score"] for analysis in category_scores.values()]

        return {
            "highest_score_category": max(category_scores.items(), key=lambda x: x[1]["raw_score"])[1]["category"],
            "lowest_score_category": min(category_scores.items(), key=lambda x: x[1]["raw_score"])[1]["category"],
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_distribution": {
                "excellent": len([s for s in scores if s >= 90]),
                "good": len([s for s in scores if 70 <= s < 90]),
                "fair": len([s for s in scores if 50 <= s < 70]),
                "poor": len([s for s in scores if s < 50])
            }
        }

    def _initialize_score_explanations(self) -> Dict[str, str]:
        """점수 설명 초기화"""
        return {
            "legal_compliance": "근로기준법 및 의료법에 따른 필수 준수사항으로, 연속근무일 제한, 야간근무 제한, 주휴 보장, 법정근로시간 준수를 평가합니다.",
            "staffing_safety": "환자 안전을 위한 시프트별 최소 인원 확보 여부를 평가하여, 의료사고 예방과 간호 품질 보장을 측정합니다.",
            "role_compliance": "간호사의 역할과 경험 수준에 따른 적절한 업무 배정으로, 신입간호사 보호와 적정 역할 분담을 평가합니다.",
            "pattern_quality": "간호사의 피로도와 업무 효율을 고려한 근무 패턴 품질로, 연속된 시프트 간의 적절한 배치를 평가합니다.",
            "preference_satisfaction": "간호사 개인의 근무 선호도와 휴가 요청 반영 정도로, 직원 만족도와 근무 의욕 향상을 측정합니다.",
            "fairness": "야간근무, 주말근무 등의 공평한 분배 정도로, 특정 직원에게 부담이 집중되지 않도록 하는 균형을 평가합니다.",
            "coverage_quality": "각 시프트별 적정 인력 배치와 추가 여유 인력 확보로, 돌발 상황 대응 능력과 서비스 품질을 측정합니다."
        }

    def _initialize_improvement_suggestions(self) -> Dict[str, Dict]:
        """개선 제안 템플릿 초기화"""
        return {
            "legal_compliance": {
                "suggestions": [
                    "연속 근무일을 5일 이하로 제한하여 법적 요구사항 준수",
                    "연속 야간근무를 3일 이하로 조정하여 간호사 건강 보호",
                    "주간 휴식일을 반드시 1일 이상 확보하여 주휴 보장",
                    "주당 근무시간을 40시간 이하로 조정하여 법정근로시간 준수"
                ],
                "expected_improvement": "법적 위험 제거 및 근로기준법 완전 준수"
            },
            "staffing_safety": {
                "suggestions": [
                    "시프트별 최소 인원을 항상 확보하여 환자 안전 보장",
                    "응급 상황 대비 여유 인력 1-2명 추가 배치",
                    "중요 시간대(야간, 주말)에 경험있는 간호사 우선 배치"
                ],
                "expected_improvement": "환자 안전 향상 및 의료사고 위험 감소"
            },
            "role_compliance": {
                "suggestions": [
                    "신입간호사 야간근무 시 반드시 선임간호사와 페어링",
                    "경험 수준별 적절한 근무 배치로 업무 품질 향상",
                    "수간호사는 주요 시간대에 우선 배치하여 리더십 발휘"
                ],
                "expected_improvement": "업무 품질 향상 및 신입간호사 교육 효과 증대"
            },
            "pattern_quality": {
                "suggestions": [
                    "Day→Night, Night→Day 같은 피로 증가 패턴 최소화",
                    "근무 간 충분한 휴식 시간 확보로 피로도 관리",
                    "개인별 선호하는 근무 패턴 반영하여 만족도 향상"
                ],
                "expected_improvement": "간호사 피로도 감소 및 업무 효율성 향상"
            },
            "preference_satisfaction": {
                "suggestions": [
                    "휴가 및 근무 선호 요청사항을 최대한 반영",
                    "개인 사정을 고려한 유연한 스케줄링",
                    "정기적인 선호도 조사를 통한 만족도 개선"
                ],
                "expected_improvement": "직원 만족도 향상 및 이직률 감소"
            },
            "fairness": {
                "suggestions": [
                    "야간근무를 모든 간호사에게 공평하게 분배",
                    "주말근무 횟수를 균등하게 조정",
                    "월별 총 근무시간을 개인간 균형있게 배분"
                ],
                "expected_improvement": "팀워크 향상 및 불공평 인식 해소"
            },
            "coverage_quality": {
                "suggestions": [
                    "각 시프트마다 필요 인원보다 1명 여유있게 배치",
                    "핵심 시간대에 숙련된 간호사 우선 배정",
                    "돌발 상황 대비 대체 인력 풀 운영"
                ],
                "expected_improvement": "서비스 품질 향상 및 응급상황 대응력 강화"
            }
        }


def get_score_breakdown_service() -> ScoreBreakdownService:
    """점수 분석 서비스 인스턴스 반환"""
    return ScoreBreakdownService()