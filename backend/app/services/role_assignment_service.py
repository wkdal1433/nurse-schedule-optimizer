"""
역할 기반 및 고용형태별 배치 서비스
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import (
    Employee, RoleConstraint, SupervisionPair, EmploymentTypeRule, 
    RoleViolation, Ward
)
from app.models.scheduling_models import Schedule
from collections import defaultdict
import json

class RoleAssignmentService:
    def __init__(self, db: Session):
        self.db = db
        
        # 역할별 기본 설정
        self.role_hierarchy = {
            "head_nurse": 5,      # 수간호사
            "charge_nurse": 4,    # 책임간호사
            "staff_nurse": 3,     # 일반간호사
            "new_nurse": 1,       # 신입간호사
            "education_coordinator": 4  # 교육담당
        }
    
    def validate_role_assignments(self, schedule: Schedule) -> Tuple[bool, List[Dict]]:
        """스케줄의 역할별 배치 규칙 검증"""
        violations = []
        schedule_data = schedule.schedule_data
        
        # 각 날짜/근무별로 검증
        if not schedule_data:
            return True, []
        
        days_count = len(next(iter(schedule_data.values()), []))
        
        for day_idx in range(days_count):
            for shift_type in ["day", "evening", "night"]:
                day_violations = self._validate_day_shift_assignments(
                    schedule, day_idx, shift_type
                )
                violations.extend(day_violations)
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def _validate_day_shift_assignments(self, schedule: Schedule, 
                                      day_idx: int, shift_type: str) -> List[Dict]:
        """특정 날짜/근무의 역할 배치 검증"""
        violations = []
        schedule_data = schedule.schedule_data
        
        # 해당 날짜/근무에 배치된 직원들 조회
        assigned_employees = []
        employees_by_role = defaultdict(list)
        
        for emp_id_str, shifts in schedule_data.items():
            if day_idx < len(shifts) and shifts[day_idx] == shift_type:
                employee = self.db.query(Employee).filter(
                    Employee.id == int(emp_id_str)
                ).first()
                if employee:
                    assigned_employees.append(employee)
                    employees_by_role[employee.role].append(employee)
        
        if not assigned_employees:
            return violations
        
        # 1. 신입간호사 감독 요구사항 검증
        violations.extend(self._check_new_nurse_supervision(
            employees_by_role, day_idx, shift_type
        ))
        
        # 2. 역할별 최소/최대 인원 검증
        violations.extend(self._check_role_staffing_requirements(
            employees_by_role, schedule.ward_id, day_idx, shift_type
        ))
        
        # 3. 고용형태별 제약조건 검증
        violations.extend(self._check_employment_type_constraints(
            assigned_employees, day_idx, shift_type
        ))
        
        # 4. 특수 역할 페어링 검증
        violations.extend(self._check_special_role_pairing(
            employees_by_role, day_idx, shift_type
        ))
        
        return violations
    
    def _check_new_nurse_supervision(self, employees_by_role: Dict, 
                                   day_idx: int, shift_type: str) -> List[Dict]:
        """신입간호사 감독 요구사항 검증"""
        violations = []
        new_nurses = employees_by_role.get("new_nurse", [])
        
        if not new_nurses:
            return violations
        
        # 감독 가능한 선임간호사 찾기
        supervisors = []
        for role in ["head_nurse", "charge_nurse", "staff_nurse"]:
            for emp in employees_by_role.get(role, []):
                if emp.can_supervise:
                    supervisors.append(emp)
        
        # 각 신입간호사에 대해 감독자 확인
        for new_nurse in new_nurses:
            if new_nurse.requires_supervision:
                # 전담 감독자 확인
                supervision_pair = self.db.query(SupervisionPair).filter(
                    SupervisionPair.supervisee_id == new_nurse.id,
                    SupervisionPair.is_active == True
                ).first()
                
                if supervision_pair:
                    # 전담 감독자가 같은 근무에 있는지 확인
                    supervisor_present = any(
                        s.id == supervision_pair.supervisor_id for s in supervisors
                    )
                    
                    if not supervisor_present:
                        violations.append({
                            "employee_id": new_nurse.id,
                            "violation_type": "missing_designated_supervisor",
                            "day": day_idx + 1,
                            "shift": shift_type,
                            "description": f"신입간호사 {new_nurse.user.full_name}의 전담 감독자가 같은 근무에 없음",
                            "severity": "high",
                            "penalty_score": 800,
                            "required_supervisor_id": supervision_pair.supervisor_id
                        })
                else:
                    # 전담 감독자가 없는 경우, 일반 감독자라도 있어야 함
                    if not supervisors:
                        violations.append({
                            "employee_id": new_nurse.id,
                            "violation_type": "no_supervisor_available",
                            "day": day_idx + 1,
                            "shift": shift_type,
                            "description": f"신입간호사 {new_nurse.user.full_name}를 감독할 선임간호사가 없음",
                            "severity": "critical",
                            "penalty_score": 1500
                        })
        
        return violations
    
    def _check_role_staffing_requirements(self, employees_by_role: Dict, 
                                        ward_id: int, day_idx: int, 
                                        shift_type: str) -> List[Dict]:
        """역할별 최소/최대 인원 요구사항 검증"""
        violations = []
        
        # 병동의 역할별 제약조건 조회
        role_constraints = self.db.query(RoleConstraint).filter(
            ((RoleConstraint.ward_id == ward_id) | (RoleConstraint.ward_id.is_(None))),
            RoleConstraint.is_active == True
        ).all()
        
        for constraint in role_constraints:
            if shift_type not in (constraint.allowed_shifts or ["day", "evening", "night"]):
                continue
            
            role_count = len(employees_by_role.get(constraint.role, []))
            
            # 최소 인원 검증
            if role_count < constraint.min_per_shift:
                violations.append({
                    "violation_type": "insufficient_role_staffing",
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "role": constraint.role,
                    "current_count": role_count,
                    "required_minimum": constraint.min_per_shift,
                    "description": f"{constraint.role} 최소 {constraint.min_per_shift}명 필요, 현재 {role_count}명",
                    "severity": "high",
                    "penalty_score": 1000
                })
            
            # 최대 인원 검증
            if role_count > constraint.max_per_shift:
                violations.append({
                    "violation_type": "excessive_role_staffing", 
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "role": constraint.role,
                    "current_count": role_count,
                    "allowed_maximum": constraint.max_per_shift,
                    "description": f"{constraint.role} 최대 {constraint.max_per_shift}명 허용, 현재 {role_count}명",
                    "severity": "medium",
                    "penalty_score": 300
                })
        
        return violations
    
    def _check_employment_type_constraints(self, assigned_employees: List[Employee], 
                                         day_idx: int, shift_type: str) -> List[Dict]:
        """고용형태별 제약조건 검증"""
        violations = []
        
        for employee in assigned_employees:
            # 고용형태별 규칙 조회
            emp_rule = self.db.query(EmploymentTypeRule).filter(
                EmploymentTypeRule.employment_type == employee.employment_type,
                EmploymentTypeRule.is_active == True
            ).first()
            
            if not emp_rule:
                continue
            
            # 허용된 근무 시간대 확인
            allowed_shifts = emp_rule.allowed_shift_types or ["day", "evening", "night"]
            forbidden_shifts = emp_rule.forbidden_shift_types or []
            
            if shift_type in forbidden_shifts:
                violations.append({
                    "employee_id": employee.id,
                    "violation_type": "forbidden_shift_type",
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "employment_type": employee.employment_type,
                    "description": f"{employee.employment_type} 직원은 {shift_type} 근무 불가",
                    "severity": "high",
                    "penalty_score": 800
                })
            
            if shift_type not in allowed_shifts:
                violations.append({
                    "employee_id": employee.id,
                    "violation_type": "not_allowed_shift_type",
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "employment_type": employee.employment_type,
                    "description": f"{employee.employment_type} 직원에게 허용되지 않은 {shift_type} 근무",
                    "severity": "medium",
                    "penalty_score": 400
                })
            
            # 주말 근무 제한 확인 (토요일=5, 일요일=6)
            day_of_week = day_idx % 7
            if day_of_week in [5, 6] and not emp_rule.weekend_work_allowed:
                violations.append({
                    "employee_id": employee.id,
                    "violation_type": "weekend_work_not_allowed",
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "employment_type": employee.employment_type,
                    "description": f"{employee.employment_type} 직원은 주말 근무 불가",
                    "severity": "high", 
                    "penalty_score": 600
                })
            
            # 야간 근무 제한 확인
            if shift_type == "night" and not emp_rule.night_shift_allowed:
                violations.append({
                    "employee_id": employee.id,
                    "violation_type": "night_shift_not_allowed",
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "employment_type": employee.employment_type,
                    "description": f"{employee.employment_type} 직원은 야간 근무 불가",
                    "severity": "high",
                    "penalty_score": 800
                })
        
        return violations
    
    def _check_special_role_pairing(self, employees_by_role: Dict, 
                                  day_idx: int, shift_type: str) -> List[Dict]:
        """특수 역할 페어링 요구사항 검증"""
        violations = []
        
        # 교육담당자 특별 규칙 (예: 신입간호사와 함께 있을 때만 근무)
        education_coordinators = employees_by_role.get("education_coordinator", [])
        new_nurses = employees_by_role.get("new_nurse", [])
        
        for coordinator in education_coordinators:
            # 교육담당자가 있는데 신입간호사가 없는 경우
            if not new_nurses:
                violations.append({
                    "employee_id": coordinator.id,
                    "violation_type": "education_coordinator_without_new_nurse",
                    "day": day_idx + 1,
                    "shift": shift_type,
                    "description": f"교육담당자 {coordinator.user.full_name}가 신입간호사 없이 근무 배정됨",
                    "severity": "medium",
                    "penalty_score": 200
                })
        
        return violations
    
    def create_supervision_pair(self, supervisor_id: int, supervisee_id: int, 
                              pairing_type: str = "mentor", 
                              end_date: Optional[datetime] = None) -> SupervisionPair:
        """감독 페어 생성"""
        # 기존 페어링 비활성화
        existing = self.db.query(SupervisionPair).filter(
            SupervisionPair.supervisee_id == supervisee_id,
            SupervisionPair.is_active == True
        ).all()
        
        for pair in existing:
            pair.is_active = False
        
        # 새 페어링 생성
        new_pair = SupervisionPair(
            supervisor_id=supervisor_id,
            supervisee_id=supervisee_id,
            pairing_type=pairing_type,
            end_date=end_date
        )
        
        self.db.add(new_pair)
        self.db.commit()
        self.db.refresh(new_pair)
        return new_pair
    
    def create_role_constraint(self, role: str, ward_id: Optional[int], 
                             constraint_data: Dict) -> RoleConstraint:
        """역할별 제약조건 생성"""
        constraint = RoleConstraint(
            role=role,
            ward_id=ward_id,
            allowed_shifts=constraint_data.get("allowed_shifts", ["day", "evening", "night"]),
            forbidden_shifts=constraint_data.get("forbidden_shifts", []),
            min_per_shift=constraint_data.get("min_per_shift", 0),
            max_per_shift=constraint_data.get("max_per_shift", 10),
            requires_pairing_with_roles=constraint_data.get("requires_pairing_with_roles", []),
            cannot_work_with_roles=constraint_data.get("cannot_work_with_roles", []),
            must_have_supervisor=constraint_data.get("must_have_supervisor", False),
            can_be_sole_charge=constraint_data.get("can_be_sole_charge", True)
        )
        
        self.db.add(constraint)
        self.db.commit()
        self.db.refresh(constraint)
        return constraint
    
    def create_employment_type_rule(self, employment_type: str, 
                                   ward_id: Optional[int], 
                                   rule_data: Dict) -> EmploymentTypeRule:
        """고용형태별 규칙 생성"""
        rule = EmploymentTypeRule(
            employment_type=employment_type,
            ward_id=ward_id,
            max_hours_per_day=rule_data.get("max_hours_per_day", 8),
            max_hours_per_week=rule_data.get("max_hours_per_week", 40),
            max_days_per_week=rule_data.get("max_days_per_week", 5),
            max_consecutive_days=rule_data.get("max_consecutive_days", 5),
            allowed_shift_types=rule_data.get("allowed_shift_types", ["day", "evening", "night"]),
            forbidden_shift_types=rule_data.get("forbidden_shift_types", []),
            weekend_work_allowed=rule_data.get("weekend_work_allowed", True),
            night_shift_allowed=rule_data.get("night_shift_allowed", True),
            holiday_work_allowed=rule_data.get("holiday_work_allowed", True),
            scheduling_priority=rule_data.get("scheduling_priority", 5)
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule
    
    def create_default_role_constraints(self, ward_id: int) -> List[RoleConstraint]:
        """기본 역할별 제약조건 생성"""
        default_constraints = [
            {
                "role": "head_nurse",
                "data": {
                    "allowed_shifts": ["day", "evening"],
                    "min_per_shift": 0,
                    "max_per_shift": 1,
                    "can_be_sole_charge": True,
                    "must_have_supervisor": False
                }
            },
            {
                "role": "staff_nurse",
                "data": {
                    "allowed_shifts": ["day", "evening", "night"],
                    "min_per_shift": 2,
                    "max_per_shift": 8,
                    "can_be_sole_charge": True,
                    "must_have_supervisor": False
                }
            },
            {
                "role": "new_nurse",
                "data": {
                    "allowed_shifts": ["day", "evening"],
                    "min_per_shift": 0,
                    "max_per_shift": 3,
                    "requires_pairing_with_roles": ["staff_nurse", "head_nurse"],
                    "can_be_sole_charge": False,
                    "must_have_supervisor": True
                }
            },
            {
                "role": "education_coordinator",
                "data": {
                    "allowed_shifts": ["day"],
                    "min_per_shift": 0,
                    "max_per_shift": 1,
                    "can_be_sole_charge": False,
                    "must_have_supervisor": False
                }
            }
        ]
        
        created_constraints = []
        for constraint_def in default_constraints:
            constraint = self.create_role_constraint(
                constraint_def["role"], ward_id, constraint_def["data"]
            )
            created_constraints.append(constraint)
        
        return created_constraints
    
    def create_default_employment_rules(self, ward_id: int) -> List[EmploymentTypeRule]:
        """기본 고용형태별 규칙 생성"""
        default_rules = [
            {
                "employment_type": "full_time",
                "data": {
                    "max_hours_per_day": 8,
                    "max_hours_per_week": 40,
                    "max_days_per_week": 5,
                    "max_consecutive_days": 5,
                    "allowed_shift_types": ["day", "evening", "night"],
                    "weekend_work_allowed": True,
                    "night_shift_allowed": True,
                    "scheduling_priority": 3
                }
            },
            {
                "employment_type": "part_time",
                "data": {
                    "max_hours_per_day": 6,
                    "max_hours_per_week": 24,
                    "max_days_per_week": 4,
                    "max_consecutive_days": 3,
                    "allowed_shift_types": ["day", "evening"],
                    "forbidden_shift_types": ["night"],
                    "weekend_work_allowed": False,
                    "night_shift_allowed": False,
                    "scheduling_priority": 7
                }
            }
        ]
        
        created_rules = []
        for rule_def in default_rules:
            rule = self.create_employment_type_rule(
                rule_def["employment_type"], ward_id, rule_def["data"]
            )
            created_rules.append(rule)
        
        return created_rules
    
    def get_role_assignment_summary(self, schedule: Schedule) -> Dict[str, Any]:
        """역할별 배치 현황 요약"""
        schedule_data = schedule.schedule_data
        if not schedule_data:
            return {"error": "스케줄 데이터가 없습니다"}
        
        summary = {
            "total_employees": len(schedule_data),
            "role_distribution": defaultdict(int),
            "employment_type_distribution": defaultdict(int),
            "supervision_pairs": 0,
            "violations_count": 0,
            "compliance_rate": 0.0
        }
        
        # 직원별 역할 및 고용형태 분포
        for emp_id_str in schedule_data.keys():
            employee = self.db.query(Employee).filter(
                Employee.id == int(emp_id_str)
            ).first()
            if employee:
                summary["role_distribution"][employee.role] += 1
                summary["employment_type_distribution"][employee.employment_type] += 1
        
        # 감독 페어 수 계산
        summary["supervision_pairs"] = self.db.query(SupervisionPair).filter(
            SupervisionPair.is_active == True
        ).count()
        
        # 위반사항 검증
        is_valid, violations = self.validate_role_assignments(schedule)
        summary["violations_count"] = len(violations)
        summary["compliance_rate"] = 100.0 if is_valid else max(0, 100 - len(violations) * 5)
        
        return summary