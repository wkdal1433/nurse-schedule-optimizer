from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .models import Base

# 수동 편집 및 스케줄링 관련 모델들

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    
    # 스케줄 기본 정보
    schedule_name = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    status = Column(String, default="draft")  # "draft", "active", "archived"
    
    # 최적화 점수
    optimization_score = Column(Float, default=0.0)
    compliance_score = Column(Float, default=0.0)
    pattern_score = Column(Float, default=0.0)
    preference_score = Column(Float, default=0.0)
    
    # 메타데이터
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 관계 설정
    ward = relationship("Ward")
    creator = relationship("User", foreign_keys=[created_by])
    modifier = relationship("User", foreign_keys=[modified_by])
    assignments = relationship("ShiftAssignment", back_populates="schedule")

class ShiftAssignment(Base):
    __tablename__ = "shift_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # 근무 정보
    shift_date = Column(DateTime, nullable=False)
    shift_type = Column(String, nullable=False)  # "day", "evening", "night", "long_day"
    start_time = Column(String, nullable=True)  # "09:00"
    end_time = Column(String, nullable=True)    # "17:00"
    
    # 수동 편집 관련
    is_manual_assignment = Column(Boolean, default=False)  # 수동으로 배정된 근무
    is_override = Column(Boolean, default=False)          # 제약조건 무시하고 강제 배정
    override_reason = Column(Text, nullable=True)          # 오버라이드 사유
    override_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # 오버라이드한 관리자
    override_at = Column(DateTime, nullable=True)          # 오버라이드 시점
    
    # 변경 이력
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    modified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    original_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)  # 원래 배정된 직원
    
    # 추가 메타데이터
    assignment_weight = Column(Float, default=1.0)  # 배정 가중치 (중요도)
    notes = Column(Text, nullable=True)              # 특별 메모
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    schedule = relationship("Schedule", back_populates="assignments")
    employee = relationship("Employee", foreign_keys=[employee_id])
    original_employee = relationship("Employee", foreign_keys=[original_employee_id])
    override_admin = relationship("User", foreign_keys=[override_by])
    modifier = relationship("User", foreign_keys=[modified_by])

class EmergencyLog(Base):
    __tablename__ = "emergency_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("shift_assignments.id"), nullable=False)
    
    # 응급 상황 정보
    emergency_type = Column(String, nullable=False)  # "illness", "absence", "accident", "family_emergency"
    urgency_level = Column(String, default="medium")  # "low", "medium", "high", "critical"
    
    # 관련 직원들
    original_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    replacement_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # 상황 설명
    reason = Column(Text, nullable=False)
    detailed_description = Column(Text, nullable=True)
    
    # 처리 정보
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resolution_time = Column(DateTime, nullable=True)  # 문제 해결 시간
    status = Column(String, default="pending")  # "pending", "resolved", "escalated"
    
    # 영향 분석
    affected_shifts = Column(JSON)  # 영향받은 다른 근무들
    notification_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    assignment = relationship("ShiftAssignment")
    original_employee = relationship("Employee", foreign_keys=[original_employee_id])
    replacement_employee = relationship("Employee", foreign_keys=[replacement_employee_id])
    admin = relationship("User", foreign_keys=[admin_id])

class ScheduleChangeLog(Base):
    __tablename__ = "schedule_change_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("shift_assignments.id"), nullable=True)
    
    # 변경 정보
    change_type = Column(String, nullable=False)  # "create", "update", "delete", "swap", "override"
    field_changed = Column(String, nullable=True)  # "employee_id", "shift_type", "shift_date"
    
    # 변경 내용
    old_value = Column(JSON, nullable=True)  # 이전 값들
    new_value = Column(JSON, nullable=True)  # 새로운 값들
    
    # 변경 사유 및 컨텍스트
    change_reason = Column(String, nullable=True)  # "manual_edit", "emergency", "optimization"
    admin_notes = Column(Text, nullable=True)
    
    # 메타데이터
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 영향 분석
    score_before = Column(Float, nullable=True)
    score_after = Column(Float, nullable=True)
    violations_introduced = Column(Integer, default=0)
    violations_resolved = Column(Integer, default=0)
    
    # 관계 설정
    schedule = relationship("Schedule")
    assignment = relationship("ShiftAssignment")
    admin = relationship("User", foreign_keys=[changed_by])

class OptimizationHistory(Base):
    __tablename__ = "optimization_history"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    
    # 최적화 실행 정보
    optimization_type = Column(String, nullable=False)  # "initial", "manual_adjustment", "emergency_fix"
    algorithm_used = Column(String, nullable=True)      # "hybrid_metaheuristic", "greedy", "manual"
    
    # 점수 변화
    score_before = Column(Float, nullable=True)
    score_after = Column(Float, nullable=True)
    improvement = Column(Float, nullable=True)  # 개선 정도
    
    # 세부 점수들
    compliance_score = Column(Float, default=0.0)
    pattern_score = Column(Float, default=0.0)
    preference_score = Column(Float, default=0.0)
    role_score = Column(Float, default=0.0)
    
    # 실행 정보
    execution_time_ms = Column(Integer, nullable=True)  # 실행 시간 (밀리초)
    iterations_count = Column(Integer, nullable=True)   # 최적화 반복 횟수
    
    # 메타데이터
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    trigger_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    schedule = relationship("Schedule")
    admin = relationship("User", foreign_keys=[triggered_by])