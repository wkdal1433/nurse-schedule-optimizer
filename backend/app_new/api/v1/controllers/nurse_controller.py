"""
Controller: NurseController
간호사 관련 HTTP API 컨트롤러
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ....infrastructure.config.database import get_database_session
from ....infrastructure.persistence.repositories.nurse_repository_impl import NurseRepositoryImpl
from ....domain.services.scheduling_rules_service import SchedulingRulesService
from ....application.services.nurse_application_service import NurseApplicationService
from ....shared.exceptions.business_exceptions import (
    BusinessException,
    EntityNotFoundError,
    BusinessRuleViolationError
)
from ..dtos.nurse_dtos import (
    CreateNurseRequestDTO,
    UpdateNurseRequestDTO,
    NurseResponseDTO,
    NurseListResponseDTO,
    SchedulingValidationRequestDTO,
    SchedulingValidationResponseDTO,
    ErrorResponseDTO
)

router = APIRouter()


class NurseController:
    """간호사 컨트롤러 - 순수 Presentation Layer"""

    def __init__(self):
        self.router = router

    def _get_nurse_service(self, session: Session) -> NurseApplicationService:
        """의존성 주입을 통한 서비스 인스턴스 생성"""
        nurse_repository = NurseRepositoryImpl(session)
        scheduling_rules_service = SchedulingRulesService()
        return NurseApplicationService(nurse_repository, scheduling_rules_service)

    def _map_to_response_dto(self, nurse) -> NurseResponseDTO:
        """도메인 엔티티를 응답 DTO로 변환"""
        return NurseResponseDTO(
            id=nurse.id,
            employee_number=nurse.employee_number,
            full_name=nurse.full_name,
            role=nurse.role.value,
            employment_type=nurse.employment_type.value,
            experience_years=nurse.experience_level.years,
            skill_level=nurse.experience_level.skill_level,
            ward_id=nurse.ward_id,
            is_active=nurse.is_active,
            created_at=nurse.created_at
        )


# 컨트롤러 인스턴스 생성
nurse_controller = NurseController()


@router.post(
    "/nurses",
    response_model=NurseResponseDTO,
    status_code=201,
    summary="간호사 생성",
    description="새로운 간호사를 등록합니다"
)
def create_nurse(
    request: CreateNurseRequestDTO,
    session: Session = Depends(get_database_session)
):
    """간호사 생성 API"""
    try:
        service = nurse_controller._get_nurse_service(session)

        # 요청 DTO를 도메인 데이터로 변환
        nurse_data = {
            "employee_number": request.employee_number,
            "full_name": request.full_name,
            "role": request.role.value,
            "employment_type": request.employment_type.value,
            "experience_years": request.experience_years,
            "skill_level": request.skill_level or 1,
            "ward_id": request.ward_id
        }

        # 비즈니스 로직 실행
        created_nurse = service.create_nurse(nurse_data)

        # 응답 DTO로 변환
        return nurse_controller._map_to_response_dto(created_nurse)

    except BusinessException as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponseDTO(
                error_code=e.error_code,
                message=e.message
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponseDTO(
                error_code="INTERNAL_ERROR",
                message="내부 서버 오류가 발생했습니다"
            ).dict()
        )


@router.get(
    "/nurses/{nurse_id}",
    response_model=NurseResponseDTO,
    summary="간호사 조회",
    description="ID로 간호사 정보를 조회합니다"
)
def get_nurse(
    nurse_id: int = Path(..., gt=0, description="간호사 ID"),
    session: Session = Depends(get_database_session)
):
    """간호사 단일 조회 API"""
    try:
        service = nurse_controller._get_nurse_service(session)
        nurse = service.get_nurse_by_id(nurse_id)
        return nurse_controller._map_to_response_dto(nurse)

    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get(
    "/nurses",
    response_model=NurseListResponseDTO,
    summary="간호사 목록 조회",
    description="조건에 따른 간호사 목록을 조회합니다"
)
def get_nurses(
    ward_id: Optional[int] = Query(None, gt=0, description="병동 ID"),
    name: Optional[str] = Query(None, min_length=1, description="이름 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    session: Session = Depends(get_database_session)
):
    """간호사 목록 조회 API"""
    try:
        service = nurse_controller._get_nurse_service(session)

        # 검색 조건 구성
        search_criteria = {}
        if ward_id:
            search_criteria["ward_id"] = ward_id
        if name:
            search_criteria["name"] = name

        # 간호사 목록 조회
        nurses = service.search_nurses(search_criteria)

        # 페이징 처리 (실제 구현에서는 Repository에서 페이징 처리)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_nurses = nurses[start_idx:end_idx]

        # 응답 DTO 변환
        nurse_dtos = [nurse_controller._map_to_response_dto(nurse) for nurse in paged_nurses]

        return NurseListResponseDTO(
            nurses=nurse_dtos,
            total_count=len(nurses),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.put(
    "/nurses/{nurse_id}",
    response_model=NurseResponseDTO,
    summary="간호사 정보 수정",
    description="간호사 정보를 수정합니다"
)
def update_nurse(
    nurse_id: int,
    request: UpdateNurseRequestDTO,
    session: Session = Depends(get_database_session)
):
    """간호사 정보 수정 API"""
    try:
        service = nurse_controller._get_nurse_service(session)

        # None이 아닌 필드만 업데이트 데이터로 구성
        update_data = {}
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.experience_years is not None:
            update_data["experience_years"] = request.experience_years

        updated_nurse = service.update_nurse(nurse_id, update_data)
        return nurse_controller._map_to_response_dto(updated_nurse)

    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.delete(
    "/nurses/{nurse_id}",
    status_code=204,
    summary="간호사 비활성화",
    description="간호사를 비활성화합니다 (소프트 삭제)"
)
def deactivate_nurse(
    nurse_id: int,
    session: Session = Depends(get_database_session)
):
    """간호사 비활성화 API"""
    try:
        service = nurse_controller._get_nurse_service(session)
        success = service.deactivate_nurse(nurse_id)

        if not success:
            raise HTTPException(status_code=404, detail="간호사를 찾을 수 없습니다")

    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post(
    "/nurses/validate-scheduling",
    response_model=SchedulingValidationResponseDTO,
    summary="스케줄링 요구사항 검증",
    description="병동의 스케줄링 요구사항 충족 여부를 검증합니다"
)
def validate_scheduling_requirements(
    request: SchedulingValidationRequestDTO,
    session: Session = Depends(get_database_session)
):
    """스케줄링 요구사항 검증 API"""
    try:
        service = nurse_controller._get_nurse_service(session)

        validation_result = service.validate_scheduling_requirements(
            ward_id=request.ward_id,
            min_nurses_per_shift=request.min_nurses_per_shift,
            shift_types=request.shift_types
        )

        # 추천 사항 생성
        recommendations = []
        if not validation_result["sufficient_night_staff"]:
            recommendations.append("야간 근무 가능 간호사를 추가로 배치하세요")
        if not validation_result["sufficient_supervisors"]:
            recommendations.append("감독 가능한 선임 간호사를 배치하세요")

        return SchedulingValidationResponseDTO(
            **validation_result,
            recommendations=recommendations
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="내부 서버 오류")