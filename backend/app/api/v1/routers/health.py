from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.minio_versioning import get_client, MINIO_BUCKET

router = APIRouter(tags=["health"])

@router.get("/health")
def get_health():
    """
    เช็คว่า service รันอยู่ (ไม่ต้องเช็คอะไรซับซ้อน)
    """
    return {"status": "ok"}

@router.get("/health/ready")
def get_health_ready():
    """
    เช็ค readiness แบบละเอียด ลอง connect ไปยัง MinIO
    """
    try:
        client = get_client()
        # เรียก client.bucket_exists()
        client.bucket_exists(MINIO_BUCKET)
        return {"status": "ok", "minio": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "minio": "unreachable"}
        )
