"""
Use Case: CreateNurseUseCase
간호사 생성 유스케이스
"""
from typing import Dict, Any

from ...domain.entities.nurse import Nurse, NurseRole
from ...domain.repositories.nurse_repository import INurseRepository
from ...domain.value_objects.experience_level import ExperienceLevel
from ...domain.value_objects.employment_type import EmploymentType
from ...shared.exceptions.business_exceptions import BusinessRuleViolationError


class CreateNurseUseCase:
    """간호사 생성 유스케이스"""

    def __init__(self, nurse_repository: INurseRepository):
        self._nurse_repository = nurse_repository

    def execute(self, nurse_data: Dict[str, Any]) -> Nurse:
        """
        간호사 생성 실행

        Args:
            nurse_data: 간호사 생성 데이터

        Returns:
            생성된 간호사 엔티티

        Raises:
            BusinessRuleViolationError: 비즈니스 규칙 위반
        """
        # 1. 직원번호 중복 검사
        existing_nurse = self._nurse_repository.get_by_employee_number(
            nurse_data["employee_number"]
        )
        if existing_nurse:
            raise BusinessRuleViolationError(
                f"직원번호 '{nurse_data['employee_number']}'가 이미 존재합니다"
            )

        # 2. 도메인 객체 생성
        try:
            nurse = Nurse(
                id=None,
                employee_number=nurse_data["employee_number"],
                full_name=nurse_data["full_name"],
                role=NurseRole(nurse_data["role"]),
                employment_type=EmploymentType(nurse_data["employment_type"]),
                experience_level=ExperienceLevel(
                    years=nurse_data["experience_years"],
                    skill_level=nurse_data.get("skill_level", 1)
                ),
                ward_id=nurse_data["ward_id"]
            )
        except ValueError as e:
            raise BusinessRuleViolationError(f"잘못된 간호사 정보: {str(e)}")

        # 3. 추가 비즈니스 규칙 검증
        self._validate_ward_constraints(nurse)

        # 4. 저장
        created_nurse = self._nurse_repository.create(nurse)

        return created_nurse

    def _validate_ward_constraints(self, nurse: Nurse) -> None:
        """병동별 제약 조건 검증"""
        # 병동별 간호사 수 제한 검사 (예: 최대 50명)
        current_count = self._nurse_repository.get_count_by_ward(nurse.ward_id)
        if current_count >= 50:
            raise BusinessRuleViolationError(
                f"병동 {nurse.ward_id}의 간호사 정원이 초과되었습니다 (최대 50명)"
            )

        # 신입 간호사 비율 검사 (예: 전체의 30% 이하)
        if nurse.role == NurseRole.NEW_NURSE:
            ward_nurses = self._nurse_repository.get_all_by_ward(nurse.ward_id)
            new_nurse_count = len([n for n in ward_nurses if n.role == NurseRole.NEW_NURSE])
            total_count = len(ward_nurses) + 1  # 추가될 간호사 포함

            if (new_nurse_count + 1) / total_count > 0.3:
                raise BusinessRuleViolationError(
                    "신입 간호사 비율이 30%를 초과할 수 없습니다"
                )