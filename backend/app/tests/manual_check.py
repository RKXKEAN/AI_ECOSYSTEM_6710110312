import os
import tempfile
from app.services.storage_service import upload_file, list_versions

def run_manual_check():
    # 1. สร้างไฟล์ทดสอบเล็ก ๆ ชั่วคราว (เขียน bytes ธรรมดาลง temp file)
    test_content = b"Hello MinIO, this is a manual test content for versioning check."
    filename = "manual_test_file.txt"
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_content)
        temp_path = temp_file.name
        
    try:
        # อ่าน bytes จากไฟล์ชั่วคราวตามเงื่อนไขที่อาจจะนำไปอัปโหลด
        with open(temp_path, "rb") as f:
            file_bytes = f.read()
            
        print(f"[i] Temporary file created at: {temp_path}")
        print(f"[i] File size to upload: {len(file_bytes)} bytes")
        
        # 2. อัปโหลดไฟล์โดยใช้ signature จาก storage_service: upload_file(file_bytes, filename)
        # ฟังก์ชัน upload_file ใน storage_service.py คืนค่า filename (object_id)
        print(f"[i] Uploading to MinIO using filename: '{filename}'...")
        object_id = upload_file(file_bytes=file_bytes, filename=filename)
        print(f"[OK] Upload successful! object_id (filename): {object_id}")
        
        # 3. แสดงรายการ versions
        print(f"[i] Listing versions for object_id: '{object_id}'...")
        versions = list_versions(object_id=object_id)
        print(f"[OK] Retrieved versions: {versions}")
        
    except Exception as e:
        print(f"[!] Error during manual check: {e}")
        
    finally:
        # ลบไฟล์ temp ที่สร้างขึ้น
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print("[i] Temporary file cleaned up.")

if __name__ == "__main__":
    run_manual_check()
