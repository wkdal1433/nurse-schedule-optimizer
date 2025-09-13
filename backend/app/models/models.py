from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "admin" or "nurse"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employees = relationship("Employee", back_populates="user")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_number = Column(String, unique=True, nullable=False)
    skill_level = Column(Integer, nullable=False)  # 1-5 숙련도
    years_experience = Column(Integer, default=0)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    preferences = Column(JSON)  # 근무 선호도 저장
    
    # 역할 관련 필드
    role = Column(String, nullable=False, default="staff_nurse")  # "head_nurse", "staff_nurse", "new_nurse", "education_coordinator"
    employment_type = Column(String, nullable=False, default="full_time")  # "full_time", "part_time"
    
    # 고용형태별 제약조건
    allowed_shifts = Column(JSON)  # Part-time 근무자의 허용된 근무 시간대
    max_hours_per_week = Column(Integer, default=40)
    max_days_per_week = Column(Integer, default=5)
    
    # 역할별 특성
    can_work_alone = Column(Boolean, default=True)  # 단독 근무 가능 여부
    requires_supervision = Column(Boolean, default=False)  # 감독 필요 여부 (신입간호사)
    can_supervise = Column(Boolean, default=True)  # 감독 가능 여부 (선임간호사)
    specialization = Column(String, nullable=True)  # 전문 분야 (ICU, ER 등)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="employees")
    ward = relationship("Ward", back_populates="employees")
    shift_requests = relationship("ShiftRequest", back_populates="employee")

class Ward(Base):
    __tablename__ = "wards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    shift_rules = Column(JSON)  # 근무 규칙 저장
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employees = relationship("Employee", back_populates="ward")
    schedules = relationship("app.models.scheduling_models.Schedule", back_populates="ward")

class ShiftRequest(Base):
    __tablename__ = "shift_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    request_date = Column(DateTime, nullable=False)
    shift_type = Column(String, nullable=False)  # "day", "evening", "night", "off"
    request_type = Column(String, nullable=False)  # "request", "avoid"
    reason = Column(Text)
    status = Column(String, default="pending")  # "pending", "approved", "denied"
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    employee = relationship("Employee", back_populates="shift_requests")

class ShiftRule(Base):
    __tablename__ = "shift_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)  # NULL이면 전체 적용
    rule_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)  # "hard", "soft"
    category = Column(String, nullable=False)  # "consecutive", "weekly", "legal", "pattern"
    
    # 규칙 파라미터들
    max_consecutive_nights = Column(Integer, default=3)
    max_consecutive_days = Column(Integer, default=5)
    min_rest_days_per_week = Column(Integer, default=1)
    max_hours_per_week = Column(Integer, default=40)
    
    # 패턴 제한
    forbidden_patterns = Column(JSON)  # ["day->night", "night->day"]
    
    # 점수 가중치
    penalty_weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    ward = relationship("Ward", foreign_keys=[ward_id])

class ComplianceViolation(Base):
    __tablename__ = "compliance_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("shift_rules.id"), nullable=False)
    violation_date = Column(DateTime, nullable=False)
    violation_type = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String, default="medium")  # "low", "medium", "high", "critical"
    penalty_score = Column(Float, default=0.0)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    schedule = relationship("Schedule")
    employee = relationship("Employee")

# 패턴 검증 관련 모델들

class ShiftPattern(Base):
    __tablename__ = "shift_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String, nullable=False)  # "day_to_night", "excessive_nights" 등
    pattern_type = Column(String, nullable=False)  # "forbidden", "discouraged", "preferred"
    description = Column(Text)
    
    # 패턴 정의
    sequence_length = Column(Integer, default=2)  # 패턴의 시퀀스 길이
    pattern_definition = Column(JSON)  # 패턴의 구체적 정의
    
    # 점수 및 패널티
    penalty_score = Column(Float, default=0.0)
    severity = Column(String, default="medium")  # "low", "medium", "high", "critical"
    
    # 적용 범위
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)  # NULL이면 전체 병동 적용
    role_specific = Column(JSON)  # 특정 역할에만 적용되는 패턴
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    ward = relationship("Ward", foreign_keys=[ward_id])

class PatternViolation(Base):
    __tablename__ = "pattern_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    pattern_id = Column(Integer, ForeignKey("shift_patterns.id"), nullable=False)
    
    # 위반 정보
    violation_date_start = Column(DateTime, nullable=False)  # 위반 패턴 시작일
    violation_date_end = Column(DateTime, nullable=False)    # 위반 패턴 종료일
    violation_sequence = Column(JSON)  # 위반된 근무 시퀀스 ["day", "night", ...]
    
    # 위반 세부사항
    description = Column(Text)
    severity = Column(String, default="medium")  # "low", "medium", "high", "critical"
    penalty_score = Column(Float, default=0.0)
    
    # 해결 상태
    is_resolved = Column(Boolean, default=False)
    resolution_method = Column(String, nullable=True)  # "manual_fix", "auto_adjust", "override"
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    schedule = relationship("Schedule")
    employee = relationship("Employee")
    pattern = relationship("ShiftPattern")
    resolver = relationship("User", foreign_keys=[resolved_by])

class FatigueScore(Base):
    __tablename__ = "fatigue_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    calculation_date = Column(DateTime, nullable=False)
    
    # 피로도 점수 구성요소
    consecutive_days_score = Column(Float, default=0.0)     # 연속 근무일로 인한 피로도
    night_shift_score = Column(Float, default=0.0)         # 야간 근무로 인한 피로도
    shift_change_score = Column(Float, default=0.0)        # 근무 패턴 변경으로 인한 피로도
    workload_score = Column(Float, default=0.0)            # 업무량으로 인한 피로도
    
    # 총 피로도 점수
    total_fatigue_score = Column(Float, default=0.0)  # 0-100 점수 (높을수록 피로함)
    risk_level = Column(String, default="low")  # "low", "medium", "high", "critical"
    
    # 권장사항
    recommendations = Column(JSON)  # 피로도 개선을 위한 권장사항들
    rest_days_needed = Column(Integer, default=0)  # 권장 휴게일 수
    
    # 계산 기간
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employee = relationship("Employee")

class PatternRecommendation(Base):
    __tablename__ = "pattern_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # 권장사항 정보
    recommendation_type = Column(String, nullable=False)  # "rest_day", "shift_change", "workload_reduce"
    priority = Column(String, default="medium")  # "low", "medium", "high", "urgent"
    
    current_pattern = Column(JSON)     # 현재 근무 패턴
    recommended_pattern = Column(JSON) # 권장 근무 패턴
    
    # 개선 효과 예상치
    fatigue_improvement = Column(Float, default=0.0)      # 피로도 개선 정도
    pattern_score_improvement = Column(Float, default=0.0) # 패턴 점수 개선
    
    # 구현 정보
    implementation_difficulty = Column(String, default="medium")  # "easy", "medium", "hard"
    estimated_impact = Column(Text)  # 예상되는 영향
    
    # 상태 추적
    status = Column(String, default="pending")  # "pending", "accepted", "rejected", "implemented"
    admin_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    schedule = relationship("Schedule")
    employee = relationship("Employee")

class PreferenceTemplate(Base):
    __tablename__ = "preference_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # 근무 선호도 설정
    preferred_shifts = Column(JSON)  # ["day", "evening"] 등
    avoided_shifts = Column(JSON)   # ["night"] 등
    max_night_shifts_per_month = Column(Integer, default=10)
    max_weekend_shifts_per_month = Column(Integer, default=8)
    
    # 근무 패턴 선호도
    preferred_patterns = Column(JSON)  # ["day->day", "evening->off"] 등
    avoided_patterns = Column(JSON)    # ["night->day"] 등
    
    # 연속 근무 선호도
    max_consecutive_days = Column(Integer, default=3)
    min_days_off_after_nights = Column(Integer, default=1)
    
    # 기타 제약 조건
    cannot_work_alone = Column(Boolean, default=False)  # 단독 근무 불가
    needs_senior_support = Column(Boolean, default=False)  # 선임 지원 필요
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employee = relationship("Employee")

class ShiftRequestV2(Base):
    __tablename__ = "shift_requests_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # 요청 기간
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # 요청 유형
    request_type = Column(String, nullable=False)  # "vacation", "shift_preference", "avoid", "pattern_request"
    priority = Column(String, default="normal")    # "low", "normal", "high", "urgent"
    
    # 상세 요청 내용
    shift_type = Column(String, nullable=True)     # 원하는 근무: "day", "evening", "night", "off"
    reason = Column(Text)
    medical_reason = Column(Boolean, default=False)  # 의료적 사유
    
    # 반복 요청 설정
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON)  # {"type": "weekly", "days": ["monday", "friday"]}
    
    # 유연성 설정
    flexibility_level = Column(Integer, default=1)  # 1-5, 1=매우 엄격, 5=매우 유연
    alternative_acceptable = Column(Boolean, default=True)
    
    # 상태 관리
    status = Column(String, default="pending")     # "pending", "approved", "denied", "partially_approved"
    admin_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 관계 설정
    employee = relationship("Employee")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

class PreferenceScore(Base):
    __tablename__ = "preference_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    
    # 선호도 점수 분석
    total_preference_score = Column(Float, default=0.0)
    shift_preference_score = Column(Float, default=0.0)
    pattern_preference_score = Column(Float, default=0.0)
    workload_fairness_score = Column(Float, default=0.0)
    
    # 요청 충족률
    vacation_fulfillment_rate = Column(Float, default=0.0)
    shift_request_fulfillment_rate = Column(Float, default=0.0)
    
    # 월별 통계
    night_shifts_assigned = Column(Integer, default=0)
    weekend_shifts_assigned = Column(Integer, default=0)
    total_hours_assigned = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    employee = relationship("Employee")
    schedule = relationship("Schedule")

class RoleConstraint(Base):
    __tablename__ = "role_constraints"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)  # "head_nurse", "staff_nurse", "new_nurse", "education_coordinator"
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)  # NULL이면 전체 적용
    
    # 역할별 근무 제약조건
    allowed_shifts = Column(JSON)  # 허용된 근무 시간대
    forbidden_shifts = Column(JSON)  # 금지된 근무 시간대
    
    # 인력 관련 제약
    min_per_shift = Column(Integer, default=0)  # 근무당 최소 필요 인원
    max_per_shift = Column(Integer, default=10)  # 근무당 최대 인원
    
    # 페어링 규칙
    requires_pairing_with_roles = Column(JSON)  # 함께 근무해야 하는 역할들
    cannot_work_with_roles = Column(JSON)  # 함께 근무할 수 없는 역할들
    
    # 특별 규칙
    must_have_supervisor = Column(Boolean, default=False)  # 감독자 필요 여부
    can_be_sole_charge = Column(Boolean, default=True)  # 단독 책임자 가능 여부
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    ward = relationship("Ward", foreign_keys=[ward_id])

class SupervisionPair(Base):
    __tablename__ = "supervision_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    supervisor_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    supervisee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    # 페어링 설정
    pairing_type = Column(String, default="mentor")  # "mentor", "buddy", "preceptor"
    is_mandatory = Column(Boolean, default=True)  # 필수 페어링 여부
    
    # 유효 기간
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    supervisor = relationship("Employee", foreign_keys=[supervisor_id])
    supervisee = relationship("Employee", foreign_keys=[supervisee_id])

class EmploymentTypeRule(Base):
    __tablename__ = "employment_type_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    employment_type = Column(String, nullable=False)  # "full_time", "part_time"
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=True)
    
    # 근무시간 제약
    max_hours_per_day = Column(Integer, default=8)
    max_hours_per_week = Column(Integer, default=40)
    max_days_per_week = Column(Integer, default=5)
    max_consecutive_days = Column(Integer, default=5)
    
    # 근무 시간대 제약
    allowed_shift_types = Column(JSON)  # ["day", "evening", "night"]
    forbidden_shift_types = Column(JSON)  # []
    
    # 특별 제약
    weekend_work_allowed = Column(Boolean, default=True)
    night_shift_allowed = Column(Boolean, default=True)
    holiday_work_allowed = Column(Boolean, default=True)
    
    # 고용형태별 우선순위
    scheduling_priority = Column(Integer, default=5)  # 1(최우선) ~ 10(최후순)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    ward = relationship("Ward", foreign_keys=[ward_id])

class RoleViolation(Base):
    __tablename__ = "role_violations"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    
    violation_type = Column(String, nullable=False)  # "role_constraint", "pairing_required", "employment_type"
    violation_date = Column(DateTime, nullable=False)
    description = Column(Text)
    
    # 관련 정보
    required_pairing_role = Column(String, nullable=True)  # 필요한 페어링 역할
    missing_supervisor = Column(Boolean, default=False)
    
    severity = Column(String, default="medium")  # "low", "medium", "high", "critical"
    penalty_score = Column(Float, default=0.0)
    is_resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    schedule = relationship("Schedule")
    employee = relationship("Employee")

# 패턴 검증 관련 모델들

