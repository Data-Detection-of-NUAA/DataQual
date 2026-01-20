from fastapi import APIRouter

optimizer_router = APIRouter(prefix="/optimizer", tags=["优化器"])

@optimizer_router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "module": "optimizer"}