"""
수동 편집 관련 엔티티 및 타입 정의
Single Responsibility: 수동 편집 도메인의 기본 타입들 정의
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from dataclasses import dataclass


class ValidationSeverity(Enum):
    """검증 위반 심각도"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChangeType(Enum):
    """변경 타입"""
    EMPLOYEE_CHANGE = "employee_change"
    SHIFT_TYPE_CHANGE = "shift_type_change"
    DATE_CHANGE = "date_change"
    EMERGENCY_OVERRIDE = "emergency_override"


class OverrideReason(Enum):
    """오버라이드 사유"""
    EMERGENCY = "emergency"
    MEDICAL_LEAVE = "medical_leave"
    FAMILY_EMERGENCY = "family_emergency"
    SYSTEM_ERROR = "system_error"
    ADMIN_REQUEST = "admin_request"


@dataclass
class ValidationResult:
    """검증 결과"""
    valid: bool
    warnings: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    pattern_score: float
    recommendations: List[str]
    error: Optional[str] = None

    def has_critical_violations(self) -> bool:
        """중요한 위반사항이 있는지 확인"""
        return any(v.get('severity') == ValidationSeverity.CRITICAL.value for v in self.violations)

    def has_high_violations(self) -> bool:
        """높은 심각도 위반사항이 있는지 확인"""
        return any(v.get('severity') == ValidationSeverity.HIGH.value for v in self.violations)


@dataclass
class ChangeRequest:
    """변경 요청"""
    assignment_id: int
    new_employee_id: Optional[int] = None
    new_shift_type: Optional[str] = None
    new_shift_date: Optional[date] = None
    override: bool = False
    override_reason: Optional[str] = None
    admin_id: Optional[int] = None
    change_type: Optional[ChangeType] = None

    def __post_init__(self):
        """변경 타입 자동 설정"""
        if self.change_type is None:
            if self.new_employee_id:
                self.change_type = ChangeType.EMPLOYEE_CHANGE
            elif self.new_shift_type:
                self.change_type = ChangeType.SHIFT_TYPE_CHANGE
            elif self.new_shift_date:
                self.change_type = ChangeType.DATE_CHANGE
            elif self.override:
                self.change_type = ChangeType.EMERGENCY_OVERRIDE


@dataclass
class ChangeResult:
    """변경 결과"""
    success: bool
    message: str
    assignment_id: Optional[int] = None
    validation_result: Optional[ValidationResult] = None
    audit_log_id: Optional[int] = None
    notifications_sent: List[int] = None

    def __post_init__(self):
        if self.notifications_sent is None:
            self.notifications_sent = []


@dataclass
class ShiftAssignmentData:
    """근무 배정 데이터"""
    id: int
    employee_id: int
    shift_date: date
    shift_type: str
    schedule_id: int
    ward_id: int


@dataclass
class EmployeeConstraints:
    """직원 제약조건"""
    employee_id: int
    role: str
    employment_type: str
    max_hours_per_week: int
    max_hours_per_month: int
    forbidden_shifts: List[str]
    preferred_shifts: List[str]
    availability: Dict[str, List[str]]  # 요일별 가능 시간


@dataclass
class PatternValidationData:
    """패턴 검증용 데이터"""
    employee_id: int
    assignments: List[Dict[str, Any]]
    start_date: datetime
    end_date: datetime


class ValidationContext:
    """검증 컨텍스트"""

    def __init__(self,
                 assignment_data: ShiftAssignmentData,
                 employee_constraints: EmployeeConstraints,
                 ward_rules: Dict[str, Any],
                 current_week_assignments: List[ShiftAssignmentData],
                 current_month_assignments: List[ShiftAssignmentData]):
        self.assignment_data = assignment_data
        self.employee_constraints = employee_constraints
        self.ward_rules = ward_rules
        self.current_week_assignments = current_week_assignments
        self.current_month_assignments = current_month_assignments

    def get_total_week_hours(self) -> int:
        """주간 총 근무시간 계산"""
        from ..utils.shift_calculator import ShiftCalculator
        calculator = ShiftCalculator()
        return sum(calculator.get_shift_hours(a.shift_type)
                  for a in self.current_week_assignments)

    def get_total_month_hours(self) -> int:
        """월간 총 근무시간 계산"""
        from ..utils.shift_calculator import ShiftCalculator
        calculator = ShiftCalculator()
        return sum(calculator.get_shift_hours(a.shift_type)
                  for a in self.current_month_assignments)


class NotificationData:
    """알림 데이터"""

    def __init__(self,
                 change_type: ChangeType,
                 assignment_id: int,
                 affected_employees: List[int],
                 ward_id: int,
                 change_details: Dict[str, Any]):
        self.change_type = change_type
        self.assignment_id = assignment_id
        self.affected_employees = affected_employees
        self.ward_id = ward_id
        self.change_details = change_details
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'change_type': self.change_type.value,
            'assignment_id': self.assignment_id,
            'affected_employees': self.affected_employees,
            'ward_id': self.ward_id,
            'change_details': self.change_details,
            'timestamp': self.timestamp.isoformat()
        }