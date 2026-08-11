from fastapi import FastAPI
from app.api.v1.routers import storage, auth, health, inference, training, annotation, models, data, monitoring
from app.core.database import engine, Base
from app.models.user import User
from app.models.model_registry import Model, ModelVersion
from app.models.dataset import Dataset
from app.models.feedback import Feedback

Base.metadata.create_all(bind=engine)

tags_metadata = [
    {"name": "Auth", "description": "จัดการการยืนยันตัวตนผู้ใช้ ลงทะเบียน เข้าสู่ระบบ และออก JWT Token"},
    {"name": "Storage", "description": "จัดการไฟล์ Object Storage ผ่าน MinIO — อัปโหลด ดาวน์โหลด และดู Version ของไฟล์"},
    {"name": "Health", "description": "ตรวจสอบสถานะของระบบและการเชื่อมต่อไปยัง Service อื่น ๆ"},
    {"name": "Inference", "description": "จำลอง (Mock) การทำนายผลจากโมเดล AI แบบเรียลไทม์และแบบ Batch"},
    {"name": "Training", "description": "จัดการ Pipeline การฝึกสอนโมเดล ผ่านระบบคิวงานเบื้องหลัง (arq + redis)"},
    {"name": "Annotation", "description": "เชื่อมต่อ Label Studio เพื่อดึงข้อมูล Project และ Task สำหรับการติดป้ายกำกับข้อมูล"},
    {"name": "Model Registry", "description": "จัดการเวอร์ชันของโมเดล AI และ Metadata การประเมินผล"},
    {"name": "Data Management", "description": "จัดการการนำเข้าและรายการชุดข้อมูล (Dataset) ของระบบ"},
    {"name": "Monitoring", "description": "ตรวจสอบ Log, Feedback, และความเบี่ยงเบนของโมเดล (Model Drift)"},
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
app.include_router(annotation.router, prefix="/api/v1")
app.include_router(models.router)
app.include_router(data.router)
app.include_router(monitoring.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}





