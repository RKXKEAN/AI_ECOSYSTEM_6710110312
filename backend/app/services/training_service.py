import uuid
import random

# ในหน่วยความจำ (module-level, ไม่ต้องต่อ DB จริง) เก็บสถานะ job
_jobs: dict[str, dict] = {}

def create_job(dataset_name: str, epochs: int, model_name: str) -> str:
    """
    สร้าง job_id เก็บสถานะเริ่มต้นเป็น queued และ คืนค่า job_id
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "dataset_name": dataset_name,
        "epochs": epochs,
        "model_name": model_name
    }
    return job_id

def get_job_status(job_id: str) -> dict | None:
    """
    ดึงสถานะของ job และสุ่มขยับ progress
    """
    # MOCK IMPLEMENTATION - งาน training จริงควรใช้ background task queue เช่น Celery/RQ แทนการ mock แบบนี้
    if job_id not in _jobs:
        return None
        
    job = _jobs[job_id]
    
    # หากจำลองเสร็จแล้ว คืนค่าได้ทันที
    if job["status"] == "completed":
        return job

    # สลับจาก queued เป็น running เมื่อมีการดึงข้อมูลครั้งแรก
    if job["status"] == "queued":
        job["status"] = "running"

    # สุ่มขยับ progress ขึ้นทุกครั้งที่ถูกเรียก (เช่น +0.2 ทุกครั้ง จนถึง 1.0 แล้วเปลี่ยน status เป็น "completed")
    increment = round(random.choice([0.2, 0.25, 0.3]), 2)
    next_progress = round(job["progress"] + increment, 2)
    
    if next_progress >= 1.0:
        job["progress"] = 1.0
        job["status"] = "completed"
    else:
        job["progress"] = next_progress
        
    return job
