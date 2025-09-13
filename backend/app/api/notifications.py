"""
알림 및 승인 워크플로우 API 엔드포인트
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.notification_models import (
    NotificationType, NotificationPriority, ApprovalStatus
)
from app.services.notification_service import (
    NotificationService, ApprovalWorkflowService, EmergencyAlertService
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Pydantic 모델들
class NotificationCreate(BaseModel):
    recipient_id: int
    notification_type: NotificationType
    title: str
    message: str
    sender_id: Optional[int] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    ward_id: Optional[int] = None
    related_data: Optional[Dict] = None
    expires_hours: Optional[int] = None

class BulkNotificationCreate(BaseModel):
    recipient_ids: List[int]
    notification_type: NotificationType
    title: str
    message: str
    sender_id: Optional[int] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    ward_id: Optional[int] = None
    related_data: Optional[Dict] = None

class WardNotificationCreate(BaseModel):
    ward_id: int
    notification_type: NotificationType
    title: str
    message: str
    sender_id: Optional[int] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    role_filter: Optional[str] = None

class ApprovalRequestCreate(BaseModel):
    request_type: str
    title: str
    description: str
    request_data: Dict
    required_role: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    expires_hours: int = 24

class ApprovalAction(BaseModel):
    reason: Optional[str] = None

class EmergencyAlertCreate(BaseModel):
    alert_type: str
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    ward_id: int
    title: str
    description: str
    action_required: Optional[str] = None
    related_shift_id: Optional[int] = None
    related_employee_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    recipient_id: int
    sender_id: Optional[int]
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True

# 의존성 주입 함수들
def get_notification_service():
    return NotificationService()

def get_approval_service():
    return ApprovalWorkflowService()

def get_emergency_service():
    return EmergencyAlertService()

def get_permission_service():
    return PermissionService()

# TODO: 실제 인증 시스템 구현 후 대체
def get_current_user_id() -> int:
    return 1  # 임시로 user_id 1 반환

# 알림 관련 엔드포인트
@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """새 알림 생성"""
    # 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "basic_schedule_edit"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    expires_at = None
    if notification_data.expires_hours:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(hours=notification_data.expires_hours)
    
    notification = notification_service.create_notification(
        db=db,
        recipient_id=notification_data.recipient_id,
        notification_type=notification_data.notification_type,
        title=notification_data.title,
        message=notification_data.message,
        sender_id=notification_data.sender_id or current_user_id,
        priority=notification_data.priority,
        ward_id=notification_data.ward_id,
        related_data=notification_data.related_data,
        expires_at=expires_at
    )
    
    return notification

@router.post("/bulk", response_model=List[NotificationResponse])
async def create_bulk_notification(
    notification_data: BulkNotificationCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """대량 알림 생성"""
    # 권한 검사 - 대량 알림은 더 높은 권한 필요
    permission_result = permission_service.check_permission(
        db, current_user_id, "bulk_edit"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    notifications = notification_service.create_bulk_notification(
        db=db,
        recipient_ids=notification_data.recipient_ids,
        notification_type=notification_data.notification_type,
        title=notification_data.title,
        message=notification_data.message,
        sender_id=notification_data.sender_id or current_user_id,
        priority=notification_data.priority,
        ward_id=notification_data.ward_id,
        related_data=notification_data.related_data
    )
    
    return notifications

@router.post("/ward", response_model=List[NotificationResponse])
async def create_ward_notification(
    notification_data: WardNotificationCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """병동별 알림 생성"""
    # 권한 검사 - 병동 알림 권한 확인
    permission_result = permission_service.check_permission(
        db, current_user_id, "bulk_edit", ward_id=notification_data.ward_id
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    notifications = notification_service.create_ward_notification(
        db=db,
        ward_id=notification_data.ward_id,
        notification_type=notification_data.notification_type,
        title=notification_data.title,
        message=notification_data.message,
        sender_id=notification_data.sender_id or current_user_id,
        priority=notification_data.priority,
        role_filter=notification_data.role_filter
    )
    
    return notifications

@router.get("/my", response_model=List[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = Query(False, description="읽지 않은 알림만 조회"),
    limit: int = Query(50, ge=1, le=100, description="조회할 알림 수"),
    offset: int = Query(0, ge=0, description="건너뛸 알림 수"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """내 알림 목록 조회"""
    notifications = notification_service.get_user_notifications(
        db=db,
        user_id=current_user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )
    
    return notifications

@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """알림을 읽음으로 표시"""
    notification = notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user_id
    )
    
    return {"message": "알림이 읽음으로 표시되었습니다", "notification_id": notification.id}

# 승인 워크플로우 관련 엔드포인트
@router.post("/approval-requests")
async def create_approval_request(
    request_data: ApprovalRequestCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    approval_service: ApprovalWorkflowService = Depends(get_approval_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """승인 요청 생성"""
    # 기본 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "emergency_request"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    workflow = approval_service.create_approval_request(
        db=db,
        request_type=request_data.request_type,
        requester_id=current_user_id,
        title=request_data.title,
        description=request_data.description,
        request_data=request_data.request_data,
        required_role=request_data.required_role,
        priority=request_data.priority,
        expires_hours=request_data.expires_hours
    )
    
    return {"message": "승인 요청이 생성되었습니다", "workflow_id": workflow.id}

@router.get("/approval-requests/pending")
async def get_pending_approvals(
    limit: int = Query(20, ge=1, le=50, description="조회할 승인 요청 수"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    approval_service: ApprovalWorkflowService = Depends(get_approval_service)
):
    """승인 대기 목록 조회"""
    approvals = approval_service.get_pending_approvals(
        db=db,
        approver_id=current_user_id,
        limit=limit
    )
    
    return approvals

@router.post("/approval-requests/{workflow_id}/approve")
async def approve_request(
    workflow_id: int,
    action_data: ApprovalAction,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    approval_service: ApprovalWorkflowService = Depends(get_approval_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """승인 요청 승인"""
    # 승인 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "approve_swap"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    workflow = approval_service.approve_request(
        db=db,
        workflow_id=workflow_id,
        approver_id=current_user_id,
        approval_reason=action_data.reason
    )
    
    return {"message": "승인이 완료되었습니다", "workflow_id": workflow.id}

@router.post("/approval-requests/{workflow_id}/reject")
async def reject_request(
    workflow_id: int,
    action_data: ApprovalAction,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    approval_service: ApprovalWorkflowService = Depends(get_approval_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """승인 요청 거부"""
    # 승인 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "approve_swap"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    if not action_data.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="거부 사유를 입력해주세요"
        )
    
    workflow = approval_service.reject_request(
        db=db,
        workflow_id=workflow_id,
        approver_id=current_user_id,
        rejection_reason=action_data.reason
    )
    
    return {"message": "승인이 거부되었습니다", "workflow_id": workflow.id}

# 응급 상황 알림 관련 엔드포인트
@router.post("/emergency-alerts")
async def create_emergency_alert(
    alert_data: EmergencyAlertCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    emergency_service: EmergencyAlertService = Depends(get_emergency_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """응급 상황 알림 생성"""
    # 응급 상황 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "emergency_override", ward_id=alert_data.ward_id
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    alert = emergency_service.create_emergency_alert(
        db=db,
        alert_type=alert_data.alert_type,
        severity=alert_data.severity,
        ward_id=alert_data.ward_id,
        title=alert_data.title,
        description=alert_data.description,
        action_required=alert_data.action_required,
        related_shift_id=alert_data.related_shift_id,
        related_employee_id=alert_data.related_employee_id
    )
    
    return {"message": "응급 상황 알림이 생성되었습니다", "alert_id": alert.id}

@router.get("/emergency-alerts/active")
async def get_active_emergency_alerts(
    ward_id: Optional[int] = Query(None, description="병동 ID 필터"),
    severity: Optional[str] = Query(None, description="심각도 필터"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    emergency_service: EmergencyAlertService = Depends(get_emergency_service)
):
    """활성 응급 상황 알림 조회"""
    alerts = emergency_service.get_active_alerts(
        db=db,
        ward_id=ward_id,
        severity=severity
    )
    
    return alerts

@router.post("/emergency-alerts/{alert_id}/acknowledge")
async def acknowledge_emergency_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    emergency_service: EmergencyAlertService = Depends(get_emergency_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """응급 상황 알림 확인"""
    # 기본 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "emergency_request"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    alert = emergency_service.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        user_id=current_user_id
    )
    
    return {"message": "응급 상황 알림이 확인되었습니다", "alert_id": alert.id}

@router.post("/emergency-alerts/{alert_id}/resolve")
async def resolve_emergency_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
    emergency_service: EmergencyAlertService = Depends(get_emergency_service),
    permission_service: PermissionService = Depends(get_permission_service)
):
    """응급 상황 알림 해결"""
    # 관리 권한 검사
    permission_result = permission_service.check_permission(
        db, current_user_id, "emergency_override"
    )
    if not permission_result['allowed']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=permission_result['reason']
        )
    
    alert = emergency_service.resolve_alert(
        db=db,
        alert_id=alert_id,
        user_id=current_user_id
    )
    
    return {"message": "응급 상황 알림이 해결되었습니다", "alert_id": alert.id}