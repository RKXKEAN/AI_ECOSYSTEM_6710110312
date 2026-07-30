import sys
from minio import Minio
from minio.error import S3Error
from minio.versioningconfig import VersioningConfig, ENABLED

from app.core.config import settings

MINIO_ENDPOINT = settings.MINIO_ENDPOINT
MINIO_ACCESS_KEY = settings.MINIO_ACCESS_KEY
MINIO_SECRET_KEY = settings.MINIO_SECRET_KEY
MINIO_BUCKET = settings.MINIO_BUCKET_NAME
MINIO_SECURE = settings.MINIO_SECURE

OBJECT_NAME = "kean.jpg"  # ใช้ชื่อเดียวกันทุกครั้ง เพื่อทดสอบ versioning


def get_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def enable_versioning(client: Minio, bucket_name: str) -> None:
    """
    Function: enable_versioning
    หน้าที่: เปิดใช้งาน versioning บน bucket
    ใช้ client.set_bucket_versioning(bucket_name, VersioningConfig(ENABLED))
    ต้องเปิดครั้งเดียว หลังจากนั้น bucket จะเก็บทุก version ของไฟล์ที่อัปโหลดซ้ำชื่อ
    """
    client.set_bucket_versioning(bucket_name, VersioningConfig(ENABLED))
    status = client.get_bucket_versioning(bucket_name)
    print(
        f"[+] เปิด versioning สำหรับ bucket '{bucket_name}' แล้ว (status={status.status})"
    )


def upload_file(
    client: Minio, bucket_name: str, local_path: str, object_name: str
) -> str:
    """อัปโหลดไฟล์ คืนค่า version_id ของ object ที่เพิ่งอัปโหลด"""
    result = client.fput_object(bucket_name, object_name, local_path)
    print(
        f"[+] อัปโหลด '{local_path}' เป็น object '{object_name}' -> version_id={result.version_id}"
    )
    return result.version_id


def list_versions(client: Minio, bucket_name: str, object_name: str) -> list[str]:
    """
    Function: list_versions
    หน้าที่: แสดงทุก version ของ object ที่ระบุ
    ใช้ client.list_objects(bucket, prefix=object_name, include_version=True)
    """
    versions = client.list_objects(
        bucket_name, prefix=object_name, include_version=True
    )
    version_ids = []
    print(f"[i] Version ทั้งหมดของ '{object_name}':")
    for v in versions:
        latest_tag = " (latest)" if v.is_latest else ""
        print(
            f"    - version_id={v.version_id}{latest_tag}  last_modified={v.last_modified}"
        )
        version_ids.append(v.version_id)
    return version_ids


def download_file(
    client: Minio,
    bucket_name: str,
    object_name: str,
    save_path: str,
    version_id: str | None = None,
) -> None:
    """
    Function: download_file
    หน้าที่: ดาวน์โหลดไฟล์ โดยเลือกได้ว่าจะระบุ version_id หรือไม่
    ใช้ client.fget_object(bucket, object_name, file_path, version_id=...)
        - ไม่ระบุ version_id (None) -> ได้ไฟล์เวอร์ชันล่าสุด (latest)
        - ระบุ version_id           -> ได้ไฟล์เวอร์ชันนั้นเจาะจง แม้จะถูกอัปโหลดทับไปแล้วก็ตาม
    """
    client.fget_object(bucket_name, object_name, save_path, version_id=version_id)
    tag = f"version_id={version_id}" if version_id else "ไม่ระบุ version (ได้ latest)"
    print(f"[+] ดาวน์โหลดสำเร็จ ({tag}) -> {save_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("วิธีใช้: uv run sandbox/minio_versioning.py <รูปที่1> <รูปที่2>")
        sys.exit(1)

    photo_v1, photo_v2 = sys.argv[1], sys.argv[2]
    client = get_client()

    try:
        # 1. เปิด versioning
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
        enable_versioning(client, MINIO_BUCKET)

        # 2. อัปโหลดรูปที่ 1 (จะกลายเป็น version แรก)
        v1_id = upload_file(client, MINIO_BUCKET, photo_v1, OBJECT_NAME)

        # 3. อัปโหลดรูปที่ 2 ด้วยชื่อ object เดิม (จะกลายเป็น version ที่สอง)
        v2_id = upload_file(client, MINIO_BUCKET, photo_v2, OBJECT_NAME)

        # 4. แสดงทุก version ที่มี
        print()
        list_versions(client, MINIO_BUCKET, OBJECT_NAME)

        # 5. ดึงแบบไม่ระบุ version -> ต้องได้รูปที่ 2 (ล่าสุด)
        print()
        download_file(client, MINIO_BUCKET, OBJECT_NAME, "downloaded_latest.jpg")

        # 6. ดึงแบบระบุ version_id ของรูปที่ 1 -> ต้องได้รูปที่ 1 กลับมา แม้จะถูกทับไปแล้ว
        download_file(
            client, MINIO_BUCKET, OBJECT_NAME, "downloaded_v1.jpg", version_id=v1_id
        )

        print(
            "\n[✓] ทดสอบ versioning สำเร็จ — เทียบไฟล์ downloaded_latest.jpg กับ downloaded_v1.jpg ได้เลยว่าคนละรูปกัน"
        )

    except S3Error as e:
        print(f"[!] เกิดข้อผิดพลาดจาก MinIO: {e}")
        sys.exit(1)
