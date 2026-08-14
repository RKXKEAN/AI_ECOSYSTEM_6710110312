# Knowledge Base: AI Ecosystem Backend Service

ไฟล์นี้สรุปรายละเอียดทางเทคนิคทั้งหมดของโปรเจกต์ FastAPI Backend สำหรับระบบนิเวศปัญญาประดิษฐ์ (AI Ecosystem) เพื่อใช้เป็นบริบทข้อมูลดิบสำหรับเขียนรายงานความคืบหน้าและการทดลองพัฒนาโปรเจกต์ (Assignment)

---

## 1. ภาพรวมโปรเจกต์
- **ชื่อโปรเจกต์**: AI Ecosystem Backend API
- **ผู้พัฒนา**: 6710110312 Pattarapong Khaokhaikaew
- **วัตถุประสงค์**:
  โปรเจกต์นี้เป็น Backend Service สำหรับระบบ AI Ecosystem พัฒนาขึ้นด้วย FastAPI และภาษา Python 3.13 มีหน้าที่บริหารจัดการวงจรชีวิตของระบบ AI (AI Lifecycle Management) ครอบคลุมการทำงาน 8 API domains หลัก:
  1. **Auth**: ยืนยันตัวตนผู้ใช้ ลงทะเบียน เข้าสู่ระบบ และออก JWT Token
  2. **Storage**: จัดการไฟล์บน Object Storage ผ่าน MinIO พร้อมระบบ Versioning
  3. **Annotation**: เชื่อมต่อกับ Label Studio SDK เพื่อดึงข้อมูลโครงการและทาสก์ป้ายกำกับข้อมูล
  4. **Model Registry**: ลงทะเบียน ประเมิน และจัดเก็บเวอร์ชันโมเดล AI
  5. **Data Management**: นำเข้าและจัดการรายการชุดข้อมูล (Datasets)
  6. **Monitoring**: ติดตามการบันทึก Feedback ความเบี่ยงเบนข้อมูล (Drift) และรายงานระบบ
  7. **Training**: จัดการคิวงานฝึกสอนโมเดลเป็น Background Tasks ด้วย arq และ Redis
  8. **Inference**: บริการคำนวณผลทำนายจำลองผ่านโมเดลในระบบ

---

## 2. สถาปัตยกรรมที่เลือกใช้
โปรเจกต์นี้เลือกใช้สถาปัตยกรรมแบบ **Layered Architecture** เพื่อแยกความรับผิดชอบอย่างชัดเจน (Separation of Concerns) ทำให้ระบบมีความยืดหยุ่นสูง สามารถทดสอบแต่ละส่วนแยกกันได้ง่าย (Testability) และพัฒนา Domain ใหม่เพิ่มเข้าไปได้โดยไม่ส่งผลกระทบต่อส่วนเดิม

การแบ่งชั้นหน้าที่ของสถาปัตยกรรมมีดังนี้:
1. **API Routers (`app/api/v1/routers/`)**: เลเยอร์ระดับบนสุดที่คอยรับ-ส่ง HTTP Requests และจัดรูป Responses ทำหน้าที่ระบุเส้นทาง Path, HTTP Method, HTTP Exception และจัดการ Auth/Permission ผ่าน Dependency Injection โดยไม่มี logic ทางธุรกิจในเลเยอร์นี้
2. **Services (`app/services/`)**: บรรจุ Logic ทางธุรกิจ (Business Logic) ทั้งหมด เป็นจุดเชื่อมโยงหลักในการประสานงานระหว่างฐานข้อมูล คลังข้อมูลไฟล์ MinIO หรือการส่งงานไปยังระบบคิวเบื้องหลัง
3. **Schemas (`app/schemas/`)**: รับผิดชอบเรื่องการตรวจสอบความถูกต้องของโครงสร้างข้อมูลเข้า (Request Validation) และจัดรูปแบบข้อมูลออก (Response Serialization) โดยใช้ Pydantic Models
4. **Models (`app/models/`)**: นิยามโครงสร้างตารางข้อมูลในระดับฐานข้อมูลเชิงสัมพันธ์ผ่าน Object-Relational Mapping (ORM) ของ SQLAlchemy เพื่อแมปคลาสภาษา Python เข้ากับตารางบน PostgreSQL
5. **Core (`app/core/`)**: ระบบโครงสร้างพื้นฐานหลักและการตั้งค่าส่วนกลางของแอปพลิเคชัน (Config, Database Engine, Security JWT, Logger และ MinIO Client)
6. **Worker (`app/worker/`)**: ส่วนงานประมวลผลเบื้องหลัง (Background Worker) ที่รับงานจาก Redis Queue มาประมวลผลจำลองการฝึกสอนเพื่อไม่ให้บล็อกการทำงานหลักของ HTTP API

---

## 3. โครงสร้างโฟลเดอร์แบบเต็ม
โครงสร้างโฟลเดอร์จริงของโปรเจกต์นี้ในเครื่องแสดงได้ดังนี้:

```text
D:/AI_ECOSYSTEM/PF_Waritorn/AI_ECOSYSTEM_6710110312/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routers/
│   │   │           ├── __init__.py
│   │   │           ├── annotation.py
│   │   │           ├── auth.py
│   │   │           ├── data.py
│   │   │           ├── health.py
│   │   │           ├── inference.py
│   │   │           ├── models.py
│   │   │           ├── monitoring.py
│   │   │           ├── storage.py
│   │   │           └── training.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── logger.py
│   │   │   ├── minio_versioning.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── dataset.py
│   │   │   ├── feedback.py
│   │   │   ├── model_registry.py
│   │   │   ├── training_job.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── annotation.py
│   │   │   ├── auth.py
│   │   │   ├── data.py
│   │   │   ├── inference.py
│   │   │   ├── model_registry.py
│   │   │   ├── monitoring.py
│   │   │   ├── storage.py
│   │   │   └── training.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── annotation_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── data_service.py
│   │   │   ├── inference_service.py
│   │   │   ├── model_registry_service.py
│   │   │   ├── monitoring_service.py
│   │   │   ├── storage_service.py
│   │   │   └── training_service.py
│   │   ├── tests/
│   │   ├── worker/
│   │   │   ├── __init__.py
│   │   │   └── tasks.py
│   │   ├── .env.example
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── logs/
│   │   └── app.log
│   ├── utils/
│   ├── .env
│   ├── .python-version
│   ├── Dockerfile
│   ├── README.md
│   ├── main.py
│   ├── pyproject.toml
│   └── uv.lock
├── dev/
├── diagrams/
│   ├── overview.drawio
│   ├── overview.png
│   ├── overview_new.drawio
│   └── overview_new.png
├── docs/
│   └── api-snapshots/
│       ├── api-list.csv
│       └── api-list.xlsx
├── frontend/
├── logss/
│   ├── label-studio.log
│   ├── minio.log
│   ├── postgres.log
│   └── redis.log
├── postgres-init/
│   └── init-db.sql
├── sandbox/
│   ├── db_test.py
│   ├── enqueue_job.py
│   ├── ls_list_projects.py
│   ├── ls_list_tasks.py
│   ├── test_settings.py
│   ├── test_storage_service.py
│   └── worker_settings.py
├── scripts/
│   └── openapi_to_csv.py
├── compose.yml
└── README.md
```

---

## 4. Library ที่ใช้ทั้งหมด

วิเคราะห์รายการไลบรารีที่ระบุไว้ใน `pyproject.toml` และ `backend/app/requirements.txt` ของตัวโปรเจกต์:

| ชื่อ Library | แหล่งอ้างอิง | หน้าที่และการใช้งาน | เชื่อมกับ Component ใด |
| :--- | :--- | :--- | :--- |
| `fastapi` | `requirements.txt` | เว็บบอร์ดเฟรมเวิร์กสร้าง HTTP REST API | Core API App |
| `uvicorn[standard]` | `requirements.txt` | ASGI Server สำหรับรัน FastAPI Web App | Core API App |
| `arq` | `pyproject.toml` | ระบบจัดการ Queue งานเบื้องหลังแบบอะซิงโครนัส | `worker/tasks.py`, `training_service` |
| `redis` | `pyproject.toml` | Client เชื่อมต่อ Redis สำหรับระบบคิวงาน | `training_service`, Redis DB |
| `sqlalchemy` | `pyproject.toml` | ORM สำหรับเชื่อมโยงออบเจกต์ภาษา Python กับฐานข้อมูลเชิงสัมพันธ์ | Models, Services, PostgreSQL |
| `psycopg2-binary` | `pyproject.toml` | Database Driver สำหรับใช้คุยกับ PostgreSQL | `core/database.py` |
| `pydantic-settings` | `pyproject.toml` | โหลดตัวแปรสภาพแวดล้อม (.env) มาตรวจสอบและใช้งานในรูปแบบ Class Settings | `core/config.py` |
| `minio` | `pyproject.toml` | Python SDK สำหรับติดต่อ Object Storage (MinIO) | `core/minio_versioning.py`, `storage_service` |
| `label-studio-sdk` | `pyproject.toml` | API Client สำหรับติดต่อไปยัง Label Studio | `annotation_service` |
| `python-jose[cryptography]` | `requirements.txt` | ถอดรหัส ลงลายมือชื่อ และยืนยัน JWT Token | `core/security.py`, `auth_service` |
| `passlib[bcrypt]` / `bcrypt` | `requirements.txt`/`pyproject.toml` | แฮชรหัสผ่านผู้ใช้และตรวจสอบรหัสผ่านแบบ Secure Hashing | `auth_service` |
| `python-multipart` | `requirements.txt` | รองรับการรับข้อมูลไฟล์ส่งผ่าน Form Data | `api/v1/routers/storage.py` |
| `requests` | `pyproject.toml` | เรียก HTTP Requests ไปยัง URL ภายนอก | `scripts/openapi_to_csv.py` |
| `openpyxl` | `pyproject.toml` | อ่านและเขียนเอกสารสเปรดชีตตระกูล Excel (.xlsx) | `scripts/openapi_to_csv.py` |
| `python-dotenv` | `requirements.txt` | อ่านไฟล์ตัวแปรสภาพแวดล้อม `.env` เข้าสู่ `os.environ` | `core/config.py` |

---

## 5. Docker Compose Services

รายละเอียด Services ในไฟล์ `compose.yml` ที่รูทโปรเจกต์:

| Service | Image | Ports | Environment Variables | Volumes และ Mounts | Logging Config |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **redis** | `redis:8.8.0-alpine` | `6379:6379` | *ไม่มีการตั้งค่า* | `redis-data:/data` | driver: `json-file`<br>max-size: "10m"<br>max-file: "3" |
| **postgres** | `postgres:15-alpine` | `5432:5432` | `POSTGRES_USER=admin`<br>`POSTGRES_PASSWORD=password123`<br>`POSTGRES_DB=ai_database` | `postgresql-data:/var/lib/postgresql/data`<br>`./postgres-init:/docker-entrypoint-initdb.d` | driver: `json-file`<br>max-size: "10m"<br>max-file: "3" |
| **label-studio** | `heartexlabs/label-studio:latest` | `8080:8080` | `DJANGO_DB=default`<br>`POSTGRE_NAME=ai_database`<br>`POSTGRE_USER=admin`<br>`POSTGRE_PASSWORD=password123`<br>`POSTGRE_PORT=5432`<br>`POSTGRE_HOST=postgres` | `label-studio-data:/label-studio/data` | driver: `json-file`<br>max-size: "10m"<br>max-file: "3" |
| **minio** | `quay.io/minio/minio:latest` | `9000:9000`<br>`9001:9001` | `MINIO_ROOT_USER=admin`<br>`MINIO_ROOT_PASSWORD=password123` | `minio-data:/data` | driver: `json-file`<br>max-size: "10m"<br>max-file: "3" |
| **backend** | *สร้างจาก Dockerfile ท้องถิ่น* | `8000:8000` | `APP_NAME=MyBackend`<br>`DEBUG=True`<br>`DATABASE_URL=postgresql+psycopg2://admin:password123@postgres:5432/ai_backend`<br>`REDIS_HOST=redis`<br>`REDIS_PORT=6379`<br>`LABEL_STUDIO_URL=http://label-studio:8080`<br>`LABEL_STUDIO_API_KEY=371dcdb2d27198b823438b40ca567d1e2d48c1da`<br>`MINIO_ENDPOINT=minio:9000`<br>`MINIO_ACCESS_KEY=admin`<br>`MINIO_SECRET_KEY=password123`<br>`MINIO_BUCKET=my-photos`<br>`MINIO_SECURE=false` | *ไม่มีการแมปพาร์ทภายนอก* | *ไม่ได้ระบุตัวขับใน compose.yml* |

*หมายเหตุ: Service `backend` จะทำหน้าที่ build รูปภาพผ่าน Dockerfile ที่โฟลเดอร์ `./backend` และกำหนดให้ขึ้นตรงกับ `minio` (ผ่านการเช็ค `condition: service_healthy` ของ minio healthcheck)*

---

## 6. Database Schema

โครงสร้างตารางและโมเดลฐานข้อมูลของโปรเจกต์นี้ทำงานอยู่บนฐานข้อมูล PostgreSQL (ชื่อ `ai_backend` สำหรับเก็บข้อมูลแอปพลิเคชัน และ `ai_database` สำหรับให้ Label Studio ใช้งานแยกกัน):

### 1. ตาราง `users` (`app/models/user.py`)
เก็บข้อมูลบัญชีผู้ใช้และระดับการเข้าใช้งาน
- `id` (Integer): Primary Key (Auto increment)
- `username` (String): Unique, Indexed, Nullable=False (ชื่อบัญชีผู้ใช้)
- `hashed_password` (String): Nullable=False (รหัสผ่านที่ผ่านการแฮชด้วย bcrypt)
- `role` (String): Nullable=False, Default="user" (สิทธิ์ของผู้ใช้ เช่น "user", "admin")
- `created_at` (DateTime): Nullable=False, server_default=func.now() (เวลาที่สมัครสมาชิก)

### 2. ตาราง `datasets` (`app/models/dataset.py`)
เก็บข้อมูลการนำเข้าชุดข้อมูลของระบบ
- `id` (Integer): Primary Key (Auto increment)
- `name` (String): Unique, Indexed, Nullable=False (ชื่อ dataset)
- `storage_path` (String): Nullable=False (พาธที่เก็บ เช่น พาธใน MinIO หรือบนเครื่อง)
- `status` (String): Nullable=False, Default="pending" (สถานะนำเข้า เช่น "pending", "ready", "processing")
- `row_count` (Integer): Nullable=True (จำนวนแถวข้อมูล)
- `created_at` (DateTime): Nullable=False, server_default=func.now() (เวลาที่บันทึกข้อมูล)

### 3. ตาราง `feedbacks` (`app/models/feedback.py`)
เก็บบันทึกการประเมินคุณภาพของคำทำนายโมเดลโดยผู้ใช้
- `id` (Integer): Primary Key (Auto increment)
- `prediction_id` (String): Nullable=False (ไอดีของคำทำนายที่ใช้อ้างอิง)
- `is_correct` (Boolean): Nullable=False (ผลตรวจสอบว่าผลทำนายถูกต้องหรือไม่)
- `comment` (String): Nullable=True (คำวิจารณ์หรือคำแนะนำเพิ่มเติมจากผู้ใช้)
- `created_at` (DateTime): Nullable=False, server_default=func.now() (เวลาที่ส่ง feedback)

### 4. ตาราง `models` (`app/models/model_registry.py`)
เก็บข้อมูลตัวตนหลักของโมเดล AI ที่ลงทะเบียนในระบบ
- `id` (Integer): Primary Key (Auto increment)
- `name` (String): Nullable=False (ชื่อของโมเดล)
- `created_by` (String): Nullable=False (ชื่อผู้สร้างหรือเจ้าของโมเดล)
- `dataset_used` (String): Nullable=False (ชื่อ dataset ที่ใช้ฝึกสอนโมเดลนี้)
- `created_at` (DateTime): Nullable=False, server_default=func.now() (เวลาลงทะเบียน)
- **Relationships**:
  - `versions`: เชื่อมโยงแบบ One-to-Many ไปยังตาราง `ModelVersion` (พร้อมคำสั่ง cascade="all, delete-orphan")

### 5. ตาราง `model_versions` (`app/models/model_registry.py`)
เก็บรายละเอียดแยกแต่ละเวอร์ชันย่อยของโมเดล
- `id` (Integer): Primary Key (Auto increment)
- `model_id` (Integer): ForeignKey("models.id", ondelete="CASCADE"), Nullable=False
- `version` (String): Nullable=False (รหัสเวอร์ชัน เช่น "v1", "v2")
- `metrics` (JSON): Nullable=False, Default=dict (ค่าตัววัดผลประเมิน เช่น loss, accuracy)
- `storage_path` (String): Nullable=False (พาธที่เก็บไฟล์ weight โมเดลบน MinIO)
- `is_deployed` (Boolean): Nullable=False, Default=False (สถานะการเปิดให้บริการโมเดล)
- `created_at` (DateTime): Nullable=False, server_default=func.now() (เวลาที่อัปโหลดเวอร์ชัน)
- **Relationships**:
  - `model`: ความสัมพันธ์กลับไปยังออบเจกต์แม่ในตาราง `Model`

### 6. ตาราง `training_jobs` (`app/models/training_job.py`)
เก็บบันทึกสถานะงานฝึกสอนโมเดลที่ส่งทำงานเบื้องหลัง
- `id` (Integer): Primary Key (Auto increment)
- `job_id` (String): Unique, Indexed, Nullable=False (ไอดีของ Task งานเบื้องหลังที่ดึงมาจาก arq)
- `status` (String): Nullable=False, Default="queued" (สถานะคิวงาน เช่น "queued", "running", "complete", "failed")
- `hyperparameters` (JSON): Nullable=True (พารามิเตอร์ส่งฝึกสอน เช่น epochs, dataset_name, learning rate)
- `created_at` (DateTime): Nullable=False, server_default=func.now() (เวลาส่งคิวงาน)
- `updated_at` (DateTime): Nullable=True, onupdate=func.now() (เวลาที่อัพเดทสถานะล่าสุด)

---

## 7. API ทั้ง 8 Domain

โครงสร้าง endpoints ตัวแปรขาเข้า และบริการภายในโปรเจกต์ที่สอดคล้องตาม API Spec จริงในโค้ด:

### 1. Domain: Auth (การจัดการสิทธิ์และสมาชิก)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/auth.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/auth` (จากการระบุ `/api/v1` ตอน include_router และกำหนด `/auth` ที่ตัวเราเตอร์)
- **Endpoints**:
  1. `POST /register`: ลงทะเบียนสมาชิกผู้ใช้ใหม่
     - ข้อมูลขาเข้า (Request Schema): `RegisterRequest` (username, password, role)
     - ผลลัพธ์กลับ (Response Schema): `UserResponse` (username, role)
     - บริการหลักที่เรียกใช้: `auth_service.register_user()` (บันทึกลงตาราง `users` แฮชรหัสผ่านด้วย `passlib[bcrypt]`)
  2. `POST /login`: เข้าสู่ระบบและขอรหัสผ่าน JWT Token
     - ข้อมูลขาเข้า (Request Schema): `LoginRequest` (username, password)
     - ผลลัพธ์กลับ (Response Schema): `TokenResponse` (access_token, token_type)
     - บริการหลักที่เรียกใช้: `auth_service.authenticate_user()`, `core/security.create_access_token()`
  3. `GET /me` และ `GET /users/me`: แสดงรายละเอียดโปรไฟล์ผู้ใช้ปัจจุบัน
     - ข้อมูลขาเข้า: ผ่าน Security Dependency `get_current_user`
     - ผลลัพธ์กลับ (Response Schema): `UserResponse`
     - บริการหลักที่เรียกใช้: `core/security.verify_token()`, `auth_service.get_user_by_username()`
  4. `GET /admin-only` และ `GET /users/admin-only`: เส้นทางทดสอบสิทธิ์สำหรับแอดมินเท่านั้น
     - ข้อมูลขาเข้า: ตรวจสอบความถูกต้องของสิทธิ์ผู้ใช้และสิทธิ์ต้องเป็น `admin`
     - ผลลัพธ์กลับ (Response Schema): `UserResponse`
     - เงื่อนไขภายใน: ตรวจสอบหาก `current_user.role != "admin"` จะส่งกลับ HTTP 403 Forbidden

### 2. Domain: Storage (บริการคลังวัตถุไฟล์)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/storage.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/storage`
- **Endpoints**:
  1. `POST /upload`: อัปโหลดไฟล์ขึ้นระบบเก็บคลังข้อมูล
     - ข้อมูลขาเข้า: รับไฟล์เดี่ยวในรูปแบบ Multipart Form Data (`UploadFile`)
     - ผลลัพธ์กลับ (Response Schema): `UploadResponse` (object_name, version_id)
     - บริการหลักที่เรียกใช้: `storage_service.upload_file()`, `storage_service.list_versions()`
  2. `GET /objects`: รายงานชื่อวัตถุไฟล์ทั้งหมดใน bucket ล่าสุด
     - ผลลัพธ์กลับ (Response Schema): `ObjectListResponse` (รายการ ObjectInfo ประกอบด้วย object_name, size, last_modified)
     - บริการหลักที่เรียกใช้: `storage_service.list_objects()`
  3. `GET /{object_name}/versions`: ตรวจเช็คเวอร์ชันทั้งหมดของไฟล์เป้าหมาย
     - ข้อมูลขาเข้า (Path Parameter): `object_name` (ชื่อไฟล์)
     - ผลลัพธ์กลับ (Response Schema): `VersionsResponse` (object_name, versions)
     - บริการหลักที่เรียกใช้: `storage_service.list_versions()`
  4. `GET /{object_name}`: ดาวน์โหลดตัวข้อมูลไฟล์ออกมา (ดาวน์โหลดเวอร์ชันย้อนหลังได้)
     - ข้อมูลขาเข้า (Path & Query Parameter): `object_name` (ชื่อไฟล์), `version_id` (ไอดีเวอร์ชันไฟล์ - ตัวเลือกเสริม)
     - ผลลัพธ์กลับ: `StreamingResponse` ส่งคืนไบนารีข้อมูลไฟล์ตรง ๆ
     - บริการหลักที่เรียกใช้: `storage_service.get_file()`
  5. `POST /buckets`: สร้าง Bucket ใหม่แยกภายใน MinIO
     - ข้อมูลขาเข้า (Request Schema): `CreateBucketRequest` (bucket_name)
     - ผลลัพธ์กลับ (Response Schema): `CreateBucketResponse` (bucket_name, created)
     - บริการหลักที่เรียกใช้: `storage_service.create_bucket()`
  6. `POST /presigned-url`: ร้องขอลิงก์ชั่วคราวในการเข้าถึงหรืออัปโหลดไฟล์
     - ข้อมูลขาเข้า (Request Schema): `PresignedUrlRequest` (object_name, method, expires_minutes)
     - ผลลัพธ์กลับ (Response Schema): `PresignedUrlResponse` (url, expires_minutes)
     - บริการหลักที่เรียกใช้: `storage_service.generate_presigned_url()`

### 3. Domain: Annotation (การทำงานร่วมกับระบบจัดทำป้ายกำกับ)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/annotation.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/annotation`
- **Endpoints**:
  1. `GET /projects`: ดึงรายชื่อโครงการติดฉลากข้อมูลทั้งหมดจาก Label Studio
     - ผลลัพธ์กลับ (Response Schema): `ProjectListResponse` (รายการ ProjectInfo ประกอบด้วย id, title, task_count)
     - บริการหลักที่เรียกใช้: `annotation_service.list_projects()` (ทำงานผ่าน SDK Client ของ Label Studio)
  2. `GET /projects/{project_id}/tasks`: ดึงทาสก์ทั้งหมดภายใต้โครงการที่กำหนด
     - ข้อมูลขาเข้า (Path Parameter): `project_id`
     - ผลลัพธ์กลับ (Response Schema): `TaskListResponse` (project_id, รายการ TaskInfo)
     - บริการหลักที่เรียกใช้: `annotation_service.list_tasks()`

### 4. Domain: Model Registry (คลังเก็บโมเดล AI)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/models.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/models` (ไม่มี Prefix เพิ่มเติมใน main.py)
- **Endpoints**:
  1. `POST /register`: ลงทะเบียนข้อมูลโมเดลตัวแรกพร้อมสร้างเวอร์ชัน v1 ให้ทันที
     - ข้อมูลขาเข้า (Request Schema): `ModelRegisterRequest` (name, created_by, dataset_used)
     - ผลลัพธ์กลับ (Response Schema): `ModelRegisterResponse`
     - บริการหลักที่เรียกใช้: `model_registry_service.register_model()` (สร้าง Model และ ModelVersion ลงฐานข้อมูล)
  2. `GET /{model_id}/versions`: ตรวจสอบเวอร์ชันย่อยของโมเดลทั้งหมด
     - ข้อมูลขาเข้า (Path Parameter): `model_id`
     - ผลลัพธ์กลับ (Response Schema): `ModelVersionListResponse`
     - บริการหลักที่เรียกใช้: `model_registry_service.get_versions()`
  3. `PUT /{id}/metrics`: ปรับปรุงตัวประเมินประสิทธิภาพในเวอร์ชันที่กำหนด
     - ข้อมูลขาเข้า (Path & Query & Body): `id` (model_id), `version_id` (ไอดีเวอร์ชัน), `UpdateMetricsRequest` (metrics ในรูปแบบ Dict/JSON)
     - ผลลัพธ์กลับ (Response Schema): `ModelVersionInfo`
     - บริการหลักที่เรียกใช้: `model_registry_service.update_metrics()`
  4. `POST /{id}/deploy`: สั่งเปิดใช้งานเวอร์ชันของโมเดลที่กำหนด (จำลองเป็นสถานะ deployed = True)
     - ข้อมูลขาเข้า (Path & Query): `id` (model_id), `version_id` (ไอดีเวอร์ชัน)
     - ผลลัพธ์กลับ (Response Schema): `DeployResponse` (model_id, version_id, deployed, message)
     - บริการหลักที่เรียกใช้: `model_registry_service.deploy_model()`

### 5. Domain: Data Management (การจัดคลังนำเข้าชุดข้อมูล)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/data.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/data` (ไม่มี Prefix เพิ่มเติมใน main.py)
- **Endpoints**:
  1. `POST /ingest`: ส่งข้อมูลพิกัดที่เก็บชุดข้อมูลเพื่อเริ่มระบบจัดการ
     - ข้อมูลขาเข้า (Request Schema): `IngestRequest` (name, storage_path)
     - ผลลัพธ์กลับ (Response Schema): `IngestResponse`
     - บริการหลักที่เรียกใช้: `data_service.ingest_dataset()` (ตรวจสอบชื่อซ้ำและบันทึกลงตาราง `datasets` สถานะเริ่มต้นเป็น "pending")
  2. `GET /datasets`: เรียกดูรายชื่อชุดข้อมูลทั้งหมดที่บันทึกไว้ในระบบ
     - ผลลัพธ์กลับ (Response Schema): `DatasetListResponse`
     - บริการหลักที่เรียกใช้: `data_service.list_datasets()`

### 6. Domain: Monitoring (ระบบตรวจความเรียบร้อยและรายงานสถิติ)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/monitoring.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/monitoring` (ไม่มี Prefix เพิ่มเติมใน main.py)
- **Endpoints**:
  1. `POST /feedback`: ส่งความคิดเห็นประเมินความถูกต้องผลทำนายโมเดล
     - ข้อมูลขาเข้า (Request Schema): `FeedbackRequest` (prediction_id, is_correct, comment)
     - ผลลัพธ์กลับ (Response Schema): `FeedbackResponse`
     - บริการหลักที่เรียกใช้: `monitoring_service.submit_feedback()` (บันทึกลงตาราง `feedbacks`)
  2. `GET /drift`: แสดงคะแนนการหลุดพ้นทิศทางชุดข้อมูลฝึกสอน (Data Drift)
     - ผลลัพธ์กลับ (Response Schema): `DriftResponse` (status, drift_score, message)
     - บริการหลักที่เรียกใช้: `monitoring_service.get_drift()` (Mock logic คืนค่าสถานะปกติและ Drift Score = 0.02)
  3. `GET /dashboard`: ดึงสถิติตัวชี้วัดระบบโดยรวม
     - ผลลัพธ์กลับ (Response Schema): `DashboardResponse` (uptime_seconds, total_predictions, active_alerts)
     - บริการหลักที่เรียกใช้: `monitoring_service.get_dashboard()` (ดึงจำนวนข้อมูลการบันทึก feedback ทั้งหมดมาแทนค่า total_predictions)
  4. `GET /logs`: ดึงประวัติ Logs ล่าสุดของแอปพลิเคชัน
     - ข้อมูลขาเข้า (Query Parameter): `limit` (จำนวนแถวประวัติที่ต้องการดึง สูงสุด 50 entry)
     - ผลลัพธ์กลับ (Response Schema): `LogsResponse` (รายการ LogEntry)
     - บริการหลักที่เรียกใช้: `monitoring_service.get_logs()` (วิเคราะห์และอ่านบรรทัด JSON จากท้ายไฟล์ `app.log` ทีละแถวแบบย้อนกลับโดยไม่มีการเขียน log ซ้ำลงเครื่องระหว่างดึง ป้องกันคิวการประมวลผลวนไม่รู้จบ)

### 7. Domain: Training (การฝึกฝนระบบคิวประมวลผลเบื้องหลัง)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/training.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/training` (จากการระบุ `/api/v1` ตอน include_router และกำหนด `/training` ที่ตัวเราเตอร์)
- **Endpoints**:
  1. `POST /jobs`: สั่งฝึกสอนระบบด้วยพารามิเตอร์ที่กำหนดและโยนเข้าคิว
     - ข้อมูลขาเข้า (Request Schema): `TrainingJobRequest` (dataset_name, epochs, model_name)
     - ผลลัพธ์กลับ (Response Schema): `TrainingJobResponse` (job_id, status)
     - บริการหลักที่เรียกใช้: `training_service.enqueue_training()` (ลงบันทึกในฐานข้อมูลตาราง `training_jobs` จากนั้นสั่ง Enqueue ไปยัง Redis queue ผ่าน `arq` และบันทึก ID จริงของ Task กลับมา)
  2. `GET /jobs/{job_id}` และ `GET /jobs/{job_id}/metrics`: ตรวจเช็คสถานะความก้าวหน้าการฝึกระบบคิวงาน
     - ข้อมูลขาเข้า (Path Parameter): `job_id` (ไอดีงานเบื้องหลังที่ได้รับจาก arq)
     - ผลลัพธ์กลับ (Response Schema): `TrainingJobStatus` (job_id, status, progress, dataset_name)
     - บริการหลักที่เรียกใช้: `training_service.get_job_metrics()` (ดึงสถานะงานจากฐานข้อมูลและคำนวณ Progress: complete = 1.0, running = 0.5, อื่นๆ = 0.0)

### 8. Domain: Inference (การให้บริการประเมินจำลองผลทำนาย)
- **ไฟล์เราเตอร์**: `backend/app/api/v1/routers/inference.py`
- **เส้นทางหลัก (Prefix)**: `/api/v1/inference` (จากการระบุ `/api/v1` ตอน include_router และกำหนด `/inference` ที่ตัวเราเตอร์)
- **Endpoints**:
  1. `GET /models`: ตรวจสอบรายชื่อโมเดล AI ที่พร้อมเปิดทำการประมวลผลทำนายผลลัพธ์
     - ผลลัพธ์กลับ: รายการ `ModelInfo`
     - บริการหลักที่เรียกใช้: `inference_service.list_models()` (Mock รายชื่อโมเดล "default" และ "sentiment-analyzer")
  2. `POST /predict`: ส่งเนื้อหาข้อมูลดิบเพื่อทำนายผลลัพธ์จำลอง
     - ข้อมูลขาเข้า (Request Schema): `PredictRequest` (input_text, model_name)
     - ผลลัพธ์กลับ (Response Schema): `PredictResponse` (model_name, prediction, confidence)
     - บริการหลักที่เรียกใช้: `inference_service.predict()` (สุ่มค่าความมั่นใจ 0.7 - 0.99 และสร้างข้อความตอบกลับสะท้อนความยาวข้อมูลนำเข้า)

### เส้นทางเพิ่มเติมในแอปพลิเคชัน
- `GET /health` (ใน `main.py` ทางเข้าหลัก): คืนค่า `{"status": "ok"}`
- `GET /api/v1/health` (ใน `health.py`): ตรวจสอบสถานะการเชื่อมต่อว่าทำงานปกติ
- `GET /api/v1/health/ready` (ใน `health.py`): ตรวจสอบ readiness ของระบบโดยพยายามทำเชื่อมต่อกับ MinIO Object Storage (หาก MinIO ไม่ทำงานจะส่งกลับ HTTP 503 Service Unavailable คืนค่า degraded)

---

## 8. Custom Logger

ระบบสร้าง Log ออกแบบขึ้นมาเพื่อรองรับหลักการทำบันทึกข้อมูลอย่างเป็นระบบ (Structured Logging) ที่สามารถวิเคราะห์ต่อได้ง่าย อยู่ภายใต้ไฟล์ `app/core/logger.py` มีการกำหนดค่าและวิธีการดังนี้:

### หลักการออกแบบที่ใช้งานจริง
1. **Timestamp ตามมาตรฐาน**: บันทึกในรูปของเวลาสากล ISO 8601 รวม UTC offset (ตัวอย่าง: `2026-08-12T06:50:00.123456+00:00`)
2. **รูปแบบโครงสร้าง JSON (Structured Format)**: ตัวบันทึกถูกแปลงเป็นออบเจกต์ JSON 1 บรรทัดต่อ 1 log entry ทำให้อ่านด้วยสคริปต์แยกวิเคราะห์ง่าย
3. **การแยกประเภทระดับความสำคัญ (Log Levels)**: รองรับการคัดกรองตั้งแต่ DEBUG, INFO, WARNING, ERROR ไปจนถึง CRITICAL
4. **Log Rotation**: กำหนดให้ไฟล์ผลลัพธ์สูงสุดไม่เกิน 5MB ต่อไฟล์ และจะย้ายไฟล์เก่าเก็บไว้สูงสุด 5 ไฟล์ป้องกันพื้นที่เก็บข้อมูลของดิสก์ในระบบเต็ม
5. **Output สองช่องทาง**: พิมพ์ออกหน้าจอคอนโซลเรียลไทม์ระหว่างพัฒนา (Console) และบันทึกลงไฟล์สะสมถาวร (`logs/app.log`)

### โครงสร้างข้อมูล Log
ตัวประมวลผล `JsonFormatter` จะจับตัวแปรจาก `logging.LogRecord` แล้วสร้างรูปแบบ JSON ดังนี้:
```json
{
  "timestamp": "2026-08-12T06:50:00.123456+00:00",
  "level": "INFO",
  "logger": "app.api.v1.routers.auth",
  "message": "API: User 'kean' registered successfully",
  "module": "auth",
  "line": 43,
  "extra_data": { "env": "development" }, // ข้อมูลเสริม (หากระบุผ่าน extra={"extra_data": ...})
  "exception": "..." // รายละเอียด stack trace (หากเกิดข้อผิดพลาดและบันทึกผ่าน logger.exception())
}
```

---

## 9. MinIO และ Versioning

ระบบประมวลผลไฟล์ Object Storage บน MinIO มีการตั้งค่าเปิดใช้งานประวัติเวอร์ชันไฟล์ (Bucket Versioning) เพื่อป้องกันข้อมูลสูญหายเมื่ออัปโหลดไฟล์ซ้ำในชื่อเดียวกัน:

### ขั้นตอนการทำงานที่สำคัญ
1. **การเปิดระบบ Versioning บน Bucket อัตโนมัติ**: 
   เมื่อเริ่ม Backend Service ตัวโปรเจกต์จะเรียก `storage_service` ตรวจสอบความถูกต้องของ Bucket หากไม่พบระบบจะดำเนินการทำ `make_bucket` และทำการสั่งเปิดการเก็บเวอร์ชันด้วย `enable_versioning()`
2. **การอัปโหลด (Upload)**:
   ในแอปพลิเคชันจะแปลงข้อมูลไบนารีเป็น Temporary File และเรียกใช้ `fput_object()` จาก MinIO ซึ่งจะส่งค่าผลลัพธ์ออกมาเป็นออบเจกต์ที่มีคุณสมบัติ `version_id` จากนั้นนำค่า `version_id` นี้เก็บในฐานข้อมูลหรือส่งคืนผู้ใช้งาน
3. **การดูเวอร์ชัน (List Versions)**:
   เรียกใช้ `client.list_objects(bucket_name, prefix=object_name, include_version=True)` เพื่อดึงประวัติไฟล์ย้อนหลังทั้งหมดมาแสดงผล
4. **การดาวน์โหลด (Download)**:
   ระบุพารามิเตอร์ `version_id` ส่งให้ฟังก์ชัน `fget_object()` ในกรณีที่ระบุ ระบบจะดึงไฟล์จากประวัติเวอร์ชันเป้าหมายนั้น ๆ ขึ้นมา แม้ปัจจุบันไฟล์ดังกล่าวจะถูกเขียนทับด้วยข้อมูลใหม่ไปแล้วก็ตาม หากไม่ระบุ (None) ระบบจะโหลดเวอร์ชันล่าสุดมาให้

### ตัวอย่างโค้ดสำคัญ (`app/core/minio_versioning.py`)
```python
from minio import Minio
from minio.versioningconfig import VersioningConfig, ENABLED

# 1. การเปิดใช้งาน Versioning บน Bucket
def enable_versioning(client: Minio, bucket_name: str) -> None:
    client.set_bucket_versioning(bucket_name, VersioningConfig(ENABLED))

# 2. การอัปโหลดไฟล์พร้อมรับค่า Version ID ล่าสุด
def upload_file(client: Minio, bucket_name: str, local_path: str, object_name: str) -> str:
    result = client.fput_object(bucket_name, object_name, local_path)
    return result.version_id

# 3. การแสดงรายการเวอร์ชันทั้งหมดของ Object
def list_versions(client: Minio, bucket_name: str, object_name: str) -> list[str]:
    versions = client.list_objects(bucket_name, prefix=object_name, include_version=True)
    version_ids = []
    for v in versions:
        version_ids.append(v.version_id)
    return version_ids

# 4. การดึงดาวน์โหลดเจาะจง Version ID
def download_file(client: Minio, bucket_name: str, object_name: str, save_path: str, version_id: str | None = None) -> None:
    client.fget_object(bucket_name, object_name, save_path, version_id=version_id)
```

---

## 10. Docker Logging

การตั้งค่าเพื่อจำกัดและบันทึกประวัติการใช้คอนเทนเนอร์บน Docker Compose:

ในไฟล์ `compose.yml` บริการ `redis`, `postgres`, `label-studio` และ `minio` ได้ติดตั้งตัวขับการทำบันทึก (Logging Driver) แบบ `json-file` และตัวเลือกควบคุมขนาดไฟล์สูงสุดเอาไว้:
```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```
### รายละเอียดการจำกัดขนาด
- คอนเทนเนอร์จะสร้างไฟล์ประวัติในรูปแบบ JSON บน Host Machine
- ไฟล์ประวัติความเคลื่อนไหวจำกัดความจุไว้ไม่เกิน 10 Megabytes (`10m`) ต่อหนึ่งไฟล์
- หากไฟล์ใช้งานเต็มขนาดที่กำหนด ระบบจะสร้างไฟล์ใหม่เก็บวนประวัติไว้ไม่เกิน 3 ไฟล์ (`max-file: "3"`) ช่วยป้องกันระบบดิสก์เต็มกรณีมีข้อมูลร้องขอทำงานปริมาณมาก
- สำหรับบริการ `backend` ไม่ได้มีการระบุ Logging driver ชั่วคราวในระดับ Docker Compose แต่แอปพลิเคชันควบคุมการ Rotate ในตัวด้วย `RotatingFileHandler` ภายใน python โค้ดไว้แล้วที่ขนาด 5MB สูงสุด 5 ไฟล์

---

## 11. เครื่องมือเสริม

โปรเจกต์นี้มีสคริปต์ยูทิลิตี้เสริม `scripts/openapi_to_csv.py` สำหรับแปลงโครงสร้างรายการ Endpoint จากหน้าเอกสารระบบ:

### การทำงาน
- ติดต่อดึงโครงสร้าง OpenAPI JSON Schema จาก FastAPI (พารามิเตอร์เริ่มต้น: `http://localhost:8000/openapi.json`)
- เดินลูปพาร์สหาคีย์ที่เกี่ยวข้องภายใต้โครงสร้าง `paths` เพื่อดึงข้อมูลสำคัญของ Endpoint (Method, Path, Tag, Summary, Description)
- จัดเก็บและเรียงลำดับรายการตาม Tag ของระบบ จากนั้นส่งออกไฟล์เป็น 2 นามสกุล:
  - `api-list.csv`: เก็บในรูปข้อมูลดิบแบบคั่นด้วยจุลภาค
  - `api-list.xlsx`: เก็บในรูปแบบไฟล์ตาราง Excel ที่จัดแต่งความกว้างแถวให้อ่านสะดวก
- สคริปต์นี้จะบันทึกไฟล์ปลายทางไว้ที่โฟลเดอร์ `docs/api-snapshots/` ในเครื่องของผู้ใช้งานโดยอัตโนมัติ

### เครื่องมือภายนอกที่จำเป็น (Libraries)
- `requests`: สำหรับเข้าถึง API ดึง JSON spec
- `openpyxl`: สำหรับจัดการสร้างและแก้ไขสเปรดชีต Excel
- `csv` และ `json`: โมดูลมาตรฐานสำหรับจัดการเขียนสเปรดชีตพื้นฐาน

---

## 12. วิธีรันระบบทั้งหมด

ขั้นตอนและคิวคำสั่งทั้งหมดในการติดตั้งและเริ่มต้นรันระบบภายในเครื่อง:

### ขั้นตอนที่ 1: การเริ่มบริการภายนอกผ่าน Docker Compose
เปิดเทอร์มินัลที่รูทโฟลเดอร์ของโปรเจกต์และรันบริการฐานข้อมูล คิว และคลังไฟล์:
```bash
docker-compose up -d
```
*ระบบจะดาวน์โหลดและเปิดรันคอนเทนเนอร์ PostgreSQL, Redis, MinIO, และ Label Studio ตามเงื่อนไขและคีย์รหัสความปลอดภัยเริ่มต้น*

### ขั้นตอนที่ 2: การตั้งค่า Environment ในโฟลเดอร์ backend
ตรวจสอบให้แน่ใจว่าได้สร้างไฟล์ `backend/.env` เพื่อระบุรายละเอียดพิกัดความปลอดภัยและการเชื่อมต่อฐานข้อมูลตามแบบฟอร์ม:
```ini
APP_NAME=MyBackend
DEBUG=True
DATABASE_URL=postgresql+psycopg2://admin:password123@localhost:5432/ai_backend
REDIS_HOST=localhost
REDIS_PORT=6379
LABEL_STUDIO_URL=http://localhost:8080
LABEL_STUDIO_API_KEY=371dcdb2d27198b823438b40ca567d1e2d48c1da
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password123
MINIO_BUCKET=my-photos
MINIO_SECURE=false
```

### ขั้นตอนที่ 3: เปิดรัน FastAPI Backend API
เข้าไปยังไดเรกทอรี `backend` และใช้ตัวจัดการแพ็คเกจ `uv` ในการดาวน์โหลดความสัมพันธ์และเปิดเซิร์ฟเวอร์พัฒนา:
```bash
cd backend
uv run uvicorn app.main:app --reload
```
*ระบบจะเปิดเซิร์ฟเวอร์บนพอร์ต 8000 และจะประมวลผลสร้างตารางฐานข้อมูลทั้งหมดบน PostgreSQL ให้อัตโนมัติ (ผ่านคำสั่ง `Base.metadata.create_all` ใน `app/main.py`)*

### ขั้นตอนที่ 4: เปิดรันงานคิวประมวลผลเบื้องหลัง (Background Worker)
เปิดเทอร์มินัลอีกหน้าต่าง เข้าไปที่ไดเรกทอรี `backend` แล้วเปิดตัวประมวลผล arq worker:
```bash
cd backend
uv run arq app.worker.tasks.WorkerSettings
```
*ระบบจะเริ่มจับความเคลื่อนไหวง่ายจำลองงานฝึกระบบ AI (Train Job)*

### ขั้นตอนที่ 5: การเข้าตรวจสอบหน้าเอกสาร API
ผู้พัฒนาสามารถเรียกดูข้อมูลและทดลองยิงคีย์ส่งข้อมูลเข้า API ทางหน้าบราวเซอร์ได้ที่:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 13. ปัญหาที่เจอระหว่างทำและวิธีแก้

ปัญหายอดฮิตและแนวทางแก้ไขที่ประมวลผลในโค้ดจริงระหว่างสร้างและขยายแอปพลิเคชัน:

### 1. ปัญหาความเข้ากันไม่ได้ของแพ็คเกจ `bcrypt` และ `passlib` (Python 3.13)
- **ปัญหา**: ไลบรารี `passlib[bcrypt]` เรียกใช้วิธีภายในของแพ็คเกจ `bcrypt` เวอร์ชัน 4.x บางตัวที่ยุติการสนับสนุนไปแล้ว ทำให้เมื่อพยายามทำการแฮชรหัสผ่านจะเกิดข้อผิดพลาดประเภท `TypeError` หรือฟังก์ชันไม่ทำงาน
- **วิธีแก้ไข**: ระบุจำกัดเวอร์ชันของ bcrypt ให้อยู่ภายใต้เวอร์ชัน 4.1 ลงมาใน `pyproject.toml` ของตัวโปรเจกต์ระบุค่าเป้าหมาย `"bcrypt<4.1"` เพื่อรักษาความเข้ากันได้ของการทำงาน

### 2. ปัญหาการชนกันของเส้นทาง API (Route Ordering Collision) ใน Storage Router
- **ปัญหา**: เมื่อเรากำหนดเส้นทางรับชื่อไฟล์แบบ Dynamic Path เช่น `/{object_name}` ไดนามิกพารามิเตอร์ดังกล่าวจะพยายามดักจับ Request ที่ถูกส่งเข้ามายังเส้นทางเฉพาะตัวอื่น เช่น `/upload` หรือ `/objects` ทำให้ระบบตีความเป็นชื่อไฟล์และแสดงผล 404
- **วิธีแก้ไข**: จัดเรียงลำดับของการประกาศตกแต่งเราเตอร์ใน `app/api/v1/routers/storage.py` โดยให้เส้นทางที่มีชื่อระบุชัดเจน (Static Routes เช่น `/upload`, `/objects`, `/buckets`, `/presigned-url`) ถูกประกาศไว้ด้านบนสุด ก่อนเส้นทางที่มีการส่งพารามิเตอร์แบบไดนามิก (`/{object_name}/versions`, `/{object_name}`)

### 3. ปัญหาการแยกการจัดสรรฐานข้อมูลระหว่างระบบแอปพลิเคชันหลักและ Label Studio
- **ปัญหา**: Label Studio ใช้เครื่องยนต์ฐานข้อมูลแบบ Django ซึ่งหากไปสร้างตารางในตารางเดียวกันกับ FastAPI อาจจะนำไปสู่ความขัดแย้งของโครงสร้าง Schema หรือการเขียนข้อมูลทับซ้อนกันจนระบบล่ม
- **วิธีแก้ไข**: สร้างฐานข้อมูลแยกขาดจากกันในเครื่องยนต์ PostgreSQL เดียวกัน โดยกำหนดให้ฐานข้อมูล `ai_database` ดูแลความปลอดภัยเฉพาะงานของ Label Studio และฐานข้อมูล `ai_backend` ดูแลจัดเก็บข้อมูลแอปพลิเคชัน FastAPI ของเรา (สร้างฐานข้อมูลเริ่มต้นด้วยไฟล์สคริปต์ `postgres-init/init-db.sql`)

### 4. ปัญหาการค้นหาตำแหน่งพาร์ธบนระบบปฏิบัติการต่างชนิดกัน (Path Resolution on Windows)
- **ปัญหา**: ตัวระบุพาธหรือการอ่านค่าสิทธิ์ของระบบปฏิบัติการ Windows มักจะมองพารามิเตอร์อย่างตัวคั่นโฟลเดอร์ไม่เหมือนกับบน Linux หรือระบบจำลองบนคอนเทนเนอร์ ส่งผลให้การค้นหาพิกัดไฟล์ตั้งค่า `.env` และการระบุพิกัดเก็บันทึก logs ผิดพลาด
- **วิธีแก้ไข**: ดำเนินการใช้คลาสไลบรารี `pathlib.Path` และฟังก์ชัน `os.path.abspath` ร่วมกับ `os.path.dirname(__file__)` คอยแปลงและค้นหาพาร์ธสัมพัทธ์ (Relative Paths) ตามสภาพแวดล้อมที่รันโค้ดจริงโดยไม่ป้อนข้อความพาร์ธแข็งลงไป (Hardcode)
