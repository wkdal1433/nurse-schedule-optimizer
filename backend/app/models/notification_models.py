"""
알림 및 승인 워크플로우 관련 모델들
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .models import Base

# 알림 타입 열거형
class NotificationType(str, Enum):
    EMERGENCY_REQUEST = "emergency_request"          # 응급 상황 요청
    SHIFT_CHANGE_REQUEST = "shift_change_request"    # 근무 변경 요청
    SCHEDULE_PUBLISHED = "schedule_published"        # 스케줄 발행
    OVERTIME_ALERT = "overtime_alert"               # 초과 근무 경고
    COMPLIANCE_VIOLATION = "compliance_violation"    # 규정 위반 알림
    SYSTEM_ALERT = "system_alert"                   # 시스템 알림
    APPROVAL_REQUEST = "approval_request"           # 승인 요청
    APPROVAL_RESULT = "approval_result"             # 승인 결과

# 알림 우선순위
class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# 승인 상태
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Notification(Base):
    """알림 모델"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 수신자 정보
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_role = Column(String, nullable=True)  # 특정 역할 대상
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)  # 병동별 알림
    
    # 발신자 정보
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 알림 내용
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # 관련 데이터 (JSON 형태로 저장)
    related_data = Column(JSON, nullable=True)  # 관련된 shift_id, schedule_id 등
    
    # 알림 상태
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 만료시간
    
    # 관계 설정
    recipient = relationship("User", foreign_keys=[recipient_id])
    sender = relationship("User", foreign_keys=[sender_id])

class ApprovalWorkflow(Base):
    """승인 워크플로우 모델"""
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 요청 정보
    request_type = Column(String, nullable=False)  # emergency_override, schedule_change, etc.
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 승인자 정보
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    required_role = Column(String, nullable=True)  # 필요한 승인자 역할
    
    # 승인 내용
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    request_data = Column(JSON, nullable=False)  # 승인 요청 상세 데이터
    
    # 승인 상태
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # 처리 정보
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    approval_reason = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    requester = relationship("User", foreign_keys=[requester_id])
    approver = relationship("User", foreign_keys=[approver_id])

class NotificationTemplate(Base):
    """알림 템플릿 모델"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 템플릿 정보
    template_name = Column(String, unique=True, nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # 템플릿 내용
    title_template = Column(String, nullable=False)  # 제목 템플릿
    message_template = Column(Text, nullable=False)  # 메시지 템플릿
    
    # 전송 설정
    send_email = Column(Boolean, default=False)
    send_sms = Column(Boolean, default=False)
    send_push = Column(Boolean, default=True)
    
    # 메타데이터
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationQueue(Base):
    """알림 발송 큐"""
    __tablename__ = "notification_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    
    # 발송 채널
    channel = Column(String, nullable=False)  # websocket, email, sms, push
    
    # 발송 상태
    status = Column(String, default="pending")  # pending, sent, failed
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 발송 시도 정보
    last_attempt_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    notification = relationship("Notification", back_populates="queue_items")

# Notification 모델에 역방향 관계 추가
Notification.queue_items = relationship("NotificationQueue", back_populates="notification", cascade="all, delete-orphan")

class EmergencyAlert(Base):
    """응급 상황 알림 로그"""
    __tablename__ = "emergency_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 응급 상황 정보
    alert_type = Column(String, nullable=False)  # staff_shortage, medical_emergency, etc.
    severity = Column(String, nullable=False)    # low, medium, high, critical
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    
    # 관련 정보
    related_shift_id = Column(Integer, nullable=True)
    related_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # 알림 내용
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    action_required = Column(Text, nullable=True)
    
    # 상태 관리
    status = Column(String, default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    ward = relationship("Ward")
    related_employee = relationship("Employee")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])
    resolved_user = relationship("User", foreign_keys=[resolved_by])