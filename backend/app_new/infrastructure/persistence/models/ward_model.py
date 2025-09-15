"""
Infrastructure Model: WardModel
병동 SQLAlchemy 모델
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from .nurse_model import Base


class WardModel(Base):
    """병동 SQLAlchemy 모델"""

    __tablename__ = "wards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    min_nurses_per_shift = Column(Integer, nullable=False, default=3)
    shift_types = Column(JSON, nullable=False, default=["DAY", "EVENING", "NIGHT"])
    is_active = Column(Boolean, default=True)

    # 관계 설정
    nurses = relationship("NurseModel", back_populates="ward")

    def __repr__(self):
        return f"<WardModel(id={self.id}, name='{self.name}')>"