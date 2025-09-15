"""
Business Exceptions
비즈니스 예외 클래스들
"""


class BusinessException(Exception):
    """기본 비즈니스 예외"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class BusinessRuleViolationError(BusinessException):
    """비즈니스 규칙 위반 예외"""

    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")


class EntityNotFoundError(BusinessException):
    """엔티티를 찾을 수 없음 예외"""

    def __init__(self, message: str):
        super().__init__(message, "ENTITY_NOT_FOUND")


class DuplicateEntityError(BusinessException):
    """중복 엔티티 예외"""

    def __init__(self, message: str):
        super().__init__(message, "DUPLICATE_ENTITY")


class InsufficientPermissionError(BusinessException):
    """권한 부족 예외"""

    def __init__(self, message: str):
        super().__init__(message, "INSUFFICIENT_PERMISSION")


class SchedulingConflictError(BusinessException):
    """스케줄링 충돌 예외"""

    def __init__(self, message: str, conflicts: list = None):
        super().__init__(message, "SCHEDULING_CONFLICT")
        self.conflicts = conflicts or []