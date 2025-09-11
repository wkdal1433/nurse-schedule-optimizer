from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def requests_status():
    return {"message": "Requests module - Coming soon"}