"""
Assignment 05 - System Logging ข้อ 1: Custom Logger ของโปรเจกต์

หลักการออกแบบ (รองรับหลักการพื้นฐานของการทำ Log):
    1. Log Level  - แยกระดับความสำคัญของ log ตามมาตรฐาน Python logging
                    (DEBUG < INFO < WARNING < ERROR < CRITICAL)
                    ทำให้กรองดูได้ว่าอยากเห็น log ระดับไหนบ้าง
    2. Timestamp  - ทุก log entry มีเวลาที่เกิดเหตุการณ์ กำกับด้วย ISO 8601
    3. Structured Format (JSON) - แต่ละ log เป็น JSON object 1 บรรทัด
                    ทำให้นำไปประมวลผลต่อได้ง่าย (เช่น ส่งเข้า log aggregator,
                    ค้นหา/filter ด้วยเครื่องมืออื่น) ต่างจาก plain text ที่อ่านง่าย
                    แต่โปรแกรมแยกวิเคราะห์ยากกว่า
    4. Multiple Output (Console + File) - แสดงผลระหว่าง dev ทาง console
                    และเก็บถาวรลงไฟล์เพื่อดูย้อนหลัง/ส่งต่อวิเคราะห์
    5. Log Rotation - ไฟล์ log จะไม่โตไม่จำกัด มีการหมุนไฟล์ใหม่เมื่อขนาดเกินกำหนด
                    ป้องกันดิสก์เต็ม
    6. Contextual Info - บันทึกชื่อ module/logger ที่มา เพื่อรู้ว่า log มาจากส่วนไหนของระบบ

วิธีใช้:
    from app.core.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Server started", extra={"extra_data": {"port": 8080}})
    logger.error("Database connection failed", extra={"extra_data": {"retry": 3}})
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from pathlib import Path

# ---------- Config ----------
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"
MAX_BYTES = 5 * 1024 * 1024   # 5 MB ต่อไฟล์ ก่อนจะ rotate
BACKUP_COUNT = 5              # เก็บไฟล์เก่าไว้สูงสุด 5 ไฟล์
try:
    from app.core.config import settings
    LOG_LEVEL = settings.LOG_LEVEL.upper()
except ImportError:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# -----------------------------


class JsonFormatter(logging.Formatter):
    """
    Custom Formatter: แปลง LogRecord ให้เป็น JSON string 1 บรรทัดต่อ 1 log entry

    โครงสร้างที่ได้:
        {
            "timestamp": "2026-07-25T10:00:00.123456+00:00",
            "level": "INFO",
            "logger": "core.logger",
            "message": "Server started",
            "module": "logger",
            "line": 42,
            "extra_data": {...}   // ถ้ามีการส่ง extra มาด้วย
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # แนบ extra field ที่ผู้ใช้ระบุมาเอง (ถ้ามี) เช่น logger.info(..., extra={"extra_data": {...}})
        if hasattr(record, "extra_data"):
            log_entry["extra_data"] = record.extra_data

        # แนบ stack trace ถ้าเป็น log ที่มาจาก exception
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Function: get_logger
    หน้าที่: สร้าง (หรือดึง) logger ที่ตั้งค่า handler ไว้ครบทั้ง console และ file

    Handler ที่ตั้งไว้:
        - StreamHandler        -> พิมพ์ log ออกทาง console/terminal แบบ real-time
        - RotatingFileHandler   -> เขียน log ลงไฟล์ logs/app.log
                                   เมื่อไฟล์มีขนาดเกิน MAX_BYTES จะ rotate
                                   เป็นไฟล์ใหม่อัตโนมัติ (เก็บของเก่าไว้ BACKUP_COUNT ไฟล์)

    ป้องกันการเพิ่ม handler ซ้ำ หากถูกเรียก get_logger() ชื่อเดียวกันหลายครั้ง
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # logger ตัวนี้ตั้งค่าไปแล้ว ไม่ต้องเพิ่ม handler ซ้ำ
        return logger

    logger.setLevel(LOG_LEVEL)
    formatter = JsonFormatter()

    # 1. Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File handler (พร้อม rotation)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # ป้องกัน log ซ้ำซ้อนจากการส่งต่อไปยัง root logger
    logger.propagate = False

    return logger


if __name__ == "__main__":
    # เดโมทดสอบ logger ทุกระดับ
    logger = get_logger("demo")

    logger.debug("นี่คือ debug message สำหรับ dev เท่านั้น")
    logger.info("Server started", extra={"extra_data": {"port": 8080, "env": "development"}})
    logger.warning("การเชื่อมต่อ database ช้ากว่าปกติ", extra={"extra_data": {"latency_ms": 850}})
    logger.error("อัปโหลดไฟล์ล้มเหลว", extra={"extra_data": {"bucket": "my-photos", "object": "kean.jpg"}})

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("เกิดข้อผิดพลาดที่ไม่คาดคิด")

    print(f"\nดู log ที่บันทึกได้ที่: {LOG_FILE}")
