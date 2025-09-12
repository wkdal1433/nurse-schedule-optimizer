"""
스케줄 관련 데이터 모델
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, date


class ScheduleStatus(str, Enum):
    """스케줄 상태"""
    DRAFT = "draft"
    OPTIMIZING = "optimizing"
    COMPLETED = "completed"
    PUBLISHED = "published"
    LOCKED = "locked"


class OptimizationStatus(str, Enum):
    """최적화 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Schedule(BaseModel):
    """스케줄 모델"""
    id: Optional[int] = None
    name: str
    department: str
    start_date: date
    end_date: date
    status: ScheduleStatus = ScheduleStatus.DRAFT
    total_shifts: int = 0
    assigned_shifts: int = 0
    optimization_score: Optional[float] = None
    compliance_score: Optional[float] = None
    fairness_score: Optional[float] = None
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None


class ScheduleMetrics(BaseModel):
    """스케줄 메트릭스"""
    id: Optional[int] = None
    schedule_id: int
    total_score: float
    compliance_score: float  # 법적/규정 준수
    preference_score: float  # 선호도 만족
    fairness_score: float   # 공정성
    safety_score: float     # 안전성 (최소 인력)
    pattern_penalty: float  # 패턴 위반 패널티
    hard_constraint_violations: int
    soft_constraint_violations: int
    nurse_workload_variance: float
    night_shift_distribution_variance: float


class ScheduleOptimization(BaseModel):
    """스케줄 최적화"""
    id: Optional[int] = None
    schedule_id: int
    algorithm_used: str
    status: OptimizationStatus = OptimizationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    iterations: int = 0
    best_score: Optional[float] = None
    parameters: Dict[str, Any] = {}
    error_message: Optional[str] = None


class ScheduleChange(BaseModel):
    """스케줄 변경 이력"""
    id: Optional[int] = None
    schedule_id: int
    change_type: str  # "manual_edit", "emergency_override", "optimization"
    changed_by: str
    shift_id: Optional[int] = None
    old_assignment: Optional[Dict[str, Any]] = None
    new_assignment: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None


class ScheduleNotification(BaseModel):
    """스케줄 알림"""
    id: Optional[int] = None
    schedule_id: int
    nurse_id: int
    notification_type: str  # "assignment", "change", "reminder"
    title: str
    message: str
    is_read: bool = False
    sent_at: Optional[datetime] = None


class ScheduleStats(BaseModel):
    """스케줄 통계"""
    total_nurses: int
    total_shifts: int
    day_shifts: int
    evening_shifts: int
    night_shifts: int
    off_days: int
    nurse_workload_stats: Dict[str, Any]
    shift_coverage: Dict[str, float]
    compliance_rate: float
    preference_satisfaction_rate: float


class ScheduleCreateRequest(BaseModel):
    """스케줄 생성 요청"""
    name: str
    department: str
    start_date: date
    end_date: date
    created_by: str
    auto_optimize: bool = True


class ScheduleUpdateRequest(BaseModel):
    """스케줄 수정 요청"""
    name: Optional[str] = None
    status: Optional[ScheduleStatus] = None


class ManualEditRequest(BaseModel):
    """수동 편집 요청"""
    schedule_id: int
    shift_id: int
    action: str  # "assign", "unassign", "replace"
    nurse_id: Optional[int] = None
    old_nurse_id: Optional[int] = None
    new_nurse_id: Optional[int] = None
    reason: Optional[str] = None
    edited_by: str


class OptimizationRequest(BaseModel):
    """최적화 요청"""
    schedule_id: int
    algorithm: str = "hybrid_metaheuristic"
    max_iterations: int = 1000
    time_limit_minutes: int = 10
    parameters: Dict[str, Any] = {}


class PublishScheduleRequest(BaseModel):
    """스케줄 발행 요청"""
    schedule_id: int
    notify_nurses: bool = True
    export_format: List[str] = ["pdf"]  # ["pdf", "image", "excel"]


class ScheduleResponse(BaseModel):
    """스케줄 응답 모델"""
    id: int
    name: str
    department: str
    start_date: date
    end_date: date
    status: ScheduleStatus
    total_shifts: int
    assigned_shifts: int
    optimization_score: Optional[float] = None
    compliance_score: Optional[float] = None
    fairness_score: Optional[float] = None
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    locked_at: Optional[datetime] = None
    metrics: Optional[ScheduleMetrics] = None
    stats: Optional[ScheduleStats] = None


class ScheduleDetailResponse(BaseModel):
    """스케줄 상세 응답 모델"""
    schedule: ScheduleResponse
    shifts: List[Dict[str, Any]]
    nurses: List[Dict[str, Any]]
    assignments: List[Dict[str, Any]]
    changes: List[ScheduleChange]
    notifications: List[ScheduleNotification]