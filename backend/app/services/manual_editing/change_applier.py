"""
변경 적용기
Single Responsibility: 검증된 근무 변경을 실제로 적용하는 것만 담당
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .entities import ChangeRequest, ChangeResult, ValidationResult, ChangeType
from .validation_engine import ValidationEngine
from .audit_logger import AuditLogger
from .notification_manager import NotificationManager
from app.models.scheduling_models import ShiftAssignment
import logging

logger = logging.getLogger(__name__)


class ChangeApplier:
    """근무 변경 적용기"""

    def __init__(self):
        self.validation_engine = ValidationEngine()
        self.audit_logger = AuditLogger()
        self.notification_manager = NotificationManager()

    def apply_shift_change(self, db: Session, change_request: ChangeRequest) -> ChangeResult:
        """근무 변경 적용"""
        try:
            # 1. 검증 실행 (오버라이드가 아닌 경우)
            if not change_request.override:
                validation_result = self.validation_engine.validate_shift_change(db, change_request)

                if not validation_result.valid:
                    return ChangeResult(
                        success=False,
                        message="검증 실패로 인해 변경이 취소되었습니다",
                        validation_result=validation_result
                    )

            # 2. 트랜잭션 시작
            try:
                # 현재 배정 조회
                current_assignment = db.query(ShiftAssignment).filter(
                    ShiftAssignment.id == change_request.assignment_id
                ).first()

                if not current_assignment:
                    return ChangeResult(
                        success=False,
                        message="해당 근무 배정을 찾을 수 없습니다"
                    )

                # 변경 전 상태 백업 (감사 로그용)
                original_state = {
                    'employee_id': current_assignment.employee_id,
                    'shift_type': current_assignment.shift_type,
                    'shift_date': current_assignment.shift_date.isoformat(),
                    'ward_id': current_assignment.ward_id
                }

                # 3. 실제 변경 적용
                changes_made = self._apply_changes(current_assignment, change_request)

                if not changes_made:
                    return ChangeResult(
                        success=False,
                        message="적용할 변경사항이 없습니다"
                    )

                # 4. 데이터베이스 커밋
                db.commit()

                # 5. 감사 로그 생성
                audit_log_id = self.audit_logger.log_change(
                    db=db,
                    change_type=change_request.change_type,
                    assignment_id=change_request.assignment_id,
                    original_state=original_state,
                    new_state=self._get_current_state(current_assignment),
                    admin_id=change_request.admin_id,
                    override_reason=change_request.override_reason if change_request.override else None
                )

                # 6. 알림 발송
                notification_ids = self.notification_manager.send_change_notifications(
                    db=db,
                    change_request=change_request,
                    assignment=current_assignment,
                    validation_result=validation_result if not change_request.override else None
                )

                return ChangeResult(
                    success=True,
                    message="근무 변경이 성공적으로 적용되었습니다",
                    assignment_id=current_assignment.id,
                    audit_log_id=audit_log_id,
                    notifications_sent=notification_ids,
                    validation_result=validation_result if not change_request.override else None
                )

            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"데이터베이스 오류 발생: {str(e)}")
                return ChangeResult(
                    success=False,
                    message=f"데이터베이스 오류로 인해 변경이 실패했습니다: {str(e)}"
                )

        except Exception as e:
            logger.error(f"근무 변경 적용 중 오류 발생: {str(e)}")
            return ChangeResult(
                success=False,
                message=f"시스템 오류로 인해 변경이 실패했습니다: {str(e)}"
            )

    def _apply_changes(self, assignment: ShiftAssignment, change_request: ChangeRequest) -> bool:
        """실제 변경사항 적용"""
        changes_made = False

        # 직원 변경
        if change_request.new_employee_id and change_request.new_employee_id != assignment.employee_id:
            assignment.employee_id = change_request.new_employee_id
            changes_made = True
            logger.info(f"근무 배정 {assignment.id}: 직원 변경 {assignment.employee_id} -> {change_request.new_employee_id}")

        # 근무 타입 변경
        if change_request.new_shift_type and change_request.new_shift_type != assignment.shift_type:
            assignment.shift_type = change_request.new_shift_type
            changes_made = True
            logger.info(f"근무 배정 {assignment.id}: 근무 타입 변경 {assignment.shift_type} -> {change_request.new_shift_type}")

        # 근무 날짜 변경
        if change_request.new_shift_date and change_request.new_shift_date != assignment.shift_date:
            assignment.shift_date = change_request.new_shift_date
            changes_made = True
            logger.info(f"근무 배정 {assignment.id}: 근무 날짜 변경 {assignment.shift_date} -> {change_request.new_shift_date}")

        # 변경 시간 업데이트
        if changes_made:
            assignment.updated_at = datetime.now()

        return changes_made

    def _get_current_state(self, assignment: ShiftAssignment) -> Dict[str, Any]:
        """현재 배정 상태 반환"""
        return {
            'employee_id': assignment.employee_id,
            'shift_type': assignment.shift_type,
            'shift_date': assignment.shift_date.isoformat(),
            'ward_id': assignment.ward_id,
            'updated_at': assignment.updated_at.isoformat() if assignment.updated_at else None
        }

    def apply_emergency_override(self, db: Session, change_request: ChangeRequest) -> ChangeResult:
        """응급 오버라이드 적용"""
        if not change_request.override:
            return ChangeResult(
                success=False,
                message="응급 오버라이드가 요청되지 않았습니다"
            )

        if not change_request.override_reason:
            return ChangeResult(
                success=False,
                message="응급 오버라이드 사유가 필요합니다"
            )

        logger.warning(f"응급 오버라이드 적용: assignment_id={change_request.assignment_id}, "
                      f"reason={change_request.override_reason}, admin_id={change_request.admin_id}")

        # 검증 없이 변경 적용
        change_request.override = True
        return self.apply_shift_change(db, change_request)

    def batch_apply_changes(self, db: Session, change_requests: List[ChangeRequest]) -> List[ChangeResult]:
        """여러 변경사항을 일괄 적용"""
        results = []

        for change_request in change_requests:
            try:
                result = self.apply_shift_change(db, change_request)
                results.append(result)

                # 실패한 경우 로그 기록
                if not result.success:
                    logger.warning(f"일괄 변경 중 실패: assignment_id={change_request.assignment_id}, "
                                 f"message={result.message}")

            except Exception as e:
                logger.error(f"일괄 변경 중 오류 발생: assignment_id={change_request.assignment_id}, error={str(e)}")
                results.append(ChangeResult(
                    success=False,
                    message=f"변경 적용 중 오류 발생: {str(e)}"
                ))

        return results

    def rollback_change(self, db: Session, assignment_id: int, admin_id: int) -> ChangeResult:
        """변경사항 롤백"""
        try:
            # 감사 로그에서 원래 상태 조회
            original_state = self.audit_logger.get_original_state(db, assignment_id)

            if not original_state:
                return ChangeResult(
                    success=False,
                    message="롤백할 원본 상태를 찾을 수 없습니다"
                )

            # 롤백 요청 생성
            rollback_request = ChangeRequest(
                assignment_id=assignment_id,
                new_employee_id=original_state.get('employee_id'),
                new_shift_type=original_state.get('shift_type'),
                new_shift_date=datetime.fromisoformat(original_state.get('shift_date')).date(),
                override=True,
                override_reason="관리자 롤백",
                admin_id=admin_id
            )

            return self.apply_shift_change(db, rollback_request)

        except Exception as e:
            logger.error(f"변경사항 롤백 중 오류 발생: {str(e)}")
            return ChangeResult(
                success=False,
                message=f"롤백 중 오류 발생: {str(e)}"
            )