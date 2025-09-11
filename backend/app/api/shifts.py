from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def shifts_status():
    return {"message": "Shifts module - Coming soon"}