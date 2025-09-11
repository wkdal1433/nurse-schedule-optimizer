from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def employees_status():
    return {"message": "Employees module - Coming soon"}