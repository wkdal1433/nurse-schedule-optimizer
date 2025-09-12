"""
메인 API 라우터
"""
from fastapi import APIRouter
from .nurses import router as nurses_router
from .shifts import router as shifts_router
from .schedules import router as schedules_router
from .manual_editing import router as manual_editing_router

router = APIRouter()

# 각 모듈별 라우터 포함
router.include_router(nurses_router, prefix="/nurses", tags=["nurses"])
router.include_router(shifts_router, prefix="/shifts", tags=["shifts"])
router.include_router(schedules_router, prefix="/schedules", tags=["schedules"])
router.include_router(manual_editing_router, prefix="/manual", tags=["manual-editing"])


@router.get("/")
async def api_root():
    """API 루트 엔드포인트"""
    return {
        "message": "Nurse Schedule Optimizer API",
        "version": "1.0.0",
        "endpoints": {
            "nurses": "/api/nurses",
            "shifts": "/api/shifts", 
            "schedules": "/api/schedules",
            "manual_editing": "/api/manual"
        }
    }