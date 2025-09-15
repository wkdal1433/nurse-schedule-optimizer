"""
Repository Implementation: NurseRepositoryImpl
간호사 Repository 구현체 - DIP의 구체적 구현
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ....domain.repositories.nurse_repository import INurseRepository
from ....domain.entities.nurse import Nurse, NurseRole
from ....domain.value_objects.experience_level import ExperienceLevel
from ....domain.value_objects.employment_type import EmploymentType
from ..models.nurse_model import NurseModel


class NurseRepositoryImpl(INurseRepository):
    """간호사 Repository 구현체"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, nurse: Nurse) -> Nurse:
        """간호사 생성"""
        db_nurse = NurseModel(
            employee_number=nurse.employee_number,
            full_name=nurse.full_name,
            role=nurse.role.value,
            employment_type=nurse.employment_type.value,
            experience_years=nurse.experience_level.years,
            skill_level=nurse.experience_level.skill_level,
            ward_id=nurse.ward_id,
            is_active=nurse.is_active
        )

        self.session.add(db_nurse)
        self.session.commit()
        self.session.refresh(db_nurse)

        return self._to_domain_entity(db_nurse)

    def get_by_id(self, nurse_id: int) -> Optional[Nurse]:
        """ID로 간호사 조회"""
        db_nurse = self.session.query(NurseModel).filter(
            NurseModel.id == nurse_id
        ).first()

        return self._to_domain_entity(db_nurse) if db_nurse else None

    def get_by_employee_number(self, employee_number: str) -> Optional[Nurse]:
        """직원번호로 간호사 조회"""
        db_nurse = self.session.query(NurseModel).filter(
            NurseModel.employee_number == employee_number
        ).first()

        return self._to_domain_entity(db_nurse) if db_nurse else None

    def get_all_by_ward(self, ward_id: int) -> List[Nurse]:
        """병동별 간호사 목록 조회"""
        db_nurses = self.session.query(NurseModel).filter(
            and_(
                NurseModel.ward_id == ward_id,
                NurseModel.is_active == True
            )
        ).all()

        return [self._to_domain_entity(db_nurse) for db_nurse in db_nurses]

    def get_all_active(self) -> List[Nurse]:
        """활성 간호사 목록 조회"""
        db_nurses = self.session.query(NurseModel).filter(
            NurseModel.is_active == True
        ).all()

        return [self._to_domain_entity(db_nurse) for db_nurse in db_nurses]

    def get_by_employment_type(self, employment_type: EmploymentType) -> List[Nurse]:
        """고용형태별 간호사 조회"""
        db_nurses = self.session.query(NurseModel).filter(
            and_(
                NurseModel.employment_type == employment_type.value,
                NurseModel.is_active == True
            )
        ).all()

        return [self._to_domain_entity(db_nurse) for db_nurse in db_nurses]

    def update(self, nurse: Nurse) -> Nurse:
        """간호사 정보 업데이트"""
        db_nurse = self.session.query(NurseModel).filter(
            NurseModel.id == nurse.id
        ).first()

        if not db_nurse:
            raise ValueError(f"Nurse with id {nurse.id} not found")

        # 도메인 엔티티의 값으로 업데이트
        db_nurse.employee_number = nurse.employee_number
        db_nurse.full_name = nurse.full_name
        db_nurse.role = nurse.role.value
        db_nurse.employment_type = nurse.employment_type.value
        db_nurse.experience_years = nurse.experience_level.years
        db_nurse.skill_level = nurse.experience_level.skill_level
        db_nurse.ward_id = nurse.ward_id
        db_nurse.is_active = nurse.is_active

        self.session.commit()
        self.session.refresh(db_nurse)

        return self._to_domain_entity(db_nurse)

    def delete(self, nurse_id: int) -> bool:
        """간호사 삭제 (소프트 삭제)"""
        db_nurse = self.session.query(NurseModel).filter(
            NurseModel.id == nurse_id
        ).first()

        if not db_nurse:
            return False

        db_nurse.is_active = False
        self.session.commit()
        return True

    def get_count_by_ward(self, ward_id: int) -> int:
        """병동별 간호사 수 조회"""
        return self.session.query(NurseModel).filter(
            and_(
                NurseModel.ward_id == ward_id,
                NurseModel.is_active == True
            )
        ).count()

    def search_by_name(self, name: str) -> List[Nurse]:
        """이름으로 간호사 검색"""
        db_nurses = self.session.query(NurseModel).filter(
            and_(
                NurseModel.full_name.contains(name),
                NurseModel.is_active == True
            )
        ).all()

        return [self._to_domain_entity(db_nurse) for db_nurse in db_nurses]

    def _to_domain_entity(self, db_nurse: NurseModel) -> Nurse:
        """DB 모델을 도메인 엔티티로 변환"""
        return Nurse(
            id=db_nurse.id,
            employee_number=db_nurse.employee_number,
            full_name=db_nurse.full_name,
            role=NurseRole(db_nurse.role),
            employment_type=EmploymentType(db_nurse.employment_type),
            experience_level=ExperienceLevel(
                years=db_nurse.experience_years,
                skill_level=db_nurse.skill_level
            ),
            ward_id=db_nurse.ward_id,
            is_active=db_nurse.is_active,
            created_at=db_nurse.created_at
        )