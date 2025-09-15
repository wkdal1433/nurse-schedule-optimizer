"""
Application Service: NurseApplicationService
간호사 관련 애플리케이션 서비스
"""
from typing import List, Optional, Dict, Any

from ...domain.entities.nurse import Nurse
from ...domain.repositories.nurse_repository import INurseRepository
from ...domain.services.scheduling_rules_service import SchedulingRulesService
from ..use_cases.create_nurse_use_case import CreateNurseUseCase
from ...shared.exceptions.business_exceptions import EntityNotFoundError


class NurseApplicationService:
    """간호사 애플리케이션 서비스 - 여러 Use Case 조합"""

    def __init__(
        self,
        nurse_repository: INurseRepository,
        scheduling_rules_service: SchedulingRulesService
    ):
        self._nurse_repository = nurse_repository
        self._scheduling_rules_service = scheduling_rules_service
        self._create_nurse_use_case = CreateNurseUseCase(nurse_repository)

    def create_nurse(self, nurse_data: Dict[str, Any]) -> Nurse:
        """간호사 생성"""
        return self._create_nurse_use_case.execute(nurse_data)

    def get_nurse_by_id(self, nurse_id: int) -> Nurse:
        """간호사 ID로 조회"""
        nurse = self._nurse_repository.get_by_id(nurse_id)
        if not nurse:
            raise EntityNotFoundError(f"간호사 ID {nurse_id}를 찾을 수 없습니다")
        return nurse

    def get_nurses_by_ward(self, ward_id: int) -> List[Nurse]:
        """병동별 간호사 목록 조회"""
        return self._nurse_repository.get_all_by_ward(ward_id)

    def update_nurse(self, nurse_id: int, update_data: Dict[str, Any]) -> Nurse:
        """간호사 정보 업데이트"""
        # 1. 기존 간호사 조회
        existing_nurse = self.get_nurse_by_id(nurse_id)

        # 2. 업데이트 데이터 적용
        updated_nurse = self._apply_updates(existing_nurse, update_data)

        # 3. 비즈니스 규칙 재검증
        # (필요시 추가 검증 로직)

        # 4. 저장
        return self._nurse_repository.update(updated_nurse)

    def deactivate_nurse(self, nurse_id: int) -> bool:
        """간호사 비활성화 (소프트 삭제)"""
        # 1. 간호사 존재 확인
        nurse = self.get_nurse_by_id(nurse_id)

        # 2. 스케줄링 영향 검사
        self._check_scheduling_impact_before_deactivation(nurse)

        # 3. 비활성화 실행
        return self._nurse_repository.delete(nurse_id)

    def search_nurses(self, search_criteria: Dict[str, Any]) -> List[Nurse]:
        """간호사 검색"""
        if "name" in search_criteria:
            return self._nurse_repository.search_by_name(search_criteria["name"])
        elif "ward_id" in search_criteria:
            return self._nurse_repository.get_all_by_ward(search_criteria["ward_id"])
        else:
            return self._nurse_repository.get_all_active()

    def validate_scheduling_requirements(
        self,
        ward_id: int,
        min_nurses_per_shift: int,
        shift_types: List[str]
    ) -> Dict[str, Any]:
        """스케줄링 요구사항 검증"""
        nurses = self._nurse_repository.get_all_by_ward(ward_id)

        return self._scheduling_rules_service.validate_minimum_staff_requirement(
            nurses, min_nurses_per_shift, shift_types
        )

    def get_workload_distribution(self, ward_id: int) -> Dict[int, float]:
        """병동별 업무 부하 분석"""
        nurses = self._nurse_repository.get_all_by_ward(ward_id)
        return self._scheduling_rules_service.calculate_workload_distribution(nurses)

    def _apply_updates(self, nurse: Nurse, update_data: Dict[str, Any]) -> Nurse:
        """업데이트 데이터를 간호사 엔티티에 적용"""
        # 실제 구현에서는 도메인 객체의 불변성을 고려하여
        # 새로운 객체를 생성하거나 빌더 패턴을 사용할 수 있음
        # 여기서는 간단히 기존 객체의 속성을 업데이트

        if "full_name" in update_data:
            nurse.full_name = update_data["full_name"]
        if "experience_years" in update_data:
            from ...domain.value_objects.experience_level import ExperienceLevel
            nurse.experience_level = ExperienceLevel.from_years(update_data["experience_years"])

        return nurse

    def _check_scheduling_impact_before_deactivation(self, nurse: Nurse) -> None:
        """간호사 비활성화 전 스케줄링 영향 검사"""
        ward_nurses = self._nurse_repository.get_all_by_ward(nurse.ward_id)

        # 비활성화 후 최소 인력 요구사항 충족 여부 검사
        remaining_nurses = [n for n in ward_nurses if n.id != nurse.id]

        if len(remaining_nurses) < 3:  # 최소 3명 필요
            from ...shared.exceptions.business_exceptions import BusinessRuleViolationError
            raise BusinessRuleViolationError(
                "간호사 비활성화 시 최소 인력 요구사항을 충족할 수 없습니다"
            )