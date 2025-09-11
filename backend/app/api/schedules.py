from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def schedules_status():
    return {"message": "Schedules module - Coming soon"}