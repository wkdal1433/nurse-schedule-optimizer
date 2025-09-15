"""
알림 관리자
Single Responsibility: 변경사항에 대한 알림 발송만 담당
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .entities import ChangeRequest, ValidationResult, NotificationData
from app.models.scheduling_models import ShiftAssignment
from app.models.models import Employee
from app.services.notification_service import NotificationService
from app.services.websocket_service import websocket_notification_service
from app.models.notification_models import NotificationType, NotificationPriority
import logging
import asyncio

logger = logging.getLogger(__name__)


class NotificationManager:
    """변경사항 알림 관리자"""

    def __init__(self):
        self.notification_service = NotificationService()

    def send_change_notifications(self,
                                db: Session,
                                change_request: ChangeRequest,
                                assignment: ShiftAssignment,
                                validation_result: Optional[ValidationResult] = None) -> List[int]:
        """변경사항 알림 발송"""
        notification_ids = []

        try:
            # 알림 대상자 결정
            recipients = self._determine_recipients(db, change_request, assignment)

            # 알림 타입 결정
            notification_type = self._determine_notification_type(change_request)

            # 알림 우선순위 결정
            priority = self._determine_priority(change_request, validation_result)

            # 알림 메시지 생성
            message = self._generate_notification_message(db, change_request, assignment)

            # 각 수신자에게 알림 발송
            for recipient_id in recipients:
                try:
                    notification_id = self._send_individual_notification(
                        db=db,
                        recipient_id=recipient_id,
                        notification_type=notification_type,
                        priority=priority,
                        message=message,
                        change_request=change_request,
                        assignment=assignment
                    )

                    if notification_id:
                        notification_ids.append(notification_id)

                except Exception as e:
                    logger.error(f"개별 알림 발송 실패: recipient_id={recipient_id}, error={str(e)}")

            # WebSocket을 통한 실시간 알림
            self._send_realtime_notifications(change_request, assignment, recipients)

            # 중요한 변경사항의 경우 추가 알림
            if change_request.override:
                self._send_emergency_notifications(db, change_request, assignment)

            logger.info(f"알림 발송 완료: {len(notification_ids)}개 발송")

        except Exception as e:
            logger.error(f"알림 발송 중 오류 발생: {str(e)}")

        return notification_ids

    def _determine_recipients(self, db: Session, change_request: ChangeRequest,
                            assignment: ShiftAssignment) -> List[int]:
        """알림 수신자 결정"""
        recipients = set()

        try:
            # 1. 변경 대상 직원
            if change_request.new_employee_id:
                recipients.add(change_request.new_employee_id)

            # 2. 기존 배정 직원 (직원 변경의 경우)
            if (change_request.new_employee_id and
                change_request.new_employee_id != assignment.employee_id):
                recipients.add(assignment.employee_id)

            # 3. 같은 병동의 관리자들
            ward_managers = db.query(Employee).filter(
                Employee.ward_id == assignment.ward_id,
                Employee.role.in_(['head_nurse', 'charge_nurse']),
                Employee.is_active == True
            ).all()

            for manager in ward_managers:
                recipients.add(manager.id)

            # 4. 같은 날짜/교대의 다른 간호사들 (교대 변경의 경우)
            if change_request.new_shift_type:
                same_shift_nurses = db.query(ShiftAssignment).filter(
                    ShiftAssignment.ward_id == assignment.ward_id,
                    ShiftAssignment.shift_date == assignment.shift_date,
                    ShiftAssignment.shift_type == (change_request.new_shift_type or assignment.shift_type),
                    ShiftAssignment.employee_id != assignment.employee_id
                ).all()

                for shift_assignment in same_shift_nurses:
                    recipients.add(shift_assignment.employee_id)

        except Exception as e:
            logger.error(f"수신자 결정 중 오류 발생: {str(e)}")

        return list(recipients)

    def _determine_notification_type(self, change_request: ChangeRequest) -> NotificationType:
        """알림 타입 결정"""
        if change_request.override:
            return NotificationType.EMERGENCY_OVERRIDE

        if change_request.new_employee_id:
            return NotificationType.ASSIGNMENT_CHANGE

        if change_request.new_shift_type:
            return NotificationType.SHIFT_CHANGE

        if change_request.new_shift_date:
            return NotificationType.SCHEDULE_CHANGE

        return NotificationType.GENERAL_UPDATE

    def _determine_priority(self, change_request: ChangeRequest,
                          validation_result: Optional[ValidationResult]) -> NotificationPriority:
        """알림 우선순위 결정"""
        if change_request.override:
            return NotificationPriority.HIGH

        if validation_result and validation_result.has_high_violations():
            return NotificationPriority.MEDIUM

        return NotificationPriority.LOW

    def _generate_notification_message(self, db: Session, change_request: ChangeRequest,
                                     assignment: ShiftAssignment) -> Dict[str, Any]:
        """알림 메시지 생성"""
        try:
            # 직원 정보 조회
            current_employee = db.query(Employee).filter(
                Employee.id == assignment.employee_id
            ).first()

            new_employee = None
            if change_request.new_employee_id:
                new_employee = db.query(Employee).filter(
                    Employee.id == change_request.new_employee_id
                ).first()

            # 메시지 구성
            message = {
                'title': self._get_message_title(change_request),
                'body': self._get_message_body(change_request, assignment, current_employee, new_employee),
                'assignment_id': assignment.id,
                'ward_id': assignment.ward_id,
                'change_details': {
                    'original': {
                        'employee_name': current_employee.name if current_employee else 'Unknown',
                        'shift_type': assignment.shift_type,
                        'shift_date': assignment.shift_date.isoformat()
                    },
                    'new': {
                        'employee_name': new_employee.name if new_employee else current_employee.name if current_employee else 'Unknown',
                        'shift_type': change_request.new_shift_type or assignment.shift_type,
                        'shift_date': (change_request.new_shift_date or assignment.shift_date).isoformat()
                    }
                }
            }

            return message

        except Exception as e:
            logger.error(f"알림 메시지 생성 중 오류 발생: {str(e)}")
            return {'title': '근무 변경 알림', 'body': '근무 스케줄에 변경사항이 있습니다.'}

    def _get_message_title(self, change_request: ChangeRequest) -> str:
        """알림 제목 생성"""
        if change_request.override:
            return "🚨 응급 근무 변경"

        if change_request.new_employee_id:
            return "👥 근무자 변경"

        if change_request.new_shift_type:
            return "🕐 근무 시간 변경"

        if change_request.new_shift_date:
            return "📅 근무 날짜 변경"

        return "📝 근무 스케줄 변경"

    def _get_message_body(self, change_request: ChangeRequest, assignment: ShiftAssignment,
                         current_employee: Optional[Employee], new_employee: Optional[Employee]) -> str:
        """알림 본문 생성"""
        date_str = assignment.shift_date.strftime('%Y-%m-%d')
        current_name = current_employee.name if current_employee else 'Unknown'
        new_name = new_employee.name if new_employee else current_name

        if change_request.override:
            return f"응급 상황으로 인해 {date_str} {assignment.shift_type} 근무가 변경되었습니다."

        if change_request.new_employee_id:
            return f"{date_str} {assignment.shift_type} 근무자가 {current_name}에서 {new_name}으로 변경되었습니다."

        if change_request.new_shift_type:
            return f"{date_str} {current_name}의 근무가 {assignment.shift_type}에서 {change_request.new_shift_type}으로 변경되었습니다."

        if change_request.new_shift_date:
            new_date_str = change_request.new_shift_date.strftime('%Y-%m-%d')
            return f"{current_name}의 {assignment.shift_type} 근무가 {date_str}에서 {new_date_str}로 변경되었습니다."

        return f"{current_name}의 근무 스케줄에 변경사항이 있습니다."

    def _send_individual_notification(self,
                                    db: Session,
                                    recipient_id: int,
                                    notification_type: NotificationType,
                                    priority: NotificationPriority,
                                    message: Dict[str, Any],
                                    change_request: ChangeRequest,
                                    assignment: ShiftAssignment) -> Optional[int]:
        """개별 알림 발송"""
        try:
            # NotificationService를 통한 알림 발송
            notification_id = self.notification_service.create_notification(
                db=db,
                user_id=recipient_id,
                title=message['title'],
                content=message['body'],
                notification_type=notification_type,
                priority=priority,
                metadata={
                    'assignment_id': assignment.id,
                    'ward_id': assignment.ward_id,
                    'change_type': change_request.change_type.value if change_request.change_type else 'unknown',
                    'change_details': message.get('change_details')
                }
            )

            logger.debug(f"개별 알림 발송: recipient_id={recipient_id}, notification_id={notification_id}")
            return notification_id

        except Exception as e:
            logger.error(f"개별 알림 발송 중 오류: recipient_id={recipient_id}, error={str(e)}")
            return None

    def _send_realtime_notifications(self, change_request: ChangeRequest,
                                   assignment: ShiftAssignment, recipients: List[int]):
        """실시간 WebSocket 알림 발송"""
        try:
            notification_data = NotificationData(
                change_type=change_request.change_type,
                assignment_id=assignment.id,
                affected_employees=recipients,
                ward_id=assignment.ward_id,
                change_details={
                    'assignment_id': assignment.id,
                    'ward_id': assignment.ward_id,
                    'shift_date': assignment.shift_date.isoformat(),
                    'override': change_request.override
                }
            )

            # WebSocket 서비스를 통한 실시간 알림
            asyncio.create_task(
                websocket_notification_service.broadcast_to_ward(
                    ward_id=assignment.ward_id,
                    message=notification_data.to_dict()
                )
            )

            logger.debug(f"실시간 알림 발송: ward_id={assignment.ward_id}, recipients={len(recipients)}")

        except Exception as e:
            logger.error(f"실시간 알림 발송 중 오류: {str(e)}")

    def _send_emergency_notifications(self, db: Session, change_request: ChangeRequest,
                                    assignment: ShiftAssignment):
        """응급 상황 알림 발송"""
        try:
            # 병원 관리자들에게 응급 알림
            hospital_admins = db.query(Employee).filter(
                Employee.role == 'admin',
                Employee.is_active == True
            ).all()

            emergency_message = {
                'title': '🚨 응급 근무 변경 발생',
                'body': f'응급 상황으로 인해 병동 {assignment.ward_id}에서 근무 변경이 발생했습니다. '
                       f'사유: {change_request.override_reason}',
                'assignment_id': assignment.id,
                'ward_id': assignment.ward_id,
                'admin_id': change_request.admin_id
            }

            for admin in hospital_admins:
                self._send_individual_notification(
                    db=db,
                    recipient_id=admin.id,
                    notification_type=NotificationType.EMERGENCY_OVERRIDE,
                    priority=NotificationPriority.HIGH,
                    message=emergency_message,
                    change_request=change_request,
                    assignment=assignment
                )

            logger.warning(f"응급 알림 발송: {len(hospital_admins)}명의 관리자에게 발송")

        except Exception as e:
            logger.error(f"응급 알림 발송 중 오류: {str(e)}")