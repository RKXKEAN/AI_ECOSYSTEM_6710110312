from fastapi import FastAPI
from app.api.v1.routers import storage, auth, health, inference, training
from app.core.database import engine, Base
from app.models.user import User

Base.metadata.create_all(bind=engine)

tags_metadata = [
    {"name": "Auth", "description": "จัดการการยืนยันตัวตนผู้ใช้ ลงทะเบียน เข้าสู่ระบบ และออก JWT Token"},
    {"name": "Storage", "description": "จัดการไฟล์ Object Storage ผ่าน MinIO — อัปโหลด ดาวน์โหลด และดู Version ของไฟล์"},
    {"name": "Health", "description": "ตรวจสอบสถานะของระบบและการเชื่อมต่อไปยัง Service อื่น ๆ"},
    {"name": "Inference", "description": "จำลอง (Mock) การทำนายผลจากโมเดล AI แบบเรียลไทม์และแบบ Batch"},
    {"name": "Training", "description": "จัดการ Pipeline การฝึกสอนโมเดล ผ่านระบบคิวงานเบื้องหลัง (arq + redis)"},
]

app = FastAPI(
    title="AI Ecosystem API",
    description=(
        "Backend API สำหรับระบบ AI Ecosystem ครอบคลุมการจัดการข้อมูล การฝึกสอนโมเดล "
        "การให้บริการโมเดล และการจัดเก็บไฟล์ Object Storage"
    ),
    version="1.0.0",
    contact={
        "name": "6710110312 PATTARAPONG KHAOKHAIKAEW",
        "url": "https://github.com/RKXKEAN/AI_ECOSYSTEM_6710110312",
    },
    license_info={"name": "MIT"},
    openapi_tags=tags_metadata,
)

app.include_router(storage.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(inference.router, prefix="/api/v1")
app.include_router(training.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}


