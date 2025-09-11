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
    schedules = relationship("Schedule", back_populates="ward")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    schedule_data = Column(JSON, nullable=False)  # 실제 근무표 데이터
    total_score = Column(Float, default=0.0)
    status = Column(String, default="draft")  # "draft", "approved", "published"
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    # 관계 설정
    ward = relationship("Ward", back_populates="schedules")

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