from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def auth_status():
    return {"message": "Auth module - Coming soon"}