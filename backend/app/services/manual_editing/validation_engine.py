"""
검증 엔진
Single Responsibility: 근무 변경 전 유효성 검증만 담당
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from .entities import (
    ValidationResult, ValidationSeverity, ChangeRequest,
    ShiftAssignmentData, EmployeeConstraints, ValidationContext
)
from .utils.shift_calculator import ShiftCalculator
from app.models.models import (
    Employee, Ward, ShiftRule,
    PreferenceTemplate, RoleConstraint, EmploymentTypeRule
)
from app.models.scheduling_models import ShiftAssignment
from app.services.pattern_validation_service import PatternValidationService
import logging

logger = logging.getLogger(__name__)


class ValidationEngine:
    """근무 변경 유효성 검증 엔진"""

    def __init__(self):
        self.shift_calculator = ShiftCalculator()
        self.pattern_service = PatternValidationService()

        # 검증 규칙들
        self.validators = [
            self._validate_employee_existence,
            self._validate_employment_type_rules,
            self._validate_role_constraints,
            self._validate_working_hours,
            self._validate_shift_patterns,
            self._validate_ward_coverage
        ]

    def validate_shift_change(self, db: Session, change_request: ChangeRequest) -> ValidationResult:
        """근무 변경 전 종합 유효성 검증"""
        try:
            # 현재 배정 정보 조회
            current_assignment = db.query(ShiftAssignment).filter(
                ShiftAssignment.id == change_request.assignment_id
            ).first()

            if not current_assignment:
                return ValidationResult(
                    valid=False,
                    warnings=[],
                    errors=[],
                    violations=[],
                    pattern_score=0.0,
                    recommendations=[],
                    error='해당 근무 배정을 찾을 수 없습니다'
                )

            # 검증 컨텍스트 구성
            context = self._build_validation_context(db, current_assignment, change_request)

            # 모든 검증 실행
            all_violations = []
            for validator in self.validators:
                violations = validator(db, context, change_request)
                all_violations.extend(violations)

            # 위반사항 분류
            warnings = [v for v in all_violations if v['severity'] in ['medium', 'low']]
            errors = [v for v in all_violations if v['severity'] in ['critical', 'high']]

            # 패턴 점수 계산
            pattern_score = self._calculate_pattern_score(db, context, change_request)

            # 추천사항 생성
            recommendations = self._generate_recommendations(context, all_violations)

            return ValidationResult(
                valid=len(errors) == 0,
                warnings=warnings,
                errors=errors,
                violations=all_violations,
                pattern_score=pattern_score,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"근무 변경 검증 중 오류 발생 - assignment_id: {change_request.assignment_id}, error: {str(e)}")
            return ValidationResult(
                valid=False,
                warnings=[],
                errors=[],
                violations=[],
                pattern_score=0.0,
                recommendations=[],
                error=f'검증 중 시스템 오류: {str(e)}'
            )

    def _build_validation_context(self, db: Session,
                                current_assignment: ShiftAssignment,
                                change_request: ChangeRequest) -> ValidationContext:
        """검증 컨텍스트 구성"""

        # 대상 직원 ID 설정
        target_employee_id = change_request.new_employee_id or current_assignment.employee_id
        target_date = change_request.new_shift_date or current_assignment.shift_date
        target_shift_type = change_request.new_shift_type or current_assignment.shift_type

        # 직원 정보 조회
        employee = db.query(Employee).filter(Employee.id == target_employee_id).first()
        if not employee:
            raise ValueError(f"직원 ID {target_employee_id}를 찾을 수 없습니다")

        # 근무 배정 데이터 구성
        assignment_data = ShiftAssignmentData(
            id=current_assignment.id,
            employee_id=target_employee_id,
            shift_date=target_date,
            shift_type=target_shift_type,
            schedule_id=current_assignment.schedule_id,
            ward_id=current_assignment.ward_id
        )

        # 직원 제약조건 구성
        employee_constraints = self._get_employee_constraints(db, employee)

        # 병동 규칙 조회
        ward_rules = self._get_ward_rules(db, current_assignment.ward_id)

        # 주간/월간 근무 배정 조회
        week_assignments = self._get_week_assignments(db, target_employee_id, target_date)
        month_assignments = self._get_month_assignments(db, target_employee_id, target_date)

        return ValidationContext(
            assignment_data=assignment_data,
            employee_constraints=employee_constraints,
            ward_rules=ward_rules,
            current_week_assignments=week_assignments,
            current_month_assignments=month_assignments
        )

    def _validate_employee_existence(self, db: Session, context: ValidationContext,
                                   change_request: ChangeRequest) -> List[Dict[str, Any]]:
        """직원 존재 여부 검증"""
        violations = []

        if change_request.new_employee_id:
            employee = db.query(Employee).filter(
                Employee.id == change_request.new_employee_id,
                Employee.is_active == True
            ).first()

            if not employee:
                violations.append({
                    'type': 'employee_not_found',
                    'severity': ValidationSeverity.CRITICAL.value,
                    'message': f'직원 ID {change_request.new_employee_id}를 찾을 수 없거나 비활성 상태입니다'
                })

        return violations

    def _validate_employment_type_rules(self, db: Session, context: ValidationContext,
                                      change_request: ChangeRequest) -> List[Dict[str, Any]]:
        """고용 형태별 규칙 검증"""
        violations = []

        employment_rules = db.query(EmploymentTypeRule).filter(
            EmploymentTypeRule.employment_type == context.employee_constraints.employment_type,
            EmploymentTypeRule.is_active == True
        ).first()

        if employment_rules:
            target_shift = change_request.new_shift_type or context.assignment_data.shift_type

            if target_shift in (employment_rules.forbidden_shifts or []):
                violations.append({
                    'type': 'employment_type_rule',
                    'severity': ValidationSeverity.HIGH.value,
                    'message': f'{context.employee_constraints.employment_type} 직원은 {target_shift} 근무에 배정될 수 없습니다'
                })

        return violations

    def _validate_role_constraints(self, db: Session, context: ValidationContext,
                                 change_request: ChangeRequest) -> List[Dict[str, Any]]:
        """역할별 제약조건 검증"""
        violations = []

        role_constraints = db.query(RoleConstraint).filter(
            RoleConstraint.role == context.employee_constraints.role,
            RoleConstraint.is_active == True
        ).first()

        if role_constraints:
            target_shift = change_request.new_shift_type or context.assignment_data.shift_type

            if target_shift in (role_constraints.forbidden_shifts or []):
                violations.append({
                    'type': 'role_constraint',
                    'severity': ValidationSeverity.HIGH.value,
                    'message': f'{context.employee_constraints.role} 역할은 {target_shift} 근무에 배정될 수 없습니다'
                })

        return violations

    def _validate_working_hours(self, db: Session, context: ValidationContext,
                              change_request: ChangeRequest) -> List[Dict[str, Any]]:
        """근무 시간 한도 검증"""
        violations = []

        target_shift = change_request.new_shift_type or context.assignment_data.shift_type
        shift_hours = self.shift_calculator.get_shift_hours(target_shift)

        # 주간 근무시간 검증
        total_week_hours = context.get_total_week_hours()
        if total_week_hours + shift_hours > context.employee_constraints.max_hours_per_week:
            violations.append({
                'type': 'weekly_hours_exceeded',
                'severity': ValidationSeverity.MEDIUM.value,
                'message': f'주간 근무시간 한도 초과 ({total_week_hours + shift_hours}/{context.employee_constraints.max_hours_per_week}시간)'
            })

        # 월간 근무시간 검증
        total_month_hours = context.get_total_month_hours()
        if total_month_hours + shift_hours > context.employee_constraints.max_hours_per_month:
            violations.append({
                'type': 'monthly_hours_exceeded',
                'severity': ValidationSeverity.MEDIUM.value,
                'message': f'월간 근무시간 한도 초과 ({total_month_hours + shift_hours}/{context.employee_constraints.max_hours_per_month}시간)'
            })

        return violations

    def _validate_shift_patterns(self, db: Session, context: ValidationContext,
                               change_request: ChangeRequest) -> List[Dict[str, Any]]:
        """근무 패턴 검증"""
        violations = []

        try:
            # 시뮬레이션된 배정으로 패턴 검증
            employee_assignments = self._get_employee_assignments(
                db, context.assignment_data.employee_id, context.assignment_data.schedule_id
            )

            simulated_assignments = []
            for assignment in employee_assignments:
                if assignment.id == change_request.assignment_id:
                    # 변경될 배정
                    simulated_assignments.append({
                        'shift_date': context.assignment_data.shift_date.strftime('%Y-%m-%d'),
                        'shift_type': context.assignment_data.shift_type,
                        'assignment_id': assignment.id
                    })
                else:
                    simulated_assignments.append({
                        'shift_date': assignment.shift_date.strftime('%Y-%m-%d'),
                        'shift_type': assignment.shift_type,
                        'assignment_id': assignment.id
                    })

            pattern_result = self.pattern_service.validate_employee_pattern(
                db, context.assignment_data.employee_id, simulated_assignments,
                datetime.now() - timedelta(days=30),
                datetime.now() + timedelta(days=30)
            )

            for violation in pattern_result.get('violations', []):
                violations.append({
                    'type': 'pattern_violation',
                    'severity': violation.get('severity', ValidationSeverity.MEDIUM.value),
                    'message': violation.get('description', '패턴 위반')
                })

        except Exception as e:
            logger.warning(f"패턴 검증 중 오류: {str(e)}")
            violations.append({
                'type': 'pattern_validation_error',
                'severity': ValidationSeverity.LOW.value,
                'message': '패턴 검증 중 오류가 발생했습니다'
            })

        return violations

    def _validate_ward_coverage(self, db: Session, context: ValidationContext,
                              change_request: ChangeRequest) -> List[Dict[str, Any]]:
        """병동 커버리지 검증"""
        violations = []

        # 병동 최소 인원 규칙 검증
        min_nurses = context.ward_rules.get('min_nurses_per_shift', 3)

        # 해당 날짜/교대의 현재 배정 수 확인
        target_date = change_request.new_shift_date or context.assignment_data.shift_date
        target_shift = change_request.new_shift_type or context.assignment_data.shift_type

        current_assignments = db.query(ShiftAssignment).filter(
            ShiftAssignment.ward_id == context.assignment_data.ward_id,
            ShiftAssignment.shift_date == target_date,
            ShiftAssignment.shift_type == target_shift
        ).count()

        if current_assignments < min_nurses:
            violations.append({
                'type': 'insufficient_coverage',
                'severity': ValidationSeverity.HIGH.value,
                'message': f'병동 최소 인원 부족 ({current_assignments}/{min_nurses}명)'
            })

        return violations

    def _get_employee_constraints(self, db: Session, employee: Employee) -> EmployeeConstraints:
        """직원 제약조건 조회"""
        return EmployeeConstraints(
            employee_id=employee.id,
            role=employee.role,
            employment_type=employee.employment_type,
            max_hours_per_week=getattr(employee, 'max_hours_per_week', 40),
            max_hours_per_month=getattr(employee, 'max_hours_per_month', 160),
            forbidden_shifts=[],
            preferred_shifts=[],
            availability={}
        )

    def _get_ward_rules(self, db: Session, ward_id: int) -> Dict[str, Any]:
        """병동 규칙 조회"""
        ward = db.query(Ward).filter(Ward.id == ward_id).first()
        if ward:
            return {
                'min_nurses_per_shift': getattr(ward, 'min_nurses_per_shift', 3),
                'max_nurses_per_shift': getattr(ward, 'max_nurses_per_shift', 10)
            }
        return {'min_nurses_per_shift': 3, 'max_nurses_per_shift': 10}

    def _get_week_assignments(self, db: Session, employee_id: int, target_date: date) -> List[ShiftAssignmentData]:
        """주간 근무 배정 조회"""
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        assignments = db.query(ShiftAssignment).filter(
            ShiftAssignment.employee_id == employee_id,
            ShiftAssignment.shift_date >= start_of_week,
            ShiftAssignment.shift_date <= end_of_week
        ).all()

        return [ShiftAssignmentData(
            id=a.id,
            employee_id=a.employee_id,
            shift_date=a.shift_date,
            shift_type=a.shift_type,
            schedule_id=a.schedule_id,
            ward_id=a.ward_id
        ) for a in assignments]

    def _get_month_assignments(self, db: Session, employee_id: int, target_date: date) -> List[ShiftAssignmentData]:
        """월간 근무 배정 조회"""
        start_of_month = target_date.replace(day=1)
        if target_date.month == 12:
            end_of_month = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)

        assignments = db.query(ShiftAssignment).filter(
            ShiftAssignment.employee_id == employee_id,
            ShiftAssignment.shift_date >= start_of_month,
            ShiftAssignment.shift_date <= end_of_month
        ).all()

        return [ShiftAssignmentData(
            id=a.id,
            employee_id=a.employee_id,
            shift_date=a.shift_date,
            shift_type=a.shift_type,
            schedule_id=a.schedule_id,
            ward_id=a.ward_id
        ) for a in assignments]

    def _get_employee_assignments(self, db: Session, employee_id: int, schedule_id: int) -> List[ShiftAssignment]:
        """직원의 스케줄 내 모든 배정 조회"""
        return db.query(ShiftAssignment).filter(
            ShiftAssignment.employee_id == employee_id,
            ShiftAssignment.schedule_id == schedule_id
        ).all()

    def _calculate_pattern_score(self, db: Session, context: ValidationContext,
                               change_request: ChangeRequest) -> float:
        """패턴 점수 계산"""
        try:
            # 패턴 서비스를 통한 점수 계산 (구현 필요)
            return 85.0  # 임시 점수
        except:
            return 100.0

    def _generate_recommendations(self, context: ValidationContext,
                                violations: List[Dict[str, Any]]) -> List[str]:
        """추천사항 생성"""
        recommendations = []

        if any(v['type'] == 'weekly_hours_exceeded' for v in violations):
            recommendations.append("주간 근무시간을 줄이기 위해 다른 교대로 변경을 고려하세요")

        if any(v['type'] == 'insufficient_coverage' for v in violations):
            recommendations.append("병동 커버리지를 위해 추가 간호사 배정을 검토하세요")

        if any(v['type'] == 'pattern_violation' for v in violations):
            recommendations.append("근무 패턴 개선을 위해 연속 근무일을 조정하세요")

        return recommendations