"""
FastAPI Main Application - Clean Architecture
SOLID 원칙과 Clean Architecture가 적용된 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request

# Infrastructure
from app_new.infrastructure.config.database import create_tables

# API Routes
from app_new.api.v1.controllers.nurse_controller import router as nurse_router

# Shared
from app_new.shared.exceptions.business_exceptions import BusinessException


def create_application() -> FastAPI:
    """
    애플리케이션 팩토리 함수
    의존성 주입과 설정을 통한 애플리케이션 생성
    """

    # FastAPI 앱 생성
    app = FastAPI(
        title="간호사 근무표 최적화 시스템 v2.0",
        description="Clean Architecture + DDD 적용된 간호사 스케줄링 API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # 미들웨어 설정
    setup_middleware(app)

    # 예외 핸들러 설정
    setup_exception_handlers(app)

    # 라우터 등록
    register_routes(app)

    # 데이터베이스 초기화
    setup_database()

    return app


def setup_middleware(app: FastAPI) -> None:
    """미들웨어 설정"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인만 허용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """예외 핸들러 설정"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        """비즈니스 예외 핸들러"""
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "type": "business_error"
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """요청 검증 예외 핸들러"""
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "요청 데이터가 올바르지 않습니다",
                "details": exc.errors(),
                "type": "validation_error"
            }
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception):
        """내부 서버 오류 핸들러"""
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "내부 서버 오류가 발생했습니다",
                "type": "system_error"
            }
        )


def register_routes(app: FastAPI) -> None:
    """API 라우터 등록"""

    # v1 API 라우터들
    app.include_router(
        nurse_router,
        prefix="/api/v1",
        tags=["Nurses"]
    )

    # 헬스 체크 엔드포인트
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "nurse-scheduler-v2",
            "version": "2.0.0"
        }

    # 루트 엔드포인트
    @app.get("/")
    async def root():
        return {
            "message": "간호사 근무표 최적화 시스템 v2.0",
            "architecture": "Clean Architecture + DDD",
            "principles": ["SOLID", "DRY", "KISS"],
            "documentation": "/api/docs"
        }


def setup_database() -> None:
    """데이터베이스 초기화"""
    create_tables()


# 애플리케이션 인스턴스 생성
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=8001,  # 기존 서버와 구분하기 위해 다른 포트 사용
        reload=True,
        log_level="info"
    )