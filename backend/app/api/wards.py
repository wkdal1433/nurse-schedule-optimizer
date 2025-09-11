from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database.connection import get_db
from ..models.models import Ward

router = APIRouter()

class WardCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    shift_rules: Optional[dict] = {}

class WardResponse(BaseModel):
    id: int
    name: str
    description: str
    shift_rules: dict

@router.post("/", response_model=WardResponse)
async def create_ward(
    ward: WardCreate,
    db: Session = Depends(get_db)
):
    """새 병동 생성"""
    
    # 병동명 중복 확인
    existing_ward = db.query(Ward).filter(Ward.name == ward.name).first()
    if existing_ward:
        raise HTTPException(status_code=400, detail="Ward name already exists")
    
    # 기본 근무 규칙 설정
    default_rules = {
        "min_day_staff": 3,
        "min_evening_staff": 2,
        "min_night_staff": 1,
        "max_consecutive_work_days": 5,
        "max_night_shifts_per_week": 3
    }
    
    new_ward = Ward(
        name=ward.name,
        description=ward.description,
        shift_rules={**default_rules, **(ward.shift_rules or {})}
    )
    
    db.add(new_ward)
    db.commit()
    db.refresh(new_ward)
    
    return WardResponse(
        id=new_ward.id,
        name=new_ward.name,
        description=new_ward.description or "",
        shift_rules=new_ward.shift_rules or {}
    )

@router.get("/", response_model=List[WardResponse])
async def get_wards(db: Session = Depends(get_db)):
    """병동 목록 조회"""
    
    wards = db.query(Ward).all()
    
    return [
        WardResponse(
            id=ward.id,
            name=ward.name,
            description=ward.description or "",
            shift_rules=ward.shift_rules or {}
        )
        for ward in wards
    ]

@router.get("/{ward_id}", response_model=WardResponse)
async def get_ward(
    ward_id: int,
    db: Session = Depends(get_db)
):
    """특정 병동 정보 조회"""
    
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    return WardResponse(
        id=ward.id,
        name=ward.name,
        description=ward.description or "",
        shift_rules=ward.shift_rules or {}
    )

@router.post("/init-sample-data")
async def create_sample_wards(db: Session = Depends(get_db)):
    """샘플 병동 데이터 생성 (테스트용)"""
    
    sample_wards = [
        {
            "name": "내과병동",
            "description": "내과계 환자 병동",
            "shift_rules": {
                "min_day_staff": 4,
                "min_evening_staff": 3,
                "min_night_staff": 2,
                "max_consecutive_work_days": 5,
                "max_night_shifts_per_week": 3
            }
        },
        {
            "name": "외과병동", 
            "description": "외과계 환자 병동",
            "shift_rules": {
                "min_day_staff": 5,
                "min_evening_staff": 3,
                "min_night_staff": 2,
                "max_consecutive_work_days": 4,
                "max_night_shifts_per_week": 2
            }
        },
        {
            "name": "중환자실",
            "description": "집중 치료가 필요한 환자 병동",
            "shift_rules": {
                "min_day_staff": 3,
                "min_evening_staff": 3,
                "min_night_staff": 3,
                "max_consecutive_work_days": 3,
                "max_night_shifts_per_week": 4
            }
        }
    ]
    
    created_wards = []
    
    for ward_data in sample_wards:
        # 중복 확인
        existing = db.query(Ward).filter(Ward.name == ward_data["name"]).first()
        if not existing:
            new_ward = Ward(
                name=ward_data["name"],
                description=ward_data["description"],
                shift_rules=ward_data["shift_rules"]
            )
            db.add(new_ward)
            created_wards.append(ward_data["name"])
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Created {len(created_wards)} sample wards",
        "wards": created_wards
    }

@router.get("/status")
async def wards_status():
    return {"message": "Ward management system is ready"}