"""
수동 편집 모듈
SOLID 원칙에 따라 분리된 수동 편집 기능들
"""

from .entities import (
    ChangeType,
    ChangeRequest,
    ChangeResult,
    ValidationResult,
    ValidationSeverity,
    ShiftAssignmentData,
    EmployeeConstraints,
    ValidationContext,
    NotificationData
)

from .validation_engine import ValidationEngine
from .change_applier import ChangeApplier
from .audit_logger import AuditLogger
from .notification_manager import NotificationManager

__all__ = [
    # 엔티티들
    'ChangeType',
    'ChangeRequest',
    'ChangeResult',
    'ValidationResult',
    'ValidationSeverity',
    'ShiftAssignmentData',
    'EmployeeConstraints',
    'ValidationContext',
    'NotificationData',

    # 서비스 컴포넌트들
    'ValidationEngine',
    'ChangeApplier',
    'AuditLogger',
    'NotificationManager'
]