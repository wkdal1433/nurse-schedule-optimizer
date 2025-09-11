from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database.connection import get_db
from ..models.models import Employee, Ward

router = APIRouter()

class EmployeeCreate(BaseModel):
    employee_number: str
    skill_level: int
    years_experience: int = 0
    ward_id: int
    preferences: Optional[dict] = {}

class EmployeeResponse(BaseModel):
    id: int
    employee_number: str
    skill_level: int
    years_experience: int
    ward_id: int
    preferences: dict
    is_active: bool

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """새 직원 등록"""
    
    # 병동 존재 확인
    ward = db.query(Ward).filter(Ward.id == employee.ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    # 직원번호 중복 확인
    existing_employee = db.query(Employee).filter(
        Employee.employee_number == employee.employee_number
    ).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="Employee number already exists")
    
    new_employee = Employee(
        user_id=1,  # 임시로 1 설정 (User 시스템이 없으므로)
        employee_number=employee.employee_number,
        skill_level=employee.skill_level,
        years_experience=employee.years_experience,
        ward_id=employee.ward_id,
        preferences=employee.preferences
    )
    
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    return EmployeeResponse(
        id=new_employee.id,
        employee_number=new_employee.employee_number,
        skill_level=new_employee.skill_level,
        years_experience=new_employee.years_experience,
        ward_id=new_employee.ward_id,
        preferences=new_employee.preferences or {},
        is_active=new_employee.is_active
    )

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    ward_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """직원 목록 조회"""
    
    query = db.query(Employee)
    
    if ward_id:
        query = query.filter(Employee.ward_id == ward_id)
    if active_only:
        query = query.filter(Employee.is_active == True)
    
    employees = query.all()
    
    return [
        EmployeeResponse(
            id=emp.id,
            employee_number=emp.employee_number,
            skill_level=emp.skill_level,
            years_experience=emp.years_experience,
            ward_id=emp.ward_id,
            preferences=emp.preferences or {},
            is_active=emp.is_active
        )
        for emp in employees
    ]

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """특정 직원 정보 조회"""
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return EmployeeResponse(
        id=employee.id,
        employee_number=employee.employee_number,
        skill_level=employee.skill_level,
        years_experience=employee.years_experience,
        ward_id=employee.ward_id,
        preferences=employee.preferences or {},
        is_active=employee.is_active
    )

@router.post("/bulk-create")
async def create_sample_employees(
    ward_id: int,
    count: int = 5,
    db: Session = Depends(get_db)
):
    """샘플 직원 데이터 대량 생성 (테스트용)"""
    
    # 병동 존재 확인
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    
    if count > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 employees at once")
    
    created_employees = []
    
    for i in range(count):
        employee_number = f"EMP{ward_id:02d}{i+1:03d}"
        
        # 중복 확인
        existing = db.query(Employee).filter(
            Employee.employee_number == employee_number
        ).first()
        if existing:
            continue
        
        new_employee = Employee(
            user_id=1,  # 임시
            employee_number=employee_number,
            skill_level=min(5, max(1, 2 + (i % 4))),  # 2-5 사이 스킬 레벨
            years_experience=i % 10,  # 0-9년 경력
            ward_id=ward_id,
            preferences={
                "preferred_shifts": ["day", "evening"] if i % 2 == 0 else ["evening", "night"],
                "avoid_consecutive_nights": i % 3 == 0
            }
        )
        
        db.add(new_employee)
        created_employees.append(employee_number)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Created {len(created_employees)} employees",
        "employee_numbers": created_employees
    }

@router.get("/status")
async def employees_status():
    return {"message": "Employee management system is ready"}
