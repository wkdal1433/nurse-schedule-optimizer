"""
Infrastructure Model: NurseModel
SQLAlchemy 데이터베이스 모델 - Infrastructure Layer
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class NurseModel(Base):
    """간호사 SQLAlchemy 모델 - 순수 데이터 저장용"""

    __tablename__ = "nurses"

    id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # head_nurse, staff_nurse, new_nurse
    employment_type = Column(String, nullable=False)  # full_time, part_time, contract
    experience_years = Column(Integer, nullable=False, default=0)
    skill_level = Column(Integer, nullable=False, default=1)
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 설정
    ward = relationship("WardModel", back_populates="nurses")
    # schedule_assignments = relationship("ScheduleAssignmentModel", back_populates="nurse")

    def __repr__(self):
        return f"<NurseModel(id={self.id}, name='{self.full_name}', role='{self.role}')>"