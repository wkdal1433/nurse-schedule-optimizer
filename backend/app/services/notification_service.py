"""
알림 및 승인 워크플로우 관리 서비스
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from app.models.notification_models import (
    Notification, ApprovalWorkflow, NotificationTemplate, NotificationQueue, EmergencyAlert,
    NotificationType, NotificationPriority, ApprovalStatus
)
from app.models.models import User, Employee, Ward
from app.models.shift import Shift
import logging
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """알림 시스템 관리 서비스"""
    
    def __init__(self):
        pass
    
    def create_notification(
        self,
        db: Session,
        recipient_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        sender_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        ward_id: Optional[int] = None,
        related_data: Optional[Dict] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """새 알림 생성"""
        try:
            notification = Notification(
                recipient_id=recipient_id,
                sender_id=sender_id,
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                ward_id=ward_id,
                related_data=related_data,
                expires_at=expires_at
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # 알림 발송 큐에 추가
            self._queue_notification_delivery(db, notification)
            
            logger.info(f"알림 생성 완료: {notification.id} -> 사용자 {recipient_id}")
            return notification
            
        except Exception as e:
            db.rollback()
            logger.error(f"알림 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 생성 중 오류 발생"
            )
    
    def create_bulk_notification(
        self,
        db: Session,
        recipient_ids: List[int],
        notification_type: NotificationType,
        title: str,
        message: str,
        sender_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        ward_id: Optional[int] = None,
        related_data: Optional[Dict] = None
    ) -> List[Notification]:
        """대량 알림 생성"""
        try:
            notifications = []
            
            for recipient_id in recipient_ids:
                notification = Notification(
                    recipient_id=recipient_id,
                    sender_id=sender_id,
                    notification_type=notification_type,
                    priority=priority,
                    title=title,
                    message=message,
                    ward_id=ward_id,
                    related_data=related_data
                )
                notifications.append(notification)
            
            db.add_all(notifications)
            db.commit()
            
            # 각 알림을 발송 큐에 추가
            for notification in notifications:
                db.refresh(notification)
                self._queue_notification_delivery(db, notification)
            
            logger.info(f"대량 알림 생성 완료: {len(notifications)}개 알림")
            return notifications
            
        except Exception as e:
            db.rollback()
            logger.error(f"대량 알림 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="대량 알림 생성 중 오류 발생"
            )
    
    def create_ward_notification(
        self,
        db: Session,
        ward_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        sender_id: Optional[int] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        role_filter: Optional[str] = None
    ) -> List[Notification]:
        """병동별 알림 생성"""
        try:
            # 병동의 모든 직원 조회
            query = db.query(Employee).filter(Employee.ward_id == ward_id)
            
            if role_filter:
                query = query.filter(Employee.role == role_filter)
            
            employees = query.all()
            recipient_ids = [emp.user_id for emp in employees if emp.user_id]
            
            if not recipient_ids:
                logger.warning(f"병동 {ward_id}에 알림 대상자가 없음")
                return []
            
            return self.create_bulk_notification(
                db=db,
                recipient_ids=recipient_ids,
                notification_type=notification_type,
                title=title,
                message=message,
                sender_id=sender_id,
                priority=priority,
                ward_id=ward_id
            )
            
        except Exception as e:
            logger.error(f"병동별 알림 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="병동별 알림 생성 중 오류 발생"
            )
    
    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> Notification:
        """알림을 읽음으로 표시"""
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.recipient_id == user_id
            ).first()
            
            if not notification:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림을 찾을 수 없습니다"
                )
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.commit()
                db.refresh(notification)
            
            return notification
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"알림 읽음 처리 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 읽음 처리 중 오류 발생"
            )
    
    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """사용자 알림 목록 조회"""
        try:
            query = db.query(Notification).filter(Notification.recipient_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            # 만료되지 않은 알림만 조회
            now = datetime.utcnow()
            query = query.filter(
                (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
            )
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()
            
            return notifications
            
        except Exception as e:
            logger.error(f"사용자 알림 조회 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 조회 중 오류 발생"
            )
    
    def _queue_notification_delivery(self, db: Session, notification: Notification):
        """알림을 발송 큐에 추가"""
        try:
            # WebSocket 실시간 알림
            websocket_queue = NotificationQueue(
                notification_id=notification.id,
                channel="websocket",
                status="pending"
            )
            db.add(websocket_queue)
            
            # 우선순위가 높은 경우 추가 채널 고려
            if notification.priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
                # 이메일 알림 큐 추가 (템플릿 설정이 있는 경우)
                template = self._get_notification_template(db, notification.notification_type)
                if template and template.send_email:
                    email_queue = NotificationQueue(
                        notification_id=notification.id,
                        channel="email",
                        status="pending"
                    )
                    db.add(email_queue)
                
                # SMS 알림 큐 추가 (긴급한 경우)
                if notification.priority == NotificationPriority.URGENT and template and template.send_sms:
                    sms_queue = NotificationQueue(
                        notification_id=notification.id,
                        channel="sms",
                        status="pending"
                    )
                    db.add(sms_queue)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"알림 큐 추가 실패: {str(e)}")
    
    def _get_notification_template(
        self, 
        db: Session, 
        notification_type: NotificationType
    ) -> Optional[NotificationTemplate]:
        """알림 타입에 해당하는 템플릿 조회"""
        return db.query(NotificationTemplate).filter(
            NotificationTemplate.notification_type == notification_type,
            NotificationTemplate.is_active == True
        ).first()


class ApprovalWorkflowService:
    """승인 워크플로우 관리 서비스"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def create_approval_request(
        self,
        db: Session,
        request_type: str,
        requester_id: int,
        title: str,
        description: str,
        request_data: Dict,
        required_role: Optional[str] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        expires_hours: int = 24
    ) -> ApprovalWorkflow:
        """승인 요청 생성"""
        try:
            # 만료시간 설정
            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            workflow = ApprovalWorkflow(
                request_type=request_type,
                requester_id=requester_id,
                required_role=required_role,
                title=title,
                description=description,
                request_data=request_data,
                priority=priority,
                expires_at=expires_at
            )
            
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            
            # 승인자에게 알림 발송
            self._notify_approvers(db, workflow)
            
            logger.info(f"승인 요청 생성: {workflow.id} by 사용자 {requester_id}")
            return workflow
            
        except Exception as e:
            db.rollback()
            logger.error(f"승인 요청 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="승인 요청 생성 중 오류 발생"
            )
    
    def approve_request(
        self,
        db: Session,
        workflow_id: int,
        approver_id: int,
        approval_reason: Optional[str] = None
    ) -> ApprovalWorkflow:
        """승인 요청 승인"""
        try:
            workflow = db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.id == workflow_id
            ).first()
            
            if not workflow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="승인 요청을 찾을 수 없습니다"
                )
            
            if workflow.status != ApprovalStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 처리된 승인 요청입니다"
                )
            
            # 승인자 권한 검증
            if not self._verify_approver_permission(db, workflow, approver_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="승인 권한이 없습니다"
                )
            
            workflow.status = ApprovalStatus.APPROVED
            workflow.approver_id = approver_id
            workflow.approved_at = datetime.utcnow()
            workflow.approval_reason = approval_reason
            
            db.commit()
            db.refresh(workflow)
            
            # 요청자에게 승인 결과 알림
            self._notify_approval_result(db, workflow, True)
            
            logger.info(f"승인 완료: {workflow.id} by 승인자 {approver_id}")
            return workflow
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"승인 처리 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="승인 처리 중 오류 발생"
            )
    
    def reject_request(
        self,
        db: Session,
        workflow_id: int,
        approver_id: int,
        rejection_reason: str
    ) -> ApprovalWorkflow:
        """승인 요청 거부"""
        try:
            workflow = db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.id == workflow_id
            ).first()
            
            if not workflow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="승인 요청을 찾을 수 없습니다"
                )
            
            if workflow.status != ApprovalStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 처리된 승인 요청입니다"
                )
            
            # 승인자 권한 검증
            if not self._verify_approver_permission(db, workflow, approver_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="승인 권한이 없습니다"
                )
            
            workflow.status = ApprovalStatus.REJECTED
            workflow.approver_id = approver_id
            workflow.rejected_at = datetime.utcnow()
            workflow.rejection_reason = rejection_reason
            
            db.commit()
            db.refresh(workflow)
            
            # 요청자에게 거부 결과 알림
            self._notify_approval_result(db, workflow, False)
            
            logger.info(f"승인 거부: {workflow.id} by 승인자 {approver_id}")
            return workflow
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"승인 거부 처리 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="승인 거부 처리 중 오류 발생"
            )
    
    def get_pending_approvals(
        self,
        db: Session,
        approver_id: int,
        limit: int = 20
    ) -> List[ApprovalWorkflow]:
        """승인 대기 목록 조회"""
        try:
            # 승인자 정보 조회
            approver = db.query(Employee).filter(Employee.user_id == approver_id).first()
            if not approver:
                return []
            
            query = db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.status == ApprovalStatus.PENDING
            )
            
            # 역할 기반 필터링
            if approver.role != 'admin':
                query = query.filter(
                    (ApprovalWorkflow.required_role.is_(None)) |
                    (ApprovalWorkflow.required_role == approver.role)
                )
            
            # 만료되지 않은 요청만 조회
            now = datetime.utcnow()
            query = query.filter(
                (ApprovalWorkflow.expires_at.is_(None)) |
                (ApprovalWorkflow.expires_at > now)
            )
            
            approvals = query.order_by(
                ApprovalWorkflow.priority.desc(),
                ApprovalWorkflow.created_at.asc()
            ).limit(limit).all()
            
            return approvals
            
        except Exception as e:
            logger.error(f"승인 대기 목록 조회 실패: {str(e)}")
            return []
    
    def _notify_approvers(self, db: Session, workflow: ApprovalWorkflow):
        """승인자들에게 알림 발송"""
        try:
            # 승인 권한을 가진 사용자들 찾기
            approver_ids = self._find_eligible_approvers(db, workflow)
            
            if not approver_ids:
                logger.warning(f"승인 요청 {workflow.id}에 대한 승인자가 없음")
                return
            
            # 승인 요청 알림 생성
            self.notification_service.create_bulk_notification(
                db=db,
                recipient_ids=approver_ids,
                notification_type=NotificationType.APPROVAL_REQUEST,
                title=f"승인 요청: {workflow.title}",
                message=f"{workflow.description}\n요청자: {workflow.requester.name if workflow.requester else 'Unknown'}",
                priority=workflow.priority,
                related_data={'workflow_id': workflow.id, 'request_type': workflow.request_type}
            )
            
        except Exception as e:
            logger.error(f"승인자 알림 발송 실패: {str(e)}")
    
    def _notify_approval_result(self, db: Session, workflow: ApprovalWorkflow, approved: bool):
        """승인 결과를 요청자에게 알림"""
        try:
            status_text = "승인됨" if approved else "거부됨"
            reason = workflow.approval_reason if approved else workflow.rejection_reason
            
            message = f"요청이 {status_text}되었습니다."
            if reason:
                message += f"\n사유: {reason}"
            
            self.notification_service.create_notification(
                db=db,
                recipient_id=workflow.requester_id,
                notification_type=NotificationType.APPROVAL_RESULT,
                title=f"승인 결과: {workflow.title}",
                message=message,
                sender_id=workflow.approver_id,
                priority=workflow.priority,
                related_data={
                    'workflow_id': workflow.id,
                    'approved': approved,
                    'request_type': workflow.request_type
                }
            )
            
        except Exception as e:
            logger.error(f"승인 결과 알림 실패: {str(e)}")
    
    def _find_eligible_approvers(self, db: Session, workflow: ApprovalWorkflow) -> List[int]:
        """승인 권한을 가진 사용자 목록 조회"""
        try:
            query = db.query(Employee)
            
            # 역할 기반 필터링
            if workflow.required_role:
                query = query.filter(Employee.role == workflow.required_role)
            else:
                # 기본적으로 선임 이상 역할에게 승인 권한
                query = query.filter(Employee.role.in_(['senior_nurse', 'head_nurse', 'admin']))
            
            employees = query.all()
            return [emp.user_id for emp in employees if emp.user_id]
            
        except Exception as e:
            logger.error(f"승인자 조회 실패: {str(e)}")
            return []
    
    def _verify_approver_permission(
        self, 
        db: Session, 
        workflow: ApprovalWorkflow, 
        approver_id: int
    ) -> bool:
        """승인자 권한 검증"""
        try:
            approver = db.query(Employee).filter(Employee.user_id == approver_id).first()
            if not approver:
                return False
            
            # 관리자는 모든 승인 권한
            if approver.role == 'admin':
                return True
            
            # 특정 역할이 요구되는 경우
            if workflow.required_role:
                return approver.role == workflow.required_role
            
            # 기본적으로 선임 이상에게 승인 권한
            return approver.role in ['senior_nurse', 'head_nurse', 'admin']
            
        except Exception as e:
            logger.error(f"승인자 권한 검증 실패: {str(e)}")
            return False


class EmergencyAlertService:
    """응급 상황 알림 관리 서비스"""
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def create_emergency_alert(
        self,
        db: Session,
        alert_type: str,
        severity: str,
        ward_id: int,
        title: str,
        description: str,
        action_required: Optional[str] = None,
        related_shift_id: Optional[int] = None,
        related_employee_id: Optional[int] = None
    ) -> EmergencyAlert:
        """응급 상황 알림 생성"""
        try:
            alert = EmergencyAlert(
                alert_type=alert_type,
                severity=severity,
                ward_id=ward_id,
                title=title,
                description=description,
                action_required=action_required,
                related_shift_id=related_shift_id,
                related_employee_id=related_employee_id
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            # 응급 상황에 따른 알림 발송
            self._broadcast_emergency_alert(db, alert)
            
            logger.info(f"응급 알림 생성: {alert.id} - {alert_type} in 병동 {ward_id}")
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"응급 알림 생성 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="응급 알림 생성 중 오류 발생"
            )
    
    def acknowledge_alert(
        self,
        db: Session,
        alert_id: int,
        user_id: int
    ) -> EmergencyAlert:
        """응급 알림 확인 처리"""
        try:
            alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
            
            if not alert:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="응급 알림을 찾을 수 없습니다"
                )
            
            if alert.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 처리된 알림입니다"
                )
            
            alert.status = "acknowledged"
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            # 확인 알림 발송
            self._notify_alert_acknowledged(db, alert)
            
            logger.info(f"응급 알림 확인: {alert.id} by 사용자 {user_id}")
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"응급 알림 확인 처리 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="응급 알림 확인 처리 중 오류 발생"
            )
    
    def resolve_alert(
        self,
        db: Session,
        alert_id: int,
        user_id: int
    ) -> EmergencyAlert:
        """응급 알림 해결 처리"""
        try:
            alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
            
            if not alert:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="응급 알림을 찾을 수 없습니다"
                )
            
            if alert.status == "resolved":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 해결된 알림입니다"
                )
            
            alert.status = "resolved"
            alert.resolved_by = user_id
            alert.resolved_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alert)
            
            # 해결 알림 발송
            self._notify_alert_resolved(db, alert)
            
            logger.info(f"응급 알림 해결: {alert.id} by 사용자 {user_id}")
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"응급 알림 해결 처리 실패: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="응급 알림 해결 처리 중 오류 발생"
            )
    
    def get_active_alerts(
        self,
        db: Session,
        ward_id: Optional[int] = None,
        severity: Optional[str] = None
    ) -> List[EmergencyAlert]:
        """활성 응급 알림 목록 조회"""
        try:
            query = db.query(EmergencyAlert).filter(
                EmergencyAlert.status.in_(["active", "acknowledged"])
            )
            
            if ward_id:
                query = query.filter(EmergencyAlert.ward_id == ward_id)
            
            if severity:
                query = query.filter(EmergencyAlert.severity == severity)
            
            alerts = query.order_by(
                EmergencyAlert.severity.desc(),
                EmergencyAlert.created_at.desc()
            ).all()
            
            return alerts
            
        except Exception as e:
            logger.error(f"활성 응급 알림 조회 실패: {str(e)}")
            return []
    
    def _broadcast_emergency_alert(self, db: Session, alert: EmergencyAlert):
        """응급 상황 알림 브로드캐스트"""
        try:
            # 심각도에 따른 알림 범위 결정
            if alert.severity in ["high", "critical"]:
                # 전체 병원 알림
                self._notify_all_management(db, alert)
            else:
                # 해당 병동만 알림
                self.notification_service.create_ward_notification(
                    db=db,
                    ward_id=alert.ward_id,
                    notification_type=NotificationType.EMERGENCY_REQUEST,
                    title=f"🚨 응급상황: {alert.title}",
                    message=f"{alert.description}\n{alert.action_required or ''}",
                    priority=NotificationPriority.URGENT if alert.severity == "critical" else NotificationPriority.HIGH
                )
            
        except Exception as e:
            logger.error(f"응급 알림 브로드캐스트 실패: {str(e)}")
    
    def _notify_all_management(self, db: Session, alert: EmergencyAlert):
        """관리자 전체에게 응급 알림"""
        try:
            # 수간호사 및 관리자에게 알림
            managers = db.query(Employee).filter(
                Employee.role.in_(['head_nurse', 'admin'])
            ).all()
            
            manager_user_ids = [mgr.user_id for mgr in managers if mgr.user_id]
            
            if manager_user_ids:
                self.notification_service.create_bulk_notification(
                    db=db,
                    recipient_ids=manager_user_ids,
                    notification_type=NotificationType.EMERGENCY_REQUEST,
                    title=f"🚨 긴급상황: {alert.title}",
                    message=f"병동: {alert.ward.name if alert.ward else '미지정'}\n{alert.description}\n{alert.action_required or ''}",
                    priority=NotificationPriority.URGENT,
                    related_data={
                        'alert_id': alert.id,
                        'ward_id': alert.ward_id,
                        'severity': alert.severity
                    }
                )
                
        except Exception as e:
            logger.error(f"관리자 응급 알림 실패: {str(e)}")
    
    def _notify_alert_acknowledged(self, db: Session, alert: EmergencyAlert):
        """응급 알림 확인 통지"""
        try:
            # 관리자들에게 확인 통지
            self.notification_service.create_ward_notification(
                db=db,
                ward_id=alert.ward_id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"응급상황 확인됨: {alert.title}",
                message=f"담당자가 확인했습니다.\n확인자: {alert.acknowledged_user.name if alert.acknowledged_user else '미지정'}",
                priority=NotificationPriority.MEDIUM,
                role_filter="head_nurse"
            )
            
        except Exception as e:
            logger.error(f"응급 알림 확인 통지 실패: {str(e)}")
    
    def _notify_alert_resolved(self, db: Session, alert: EmergencyAlert):
        """응급 알림 해결 통지"""
        try:
            # 관리자들에게 해결 통지
            self.notification_service.create_ward_notification(
                db=db,
                ward_id=alert.ward_id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"응급상황 해결: {alert.title}",
                message=f"응급상황이 해결되었습니다.\n해결자: {alert.resolved_user.name if alert.resolved_user else '미지정'}",
                priority=NotificationPriority.LOW,
                role_filter="head_nurse"
            )
            
        except Exception as e:
            logger.error(f"응급 알림 해결 통지 실패: {str(e)}")