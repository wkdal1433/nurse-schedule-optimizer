"""
Database Configuration
데이터베이스 설정 및 연결 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import os

# 환경 변수에서 DB URL 가져오기 (기본값은 SQLite)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nurse_scheduler_new.db"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=True  # 개발 환경에서 SQL 로그 출력
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


def get_database_session() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 주입용 함수
    FastAPI의 Depends와 함께 사용
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_tables():
    """
    모든 테이블 생성
    애플리케이션 시작 시 호출
    """
    # 모든 모델을 import하여 Base.metadata에 등록
    from ..persistence.models.nurse_model import NurseModel
    from ..persistence.models.ward_model import WardModel

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    모든 테이블 삭제
    테스트 환경에서 사용
    """
    Base.metadata.drop_all(bind=engine)