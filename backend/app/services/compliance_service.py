"""
근무 규칙 및 법적 준수 검증 서비스
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import ShiftRule, ComplianceViolation, Employee, Schedule
import json

class ComplianceService:
    def __init__(self, db: Session):
        self.db = db
    
    def validate_schedule(self, schedule: Schedule) -> Tuple[bool, List[Dict]]:
        """
        스케줄 전체의 법적 준수성을 검증
        Returns: (is_compliant, violations_list)
        """
        violations = []
        rules = self._get_active_rules(schedule.ward_id)
        
        for rule in rules:
            rule_violations = self._check_rule_compliance(schedule, rule)
            violations.extend(rule_violations)
        
        is_compliant = len(violations) == 0
        return is_compliant, violations
    
    def _get_active_rules(self, ward_id: int) -> List[ShiftRule]:
        """활성 규칙 조회 (병동별 + 전체 규칙)"""
        return self.db.query(ShiftRule).filter(
            ((ShiftRule.ward_id == ward_id) | (ShiftRule.ward_id.is_(None))),
            ShiftRule.is_active == True
        ).all()
    
    def _check_rule_compliance(self, schedule: Schedule, rule: ShiftRule) -> List[Dict]:
        """개별 규칙 준수 검증"""
        violations = []
        schedule_data = schedule.schedule_data
        
        if rule.category == "consecutive":
            violations.extend(self._check_consecutive_shifts(schedule_data, rule))
        elif rule.category == "weekly":
            violations.extend(self._check_weekly_limits(schedule_data, rule))
        elif rule.category == "legal":
            violations.extend(self._check_legal_hours(schedule_data, rule))
        elif rule.category == "pattern":
            violations.extend(self._check_forbidden_patterns(schedule_data, rule))
        
        return violations
    
    def _check_consecutive_shifts(self, schedule_data: Dict, rule: ShiftRule) -> List[Dict]:
        """연속 근무 제한 검증"""
        violations = []
        
        for employee_id, shifts in schedule_data.items():
            # 연속 야간근무 검사
            night_streak = 0
            work_streak = 0
            
            for day, shift_type in enumerate(shifts):
                if shift_type == "night":
                    night_streak += 1
                    work_streak += 1
                    
                    if night_streak > rule.max_consecutive_nights:
                        violations.append({
                            "employee_id": employee_id,
                            "rule_id": rule.id,
                            "violation_type": "consecutive_nights_exceeded",
                            "day": day + 1,
                            "description": f"연속 야간근무 {night_streak}일 (최대 {rule.max_consecutive_nights}일)",
                            "severity": "high",
                            "penalty_score": 1000
                        })
                elif shift_type != "off":
                    night_streak = 0
                    work_streak += 1
                    
                    if work_streak > rule.max_consecutive_days:
                        violations.append({
                            "employee_id": employee_id,
                            "rule_id": rule.id,
                            "violation_type": "consecutive_days_exceeded",
                            "day": day + 1,
                            "description": f"연속 근무 {work_streak}일 (최대 {rule.max_consecutive_days}일)",
                            "severity": "high",
                            "penalty_score": 500
                        })
                else:  # off day
                    night_streak = 0
                    work_streak = 0
        
        return violations
    
    def _check_weekly_limits(self, schedule_data: Dict, rule: ShiftRule) -> List[Dict]:
        """주간 제한 검증 (휴무일 보장)"""
        violations = []
        
        for employee_id, shifts in schedule_data.items():
            # 7일 단위로 분할하여 검사
            for week_start in range(0, len(shifts), 7):
                week_shifts = shifts[week_start:week_start + 7]
                rest_days = week_shifts.count("off")
                
                if rest_days < rule.min_rest_days_per_week:
                    violations.append({
                        "employee_id": employee_id,
                        "rule_id": rule.id,
                        "violation_type": "insufficient_rest_days",
                        "week": week_start // 7 + 1,
                        "description": f"주간 휴무 {rest_days}일 (최소 {rule.min_rest_days_per_week}일)",
                        "severity": "medium",
                        "penalty_score": 300
                    })
        
        return violations
    
    def _check_legal_hours(self, schedule_data: Dict, rule: ShiftRule) -> List[Dict]:
        """법정 근무시간 검증"""
        violations = []
        shift_hours = {"day": 8, "evening": 8, "night": 8, "off": 0}
        
        for employee_id, shifts in schedule_data.items():
            # 주간 근무시간 계산
            for week_start in range(0, len(shifts), 7):
                week_shifts = shifts[week_start:week_start + 7]
                total_hours = sum(shift_hours.get(shift, 0) for shift in week_shifts)
                
                if total_hours > rule.max_hours_per_week:
                    violations.append({
                        "employee_id": employee_id,
                        "rule_id": rule.id,
                        "violation_type": "weekly_hours_exceeded",
                        "week": week_start // 7 + 1,
                        "description": f"주간 근무 {total_hours}시간 (최대 {rule.max_hours_per_week}시간)",
                        "severity": "critical",
                        "penalty_score": 2000
                    })
        
        return violations
    
    def _check_forbidden_patterns(self, schedule_data: Dict, rule: ShiftRule) -> List[Dict]:
        """금지된 근무 패턴 검증"""
        violations = []
        forbidden = rule.forbidden_patterns or []
        
        for employee_id, shifts in schedule_data.items():
            for i in range(len(shifts) - 1):
                current_shift = shifts[i]
                next_shift = shifts[i + 1]
                pattern = f"{current_shift}->{next_shift}"
                
                if pattern in forbidden:
                    violations.append({
                        "employee_id": employee_id,
                        "rule_id": rule.id,
                        "violation_type": "forbidden_pattern",
                        "day": i + 1,
                        "description": f"금지된 패턴: {pattern}",
                        "severity": "medium",
                        "penalty_score": 200
                    })
        
        return violations
    
    def create_default_rules(self, ward_id: int = None) -> List[ShiftRule]:
        """기본 근무 규칙 생성"""
        default_rules = [
            ShiftRule(
                ward_id=ward_id,
                rule_name="연속 야간근무 제한",
                rule_type="hard",
                category="consecutive",
                max_consecutive_nights=3,
                penalty_weight=2.0
            ),
            ShiftRule(
                ward_id=ward_id,
                rule_name="연속 근무일 제한",
                rule_type="hard",
                category="consecutive",
                max_consecutive_days=5,
                penalty_weight=1.5
            ),
            ShiftRule(
                ward_id=ward_id,
                rule_name="주간 휴무 보장",
                rule_type="hard",
                category="weekly",
                min_rest_days_per_week=1,
                penalty_weight=2.0
            ),
            ShiftRule(
                ward_id=ward_id,
                rule_name="법정 근무시간 준수",
                rule_type="hard",
                category="legal",
                max_hours_per_week=40,
                penalty_weight=3.0
            ),
            ShiftRule(
                ward_id=ward_id,
                rule_name="피로 패턴 방지",
                rule_type="soft",
                category="pattern",
                forbidden_patterns=["day->night", "night->day", "evening->day"],
                penalty_weight=1.0
            )
        ]
        
        for rule in default_rules:
            self.db.add(rule)
        
        self.db.commit()
        return default_rules
    
    def calculate_compliance_score(self, schedule: Schedule) -> float:
        """규칙 준수 점수 계산"""
        is_compliant, violations = self.validate_schedule(schedule)
        
        if is_compliant:
            return 100.0
        
        total_penalty = sum(v.get("penalty_score", 0) for v in violations)
        base_score = 100.0
        final_score = max(0.0, base_score - (total_penalty / 100))
        
        return final_score
    
    def save_violations(self, schedule: Schedule, violations: List[Dict]) -> List[ComplianceViolation]:
        """규칙 위반 사항 저장"""
        violation_objects = []
        
        for violation in violations:
            violation_obj = ComplianceViolation(
                schedule_id=schedule.id,
                employee_id=violation["employee_id"],
                rule_id=violation["rule_id"],
                violation_date=datetime.utcnow(),
                violation_type=violation["violation_type"],
                description=violation["description"],
                severity=violation["severity"],
                penalty_score=violation["penalty_score"]
            )
            self.db.add(violation_obj)
            violation_objects.append(violation_obj)
        
        self.db.commit()
        return violation_objects