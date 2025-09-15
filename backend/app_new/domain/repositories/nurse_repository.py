"""
Repository Interface: NurseRepository
간호사 Repository 인터페이스 - DIP(Dependency Inversion Principle) 적용
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.nurse import Nurse
from ..value_objects.employment_type import EmploymentType


class INurseRepository(ABC):
    """간호사 Repository 인터페이스 - 순수 추상화"""

    @abstractmethod
    def create(self, nurse: Nurse) -> Nurse:
        """간호사 생성"""
        pass

    @abstractmethod
    def get_by_id(self, nurse_id: int) -> Optional[Nurse]:
        """ID로 간호사 조회"""
        pass

    @abstractmethod
    def get_by_employee_number(self, employee_number: str) -> Optional[Nurse]:
        """직원번호로 간호사 조회"""
        pass

    @abstractmethod
    def get_all_by_ward(self, ward_id: int) -> List[Nurse]:
        """병동별 간호사 목록 조회"""
        pass

    @abstractmethod
    def get_all_active(self) -> List[Nurse]:
        """활성 간호사 목록 조회"""
        pass

    @abstractmethod
    def get_by_employment_type(self, employment_type: EmploymentType) -> List[Nurse]:
        """고용형태별 간호사 조회"""
        pass

    @abstractmethod
    def update(self, nurse: Nurse) -> Nurse:
        """간호사 정보 업데이트"""
        pass

    @abstractmethod
    def delete(self, nurse_id: int) -> bool:
        """간호사 삭제"""
        pass

    @abstractmethod
    def get_count_by_ward(self, ward_id: int) -> int:
        """병동별 간호사 수 조회"""
        pass

    @abstractmethod
    def search_by_name(self, name: str) -> List[Nurse]:
        """이름으로 간호사 검색"""
        pass