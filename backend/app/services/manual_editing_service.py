"""
통합 수동 편집 서비스
SOLID 원칙에 따라 분리된 컴포넌트들을 조합하여 수동 편집 기능을 제공
"""
from typing import List, Dict, Any, Optional, Union
from datetime import date
from sqlalchemy.orm import Session

# 분리된 컴포넌트들 import
from app.services.manual_editing.entities import (
    ChangeRequest, ChangeResult, ValidationResult, ChangeType
)
from app.services.manual_editing.validation_engine import ValidationEngine
from app.services.manual_editing.change_applier import ChangeApplier
from app.services.manual_editing.audit_logger import AuditLogger
from app.services.manual_editing.notification_manager import NotificationManager

import logging

logger = logging.getLogger(__name__)


class ManualEditingService:
    """
    수동 편집 서비스 통합 파사드
    Single Responsibility: 수동 편집 기능의 진입점 및 조합 관리
    """

    def __init__(self):
        # 각 책임을 담당하는 컴포넌트들을 조합
        self.validation_engine = ValidationEngine()
        self.change_applier = ChangeApplier()
        self.audit_logger = AuditLogger()
        self.notification_manager = NotificationManager()

    def create_shift_change_request(self,
                                  assignment_id: int,
                                  admin_id: int,
                                  new_employee_id: Optional[int] = None,
                                  new_shift_type: Optional[str] = None,
                                  new_shift_date: Optional[date] = None,
                                  override: bool = False,
                                  override_reason: Optional[str] = None) -> ChangeRequest:
        """근무 변경 요청 생성"""

        # 변경 타입 자동 결정
        change_type = self._determine_change_type(
            new_employee_id, new_shift_type, new_shift_date, override
        )

        return ChangeRequest(
            assignment_id=assignment_id,
            new_employee_id=new_employee_id,
            new_shift_type=new_shift_type,
            new_shift_date=new_shift_date,
            change_type=change_type,
            override=override,
            override_reason=override_reason,
            admin_id=admin_id
        )

    def process_shift_change(self, db: Session, change_request: ChangeRequest) -> ChangeResult:
        """
        근무 변경 처리 메인 메서드
        전체 워크플로우 조정: 검증 → 적용 → 알림
        """
        try:
            logger.info(f"근무 변경 처리 시작: assignment_id={change_request.assignment_id}")

            # 1. 검증 (오버라이드가 아닌 경우에만)
            validation_result = None
            if not change_request.override:
                validation_result = self.validation_engine.validate_shift_change(db, change_request)

                if not validation_result.valid:
                    logger.warning(f"근무 변경 검증 실패: {validation_result.error}")
                    return ChangeResult(
                        success=False,
                        message="검증 실패로 인해 변경이 취소되었습니다",
                        validation_result=validation_result
                    )

            # 2. 변경 적용
            result = self.change_applier.apply_shift_change(db, change_request)

            if result.success:
                logger.info(f"근무 변경 처리 완료: assignment_id={change_request.assignment_id}")
            else:
                logger.error(f"근무 변경 처리 실패: {result.message}")

            return result

        except Exception as e:
            logger.error(f"근무 변경 처리 중 오류 발생: {str(e)}")
            return ChangeResult(
                success=False,
                message=f"시스템 오류로 인해 변경이 실패했습니다: {str(e)}"
            )

    def validate_change_only(self, db: Session, change_request: ChangeRequest) -> ValidationResult:
        """변경 적용 없이 검증만 수행"""
        return self.validation_engine.validate_shift_change(db, change_request)

    def emergency_override(self, db: Session, change_request: ChangeRequest) -> ChangeResult:
        """응급 오버라이드 처리 (검증 생략)"""
        if not change_request.override:
            return ChangeResult(
                success=False,
                message="응급 오버라이드가 요청되지 않았습니다"
            )

        return self.change_applier.apply_emergency_override(db, change_request)

    def batch_process_changes(self, db: Session, change_requests: List[ChangeRequest]) -> List[ChangeResult]:
        """여러 변경사항을 일괄 처리"""
        results = []

        for change_request in change_requests:
            try:
                result = self.process_shift_change(db, change_request)
                results.append(result)

            except Exception as e:
                logger.error(f"일괄 처리 중 오류: assignment_id={change_request.assignment_id}, error={str(e)}")
                results.append(ChangeResult(
                    success=False,
                    message=f"처리 중 오류 발생: {str(e)}"
                ))

        return results

    def rollback_change(self, db: Session, assignment_id: int, admin_id: int) -> ChangeResult:
        """변경사항 롤백"""
        return self.change_applier.rollback_change(db, assignment_id, admin_id)

    def get_change_history(self, db: Session, assignment_id: int) -> List[Dict[str, Any]]:
        """특정 배정의 변경 이력 조회"""
        return self.audit_logger.get_change_history(db, assignment_id)

    def get_admin_activity_log(self, db: Session, admin_id: int,
                             start_date, end_date) -> List[Dict[str, Any]]:
        """관리자 활동 로그 조회"""
        return self.audit_logger.get_admin_activity_log(db, admin_id, start_date, end_date)

    def generate_audit_report(self, db: Session, start_date, end_date,
                            ward_id: Optional[int] = None) -> Dict[str, Any]:
        """감사 보고서 생성"""
        return self.audit_logger.generate_audit_report(db, start_date, end_date, ward_id)

    def _determine_change_type(self,
                              new_employee_id: Optional[int],
                              new_shift_type: Optional[str],
                              new_shift_date: Optional[date],
                              override: bool) -> ChangeType:
        """변경 타입 자동 결정"""
        if override:
            return ChangeType.EMERGENCY_OVERRIDE

        if new_employee_id:
            return ChangeType.EMPLOYEE_CHANGE

        if new_shift_type:
            return ChangeType.SHIFT_TYPE_CHANGE

        if new_shift_date:
            return ChangeType.SHIFT_DATE_CHANGE

        return ChangeType.GENERAL_UPDATE

    # 편의 메서드들 - 자주 사용되는 패턴들
    def change_employee(self, db: Session, assignment_id: int, new_employee_id: int,
                       admin_id: int, reason: str = None) -> ChangeResult:
        """직원 변경 편의 메서드"""
        change_request = self.create_shift_change_request(
            assignment_id=assignment_id,
            admin_id=admin_id,
            new_employee_id=new_employee_id
        )
        return self.process_shift_change(db, change_request)

    def change_shift_type(self, db: Session, assignment_id: int, new_shift_type: str,
                         admin_id: int, reason: str = None) -> ChangeResult:
        """근무 타입 변경 편의 메서드"""
        change_request = self.create_shift_change_request(
            assignment_id=assignment_id,
            admin_id=admin_id,
            new_shift_type=new_shift_type
        )
        return self.process_shift_change(db, change_request)

    def change_shift_date(self, db: Session, assignment_id: int, new_shift_date: date,
                         admin_id: int, reason: str = None) -> ChangeResult:
        """근무 날짜 변경 편의 메서드"""
        change_request = self.create_shift_change_request(
            assignment_id=assignment_id,
            admin_id=admin_id,
            new_shift_date=new_shift_date
        )
        return self.process_shift_change(db, change_request)

    def emergency_change_employee(self, db: Session, assignment_id: int,
                                new_employee_id: int, admin_id: int,
                                reason: str) -> ChangeResult:
        """응급 직원 변경 편의 메서드"""
        change_request = self.create_shift_change_request(
            assignment_id=assignment_id,
            admin_id=admin_id,
            new_employee_id=new_employee_id,
            override=True,
            override_reason=reason
        )
        return self.emergency_override(db, change_request)

    # 조회 및 분석 메서드들
    def get_validation_summary(self, db: Session, change_request: ChangeRequest) -> Dict[str, Any]:
        """변경 요청에 대한 검증 요약 정보 제공"""
        validation_result = self.validate_change_only(db, change_request)

        return {
            'valid': validation_result.valid,
            'error_count': len(validation_result.errors),
            'warning_count': len(validation_result.warnings),
            'pattern_score': validation_result.pattern_score,
            'recommendations': validation_result.recommendations,
            'can_proceed': validation_result.valid or change_request.override
        }

    def check_assignment_editability(self, db: Session, assignment_id: int) -> Dict[str, Any]:
        """배정의 편집 가능성 체크"""
        try:
            # 임시 변경 요청으로 기본 검증 수행
            temp_request = ChangeRequest(
                assignment_id=assignment_id,
                admin_id=0,  # 임시 ID
                change_type=ChangeType.GENERAL_UPDATE
            )

            validation_result = self.validate_change_only(db, temp_request)

            return {
                'editable': True,
                'restrictions': [],
                'warnings': [w['message'] for w in validation_result.warnings],
                'pattern_score': validation_result.pattern_score
            }

        except Exception as e:
            logger.error(f"배정 편집 가능성 체크 중 오류: {str(e)}")
            return {
                'editable': False,
                'restrictions': ['시스템 오류로 인한 편집 불가'],
                'warnings': [],
                'pattern_score': 0.0
            }

    # 기존 메서드들과의 호환성을 위한 래퍼 메서드들
    def validate_shift_change(self, db: Session, assignment_id: int,
                             new_employee_id: Optional[int] = None,
                             new_shift_type: Optional[str] = None,
                             new_shift_date: Optional[date] = None) -> Dict:
        """기존 API와의 호환성을 위한 래퍼 메서드"""
        try:
            change_request = ChangeRequest(
                assignment_id=assignment_id,
                new_employee_id=new_employee_id,
                new_shift_type=new_shift_type,
                new_shift_date=new_shift_date,
                admin_id=0  # 임시 ID
            )

            validation_result = self.validation_engine.validate_shift_change(db, change_request)

            return {
                'valid': validation_result.valid,
                'warnings': [{'message': w['message'], 'severity': w['severity']} for w in validation_result.warnings],
                'errors': [{'message': e['message'], 'severity': e['severity']} for e in validation_result.errors],
                'violations': validation_result.violations,
                'pattern_score': validation_result.pattern_score,
                'recommendations': validation_result.recommendations,
                'error': validation_result.error
            }
        except Exception as e:
            logger.error(f"기존 API 호환 래퍼에서 오류: {str(e)}")
            return {
                'valid': False,
                'error': f'검증 중 오류 발생: {str(e)}',
                'warnings': [],
                'errors': [],
                'violations': [],
                'pattern_score': 0.0,
                'recommendations': []
            }

    def apply_shift_change(self, db: Session, assignment_id: int,
                          new_employee_id: Optional[int] = None,
                          new_shift_type: Optional[str] = None,
                          new_shift_date: Optional[date] = None,
                          override: bool = False,
                          override_reason: Optional[str] = None,
                          admin_id: Optional[int] = None) -> Dict:
        """기존 API와의 호환성을 위한 래퍼 메서드"""
        try:
            change_request = self.create_shift_change_request(
                assignment_id=assignment_id,
                admin_id=admin_id or 0,
                new_employee_id=new_employee_id,
                new_shift_type=new_shift_type,
                new_shift_date=new_shift_date,
                override=override,
                override_reason=override_reason
            )

            result = self.process_shift_change(db, change_request)

            return {
                'success': result.success,
                'message': result.message,
                'error': result.message if not result.success else None,
                'validation_result': result.validation_result.__dict__ if result.validation_result else None,
                'assignment_id': result.assignment_id,
                'audit_log_id': result.audit_log_id,
                'notifications_sent': result.notifications_sent or []
            }
        except Exception as e:
            logger.error(f"기존 API 호환 래퍼에서 오류: {str(e)}")
            return {
                'success': False,
                'error': f'변경 적용 중 오류 발생: {str(e)}'
            }