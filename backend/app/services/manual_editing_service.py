from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.models import (
    Employee, ShiftAssignment, Schedule, Ward, ShiftRule, 
    PreferenceTemplate, RoleConstraint, EmploymentTypeRule
)
from app.services.compliance_service import ComplianceService
from app.services.pattern_validation_service import PatternValidationService
from app.services.role_assignment_service import RoleAssignmentService
import logging

logger = logging.getLogger(__name__)

class ManualEditingService:
    """수동 편집 및 응급 오버라이드 서비스"""
    
    def __init__(self):
        self.compliance_service = ComplianceService()
        self.pattern_service = PatternValidationService()
        self.role_service = RoleAssignmentService()
    
    def validate_shift_change(
        self, 
        db: Session, 
        assignment_id: int, 
        new_employee_id: Optional[int] = None,
        new_shift_type: Optional[str] = None,
        new_shift_date: Optional[date] = None
    ) -> Dict:
        """근무 변경 전 유효성 검증"""
        try:
            # 현재 배정 정보 조회
            current_assignment = db.query(ShiftAssignment).filter(
                ShiftAssignment.id == assignment_id
            ).first()
            
            if not current_assignment:
                return {
                    'valid': False,
                    'error': '해당 근무 배정을 찾을 수 없습니다',
                    'violations': []
                }
            
            # 변경 대상 설정
            target_employee_id = new_employee_id or current_assignment.employee_id
            target_shift_type = new_shift_type or current_assignment.shift_type
            target_date = new_shift_date or current_assignment.shift_date.date()
            
            violations = []
            
            # 1. 직원 존재 및 활성 상태 확인
            employee = db.query(Employee).filter(
                Employee.id == target_employee_id,
                Employee.is_active == True
            ).first()
            
            if not employee:
                violations.append({
                    'type': 'employee_not_found',
                    'severity': 'critical',
                    'message': f'직원 ID {target_employee_id}를 찾을 수 없거나 비활성 상태입니다'
                })
                return {'valid': False, 'error': '직원을 찾을 수 없습니다', 'violations': violations}
            
            # 2. 중복 배정 확인
            duplicate_assignment = db.query(ShiftAssignment).filter(
                and_(
                    ShiftAssignment.employee_id == target_employee_id,
                    ShiftAssignment.shift_date == target_date,
                    ShiftAssignment.shift_type == target_shift_type,
                    ShiftAssignment.id != assignment_id,
                    ShiftAssignment.schedule_id == current_assignment.schedule_id
                )
            ).first()
            
            if duplicate_assignment:
                violations.append({
                    'type': 'duplicate_assignment',
                    'severity': 'critical',
                    'message': f'{employee.user.full_name}은 이미 {target_date} {target_shift_type} 근무에 배정되어 있습니다'
                })
            
            # 3. 고용 형태별 제약조건 확인
            employment_rules = db.query(EmploymentTypeRule).filter(
                EmploymentTypeRule.employment_type == employee.employment_type,
                EmploymentTypeRule.is_active == True
            ).first()
            
            if employment_rules:
                if target_shift_type not in (employment_rules.allowed_shift_types or []):
                    violations.append({
                        'type': 'employment_constraint',
                        'severity': 'high',
                        'message': f'{employee.employment_type} 직원은 {target_shift_type} 근무에 배정될 수 없습니다'
                    })
            
            # 4. 역할별 제약조건 확인
            role_constraints = db.query(RoleConstraint).filter(
                RoleConstraint.role == employee.role,
                RoleConstraint.is_active == True
            ).first()
            
            if role_constraints:
                if target_shift_type in (role_constraints.forbidden_shifts or []):
                    violations.append({
                        'type': 'role_constraint',
                        'severity': 'high',
                        'message': f'{employee.role} 역할은 {target_shift_type} 근무에 배정될 수 없습니다'
                    })
            
            # 5. 주간/월간 근무 시간 한도 확인
            current_week_assignments = self._get_week_assignments(db, target_employee_id, target_date)
            current_month_assignments = self._get_month_assignments(db, target_employee_id, target_date)
            
            total_week_hours = sum([self._get_shift_hours(a.shift_type) for a in current_week_assignments])
            total_month_hours = sum([self._get_shift_hours(a.shift_type) for a in current_month_assignments])
            
            shift_hours = self._get_shift_hours(target_shift_type)
            
            if total_week_hours + shift_hours > employee.max_hours_per_week:
                violations.append({
                    'type': 'weekly_hours_exceeded',
                    'severity': 'medium',
                    'message': f'주간 근무시간 한도 초과 ({total_week_hours + shift_hours}/{employee.max_hours_per_week}시간)'
                })
            
            # 6. 패턴 검증
            employee_assignments = self._get_employee_assignments(db, target_employee_id, current_assignment.schedule_id)
            
            # 현재 변경사항을 시뮬레이션하여 패턴 검증
            simulated_assignments = []
            for assignment in employee_assignments:
                if assignment.id == assignment_id:
                    # 변경될 배정
                    simulated_assignments.append({
                        'shift_date': target_date.strftime('%Y-%m-%d'),
                        'shift_type': target_shift_type,
                        'assignment_id': assignment.id
                    })
                else:
                    simulated_assignments.append({
                        'shift_date': assignment.shift_date.strftime('%Y-%m-%d'),
                        'shift_type': assignment.shift_type,
                        'assignment_id': assignment.id
                    })
            
            pattern_result = self.pattern_service.validate_employee_pattern(
                db, target_employee_id, simulated_assignments,
                datetime.now() - timedelta(days=30),
                datetime.now() + timedelta(days=30)
            )
            
            for violation in pattern_result.get('violations', []):
                violations.append({
                    'type': 'pattern_violation',
                    'severity': violation.get('severity', 'medium'),
                    'message': violation.get('description', '패턴 위반')
                })
            
            # 검증 결과 반환
            has_critical = any(v['severity'] == 'critical' for v in violations)
            has_high = any(v['severity'] == 'high' for v in violations)
            
            return {
                'valid': not has_critical,
                'warnings': [v for v in violations if v['severity'] in ['medium', 'low']],
                'errors': [v for v in violations if v['severity'] in ['critical', 'high']],
                'violations': violations,
                'pattern_score': pattern_result.get('pattern_score', 100),
                'recommendations': pattern_result.get('recommendations', [])
            }
            
        except Exception as e:
            logger.error(f"근무 변경 검증 중 오류 발생 - assignment_id: {assignment_id}, error: {str(e)}")
            return {
                'valid': False,
                'error': f'검증 중 시스템 오류: {str(e)}',
                'violations': []
            }
    
    def apply_shift_change(
        self, 
        db: Session, 
        assignment_id: int,
        new_employee_id: Optional[int] = None,
        new_shift_type: Optional[str] = None,
        new_shift_date: Optional[date] = None,
        override: bool = False,
        override_reason: Optional[str] = None,
        admin_id: Optional[int] = None
    ) -> Dict:
        """근무 변경 적용"""
        try:
            # 검증 수행 (오버라이드가 아닌 경우)
            if not override:
                validation_result = self.validate_shift_change(
                    db, assignment_id, new_employee_id, new_shift_type, new_shift_date
                )
                
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'error': '변경사항이 유효성 검증을 통과하지 못했습니다',
                        'validation_result': validation_result
                    }
            
            # 현재 배정 조회
            assignment = db.query(ShiftAssignment).filter(
                ShiftAssignment.id == assignment_id
            ).first()
            
            if not assignment:
                return {
                    'success': False,
                    'error': '해당 근무 배정을 찾을 수 없습니다'
                }
            
            # 변경 전 정보 저장
            original_data = {
                'employee_id': assignment.employee_id,
                'shift_type': assignment.shift_type,
                'shift_date': assignment.shift_date
            }
            
            # 변경사항 적용
            if new_employee_id:
                assignment.employee_id = new_employee_id
            if new_shift_type:
                assignment.shift_type = new_shift_type
            if new_shift_date:
                assignment.shift_date = datetime.combine(new_shift_date, datetime.min.time())
            
            # 오버라이드 정보 기록
            if override:
                assignment.is_override = True
                assignment.override_reason = override_reason
                assignment.override_by = admin_id
                assignment.override_at = datetime.utcnow()
            
            assignment.last_modified = datetime.utcnow()
            assignment.modified_by = admin_id
            
            db.commit()
            
            # 변경 후 스케줄 점수 재계산
            new_score = self._recalculate_schedule_score(db, assignment.schedule_id)
            
            return {
                'success': True,
                'message': '근무 변경이 성공적으로 적용되었습니다',
                'original_data': original_data,
                'new_data': {
                    'employee_id': assignment.employee_id,
                    'shift_type': assignment.shift_type,
                    'shift_date': assignment.shift_date.date()
                },
                'is_override': override,
                'new_schedule_score': new_score
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"근무 변경 적용 중 오류 발생 - assignment_id: {assignment_id}, error: {str(e)}")
            return {
                'success': False,
                'error': f'변경 적용 중 오류 발생: {str(e)}'
            }
    
    def get_replacement_suggestions(
        self, 
        db: Session, 
        assignment_id: int,
        emergency: bool = False,
        max_suggestions: int = 5
    ) -> List[Dict]:
        """대체 근무자 추천"""
        try:
            # 현재 배정 정보 조회
            current_assignment = db.query(ShiftAssignment).filter(
                ShiftAssignment.id == assignment_id
            ).first()
            
            if not current_assignment:
                return []
            
            target_date = current_assignment.shift_date.date()
            target_shift = current_assignment.shift_type
            ward_id = current_assignment.schedule.ward_id
            
            # 후보 직원들 조회
            candidates = db.query(Employee).filter(
                Employee.ward_id == ward_id,
                Employee.is_active == True,
                Employee.id != current_assignment.employee_id
            ).all()
            
            suggestions = []
            
            for candidate in candidates:
                # 기본 적합성 검사
                suitability = self._evaluate_replacement_suitability(
                    db, candidate, target_date, target_shift, emergency
                )
                
                if suitability['score'] > 0:  # 0점 이상인 경우만 추천
                    suggestions.append({
                        'employee_id': candidate.id,
                        'employee_name': candidate.user.full_name,
                        'role': candidate.role,
                        'employment_type': candidate.employment_type,
                        'skill_level': candidate.skill_level,
                        'years_experience': candidate.years_experience,
                        'suitability_score': suitability['score'],
                        'suitability_reasons': suitability['reasons'],
                        'warnings': suitability['warnings'],
                        'availability_status': suitability['availability']
                    })
            
            # 적합도 순으로 정렬하고 상위 N개 반환
            suggestions.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"대체자 추천 중 오류 발생 - assignment_id: {assignment_id}, error: {str(e)}")
            return []
    
    def emergency_reassignment(
        self, 
        db: Session, 
        assignment_id: int,
        replacement_employee_id: int,
        emergency_reason: str,
        admin_id: int,
        notify_affected: bool = True
    ) -> Dict:
        """응급 근무 재배치"""
        try:
            # 현재 배정 정보 확인
            original_assignment = db.query(ShiftAssignment).filter(
                ShiftAssignment.id == assignment_id
            ).first()
            
            if not original_assignment:
                return {
                    'success': False,
                    'error': '원본 근무 배정을 찾을 수 없습니다'
                }
            
            # 대체 직원 확인
            replacement_employee = db.query(Employee).filter(
                Employee.id == replacement_employee_id,
                Employee.is_active == True
            ).first()
            
            if not replacement_employee:
                return {
                    'success': False,
                    'error': '대체 직원을 찾을 수 없습니다'
                }
            
            # 응급 상황에서는 기본적인 제약조건만 확인
            basic_validation = self._emergency_validation(
                db, replacement_employee_id, 
                original_assignment.shift_date.date(),
                original_assignment.shift_type
            )
            
            if not basic_validation['valid']:
                return {
                    'success': False,
                    'error': '대체 직원이 기본 요구사항을 충족하지 않습니다',
                    'details': basic_validation['errors']
                }
            
            # 응급 재배치 실행 (강제 오버라이드)
            result = self.apply_shift_change(
                db=db,
                assignment_id=assignment_id,
                new_employee_id=replacement_employee_id,
                override=True,
                override_reason=f"응급 재배치: {emergency_reason}",
                admin_id=admin_id
            )
            
            if result['success']:
                # 응급 로그 기록
                self._log_emergency_action(
                    db, assignment_id, original_assignment.employee_id,
                    replacement_employee_id, emergency_reason, admin_id
                )
                
                # 알림 발송 (선택적)
                if notify_affected:
                    affected_employees = [original_assignment.employee_id, replacement_employee_id]
                    self._queue_emergency_notifications(
                        db, affected_employees, original_assignment, emergency_reason
                    )
                
                result['emergency_log_created'] = True
                result['notifications_queued'] = notify_affected
            
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"응급 재배치 중 오류 발생 - assignment_id: {assignment_id}, error: {str(e)}")
            return {
                'success': False,
                'error': f'응급 재배치 중 오류 발생: {str(e)}'
            }
    
    def bulk_shift_swap(
        self, 
        db: Session, 
        swap_pairs: List[Tuple[int, int]],  # [(assignment_id_1, assignment_id_2), ...]
        admin_id: int,
        validation_level: str = 'standard'  # 'strict', 'standard', 'minimal'
    ) -> Dict:
        """일괄 근무 교환"""
        try:
            results = []
            total_swaps = len(swap_pairs)
            successful_swaps = 0
            
            for assignment_id_1, assignment_id_2 in swap_pairs:
                # 두 배정 정보 조회
                assignment_1 = db.query(ShiftAssignment).filter(
                    ShiftAssignment.id == assignment_id_1
                ).first()
                assignment_2 = db.query(ShiftAssignment).filter(
                    ShiftAssignment.id == assignment_id_2
                ).first()
                
                if not assignment_1 or not assignment_2:
                    results.append({
                        'pair': (assignment_id_1, assignment_id_2),
                        'success': False,
                        'error': '배정 정보를 찾을 수 없습니다'
                    })
                    continue
                
                # 교환 가능성 검증
                if validation_level == 'strict':
                    validation_1 = self.validate_shift_change(
                        db, assignment_id_1, assignment_2.employee_id
                    )
                    validation_2 = self.validate_shift_change(
                        db, assignment_id_2, assignment_1.employee_id
                    )
                    
                    if not (validation_1['valid'] and validation_2['valid']):
                        results.append({
                            'pair': (assignment_id_1, assignment_id_2),
                            'success': False,
                            'error': '교환이 유효성 검증을 통과하지 못했습니다',
                            'validation_errors': {
                                'assignment_1': validation_1.get('errors', []),
                                'assignment_2': validation_2.get('errors', [])
                            }
                        })
                        continue
                
                # 교환 실행
                try:
                    # 직원 ID 교환
                    temp_employee_id = assignment_1.employee_id
                    assignment_1.employee_id = assignment_2.employee_id
                    assignment_2.employee_id = temp_employee_id
                    
                    # 메타데이터 업데이트
                    assignment_1.last_modified = datetime.utcnow()
                    assignment_1.modified_by = admin_id
                    assignment_2.last_modified = datetime.utcnow()
                    assignment_2.modified_by = admin_id
                    
                    db.commit()
                    
                    results.append({
                        'pair': (assignment_id_1, assignment_id_2),
                        'success': True,
                        'swapped_employees': {
                            'assignment_1': assignment_1.employee_id,
                            'assignment_2': assignment_2.employee_id
                        }
                    })
                    successful_swaps += 1
                    
                except Exception as e:
                    db.rollback()
                    results.append({
                        'pair': (assignment_id_1, assignment_id_2),
                        'success': False,
                        'error': f'교환 실행 중 오류: {str(e)}'
                    })
            
            return {
                'success': successful_swaps > 0,
                'total_pairs': total_swaps,
                'successful_swaps': successful_swaps,
                'failed_swaps': total_swaps - successful_swaps,
                'results': results
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"일괄 근무 교환 중 오류 발생 - error: {str(e)}")
            return {
                'success': False,
                'error': f'일괄 교환 중 오류 발생: {str(e)}'
            }
    
    # 헬퍼 메서드들
    
    def _get_week_assignments(self, db: Session, employee_id: int, target_date: date) -> List:
        """해당 주의 근무 배정 조회"""
        week_start = target_date - timedelta(days=target_date.weekday())
        week_end = week_start + timedelta(days=6)
        
        return db.query(ShiftAssignment).filter(
            and_(
                ShiftAssignment.employee_id == employee_id,
                ShiftAssignment.shift_date >= week_start,
                ShiftAssignment.shift_date <= week_end
            )
        ).all()
    
    def _get_month_assignments(self, db: Session, employee_id: int, target_date: date) -> List:
        """해당 월의 근무 배정 조회"""
        month_start = target_date.replace(day=1)
        next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
        month_end = next_month - timedelta(days=1)
        
        return db.query(ShiftAssignment).filter(
            and_(
                ShiftAssignment.employee_id == employee_id,
                ShiftAssignment.shift_date >= month_start,
                ShiftAssignment.shift_date <= month_end
            )
        ).all()
    
    def _get_employee_assignments(self, db: Session, employee_id: int, schedule_id: int) -> List:
        """직원의 특정 스케줄 내 모든 배정 조회"""
        return db.query(ShiftAssignment).filter(
            and_(
                ShiftAssignment.employee_id == employee_id,
                ShiftAssignment.schedule_id == schedule_id
            )
        ).all()
    
    def _get_shift_hours(self, shift_type: str) -> int:
        """근무 유형별 시간 반환"""
        shift_hours = {
            'day': 8,
            'evening': 8,
            'night': 8,
            'long_day': 12,
            'half_day': 4
        }
        return shift_hours.get(shift_type, 8)
    
    def _recalculate_schedule_score(self, db: Session, schedule_id: int) -> float:
        """스케줄의 전체 최적화 점수 재계산"""
        try:
            # 기본 점수부터 시작
            base_score = 100.0
            
            # 컴플라이언스 점수
            compliance_result = self.compliance_service.validate_schedule_compliance(db, schedule_id)
            compliance_penalty = compliance_result.get('total_penalty', 0)
            
            # 패턴 검증 점수
            pattern_result = self.pattern_service.validate_schedule_patterns(db, schedule_id)
            pattern_penalty = (100 - pattern_result.get('overall_score', 100))
            
            # 역할 배정 점수
            role_validation = self.role_service.validate_schedule_role_assignments(db, schedule_id)
            role_penalty = role_validation.get('total_penalty', 0)
            
            # 최종 점수 계산
            final_score = base_score + compliance_penalty + pattern_penalty + role_penalty
            final_score = max(0, min(100, final_score))  # 0-100 범위로 제한
            
            return final_score
            
        except Exception as e:
            logger.error(f"스케줄 점수 재계산 중 오류: {str(e)}")
            return 50.0  # 오류 시 중간값 반환
    
    def _evaluate_replacement_suitability(
        self, 
        db: Session, 
        candidate: Employee, 
        target_date: date, 
        target_shift: str,
        emergency: bool = False
    ) -> Dict:
        """대체자 적합성 평가"""
        score = 0.0
        reasons = []
        warnings = []
        availability = "unknown"
        
        try:
            # 1. 기본 가용성 확인 (이미 해당 시간에 근무하는지)
            existing_assignment = db.query(ShiftAssignment).filter(
                and_(
                    ShiftAssignment.employee_id == candidate.id,
                    ShiftAssignment.shift_date == target_date
                )
            ).first()
            
            if existing_assignment:
                if not emergency:
                    return {'score': 0, 'reasons': ['이미 해당 날짜에 근무 배정됨'], 'warnings': [], 'availability': 'unavailable'}
                else:
                    warnings.append('이미 근무 배정되어 있지만 응급상황으로 고려됨')
                    availability = "emergency_available"
                    score -= 20
            else:
                availability = "available"
                score += 30
                reasons.append('해당 날짜에 가용함')
            
            # 2. 역할 적합성
            if candidate.role in ['head_nurse', 'senior_nurse']:
                score += 20
                reasons.append('선임 간호사로 리더십 가능')
            elif candidate.role == 'staff_nurse':
                score += 15
                reasons.append('숙련된 일반 간호사')
            elif candidate.role == 'new_nurse':
                if target_shift == 'night':
                    score -= 10
                    warnings.append('신입간호사의 야간 근무 - 감독 필요')
                else:
                    score += 5
                    reasons.append('신입간호사지만 낮 근무 가능')
            
            # 3. 숙련도 및 경험
            score += candidate.skill_level * 3  # 1-5 레벨, 최대 15점
            score += min(candidate.years_experience, 10)  # 경험년수, 최대 10점
            
            if candidate.skill_level >= 4:
                reasons.append(f'높은 숙련도 (레벨 {candidate.skill_level})')
            if candidate.years_experience >= 5:
                reasons.append(f'풍부한 경험 ({candidate.years_experience}년)')
            
            # 4. 고용 형태 및 근무 제약
            employment_rules = db.query(EmploymentTypeRule).filter(
                EmploymentTypeRule.employment_type == candidate.employment_type
            ).first()
            
            if employment_rules:
                if target_shift in (employment_rules.allowed_shift_types or []):
                    score += 10
                    reasons.append('고용 형태에 적합한 근무 시간대')
                else:
                    score -= 15
                    warnings.append('고용 형태 제약 위반')
            
            # 5. 최근 근무 패턴 분석
            recent_assignments = db.query(ShiftAssignment).filter(
                and_(
                    ShiftAssignment.employee_id == candidate.id,
                    ShiftAssignment.shift_date >= target_date - timedelta(days=7),
                    ShiftAssignment.shift_date <= target_date + timedelta(days=7)
                )
            ).all()
            
            night_count = len([a for a in recent_assignments if a.shift_type == 'night'])
            if target_shift == 'night' and night_count >= 3:
                score -= 15
                warnings.append('최근 야간 근무가 많음')
            elif night_count <= 1:
                score += 5
                reasons.append('최근 야간 근무 부담이 적음')
            
            # 6. 전문 분야 고려
            if candidate.specialization and target_shift in ['night', 'emergency']:
                if candidate.specialization in ['ICU', 'ER', 'Critical_Care']:
                    score += 15
                    reasons.append(f'응급/중환자 전문 ({candidate.specialization})')
            
            return {
                'score': max(0, score),
                'reasons': reasons,
                'warnings': warnings,
                'availability': availability
            }
            
        except Exception as e:
            logger.error(f"대체자 적합성 평가 중 오류: {str(e)}")
            return {'score': 0, 'reasons': ['평가 중 오류 발생'], 'warnings': [], 'availability': 'error'}
    
    def _emergency_validation(self, db: Session, employee_id: int, target_date: date, target_shift: str) -> Dict:
        """응급 상황에서의 최소 검증"""
        errors = []
        
        try:
            # 1. 직원 존재 및 활성 상태
            employee = db.query(Employee).filter(
                Employee.id == employee_id,
                Employee.is_active == True
            ).first()
            
            if not employee:
                errors.append('직원을 찾을 수 없거나 비활성 상태입니다')
            
            # 2. 중복 배정 (응급 상황에서도 확인)
            duplicate = db.query(ShiftAssignment).filter(
                and_(
                    ShiftAssignment.employee_id == employee_id,
                    ShiftAssignment.shift_date == target_date,
                    ShiftAssignment.shift_type == target_shift
                )
            ).first()
            
            if duplicate:
                errors.append('이미 동일한 시간에 근무 배정되어 있습니다')
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"응급 검증 중 오류: {str(e)}")
            return {
                'valid': False,
                'errors': [f'검증 중 오류 발생: {str(e)}']
            }
    
    def _log_emergency_action(
        self, 
        db: Session, 
        assignment_id: int, 
        original_employee_id: int,
        replacement_employee_id: int, 
        reason: str, 
        admin_id: int
    ):
        """응급 조치 로그 기록"""
        try:
            # 응급 로그를 별도 테이블에 기록 (실제 구현에서는 EmergencyLog 모델 필요)
            logger.info(f"응급 재배치 로그 - Assignment: {assignment_id}, "
                       f"Original: {original_employee_id} -> Replacement: {replacement_employee_id}, "
                       f"Reason: {reason}, Admin: {admin_id}")
        except Exception as e:
            logger.error(f"응급 로그 기록 중 오류: {str(e)}")
    
    def _queue_emergency_notifications(
        self, 
        db: Session, 
        employee_ids: List[int], 
        assignment, 
        reason: str
    ):
        """응급 상황 알림 대기열 추가"""
        try:
            # 알림 시스템에 메시지 추가 (실제 구현에서는 Notification 모델 및 큐 시스템 필요)
            logger.info(f"응급 알림 대기열 추가 - 대상: {employee_ids}, 근무: {assignment.id}, 사유: {reason}")
        except Exception as e:
            logger.error(f"응급 알림 대기열 추가 중 오류: {str(e)}")