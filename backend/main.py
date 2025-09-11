from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, employees, shifts, schedules, requests, wards
from app.database.connection import engine
from app.models import models

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="간호사 근무표 최적화 시스템",
    description="Hybrid Metaheuristic 알고리즘을 활용한 자동 근무표 생성 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(wards.router, prefix="/api/wards", tags=["Wards"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(shifts.router, prefix="/api/shifts", tags=["Shift Rules"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["Schedules"])
app.include_router(requests.router, prefix="/api/requests", tags=["Shift Requests"])

@app.get("/")
async def root():
    return {
        "message": "간호사 근무표 최적화 시스템",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Hybrid Metaheuristic 알고리즘",
            "실시간 근무표 최적화", 
            "사용자 권한 관리",
            "모바일 최적화 UI"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
