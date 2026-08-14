# AI ECOSYSTEM SUBJECT
### 6710110312 PATTARAPONG KHAOKHAIKAEW

---

## 🇹🇭 ส่วนภาษาไทย (Thai Version)

### A. ภาพรวมของโปรเจกต์ (Project Overview)
โปรเจกต์นี้เป็น Backend API สำหรับระบบนิเวศปัญญาประดิษฐ์ (AI Ecosystem) พัฒนาขึ้นด้วย FastAPI และภาษา Python 3.13 มีหน้าที่บริหารจัดการวงจรชีวิตของระบบ AI ครอบคลุมการนำเข้าข้อมูลชุดการฝึกสอน การตรวจสอบความเบี่ยงเบน การจัดการโมเดล การฝึกสอนผ่านคิวเบื้องหลัง และการจำลองการให้บริการทำนายผล

### B. สถาปัตยกรรมของระบบ (Layered Architecture)
โปรเจกต์นี้เลือกใช้สถาปัตยกรรมแบบ **Layered Architecture** ในการจัดระเบียบโค้ด เพื่อแบ่งความรับผิดชอบอย่างชัดเจน (Separation of Concerns) ทำให้ระบบสามารถขยายได้ง่าย เพิ่ม Domain ใหม่ได้โดยไม่กระทบต่อฟีเจอร์เดิม และสามารถทดสอบแต่ละเลเยอร์แยกกันได้ง่าย (Testability)
สถาปัตยกรรมประกอบด้วยเลเยอร์ดังนี้:
1. **API Routers (api/v1/routers/)**: มีหน้าที่รับ-ส่ง HTTP Requests/Responses เท่านั้น โดยทำการแปลงข้อมูลและจัดการ HTTP Exception เท่านั้น ไม่ประมวลผลโลจิกทางธุรกิจเอง
2. **Services (services/)**: บรรจุ Logic ทางธุรกิจ (Business Logic) ทั้งหมด เชื่อมต่อกับฐานข้อมูล บริการจัดเก็บไฟล์ หรือระบบภายนอก
3. **Schemas (schemas/)**: รับผิดชอบเรื่องการตรวจสอบความถูกต้องของข้อมูลขาเข้าและจัดรูปแบบข้อมูลขาออกด้วย Pydantic
4. **Models (models/)**: นิยามโครงสร้างตารางข้อมูลเพื่อทำ Object-Relational Mapping (ORM) ผ่าน SQLAlchemy เข้ากับฐานข้อมูล PostgreSQL
5. **Core (core/)**: ระบบโครงสร้างพื้นฐานและการตั้งค่าส่วนกลาง (Infrastructure & Configurations)

### C. แผนผังโครงสร้างโฟลเดอร์แบบย่อ (Folder Structure)
```text
backend/
├── app/
│   ├── api/v1/routers/  # เลเยอร์รับส่ง HTTP Requests
│   ├── core/            # ระบบส่วนกลางและการตั้งค่า (DB, Logging, MinIO, Security)
│   ├── models/          # โครงสร้างตาราง SQLAlchemy ORM
│   ├── schemas/         # โมเดลตรวจสอบข้อมูล Pydantic
│   ├── services/        # โลจิกทางธุรกิจของระบบ
│   ├── worker/          # โค้ดสำหรับงานเบื้องหลัง arq worker
│   ├── tests/           # Unit tests ต่อโดเมน
│   └── main.py          # ไฟล์ทางเข้าหลักของแอปพลิเคชัน FastAPI
├── logs/                # ที่เก็บไฟล์ app.log (JSON format)
├── .env.example         # ตัวอย่างตัวแปรสภาพแวดล้อมที่ต้องตั้งค่า
├── pyproject.toml       # รายการ dependency ที่จัดการด้วย uv
├── uv.lock              # ล็อกเวอร์ชัน dependency แบบละเอียด
└── README.md            # เอกสารประกอบการใช้งานโปรเจกต์
sandbox/                 # สคริปต์สำหรับทดสอบระบบก่อนย้ายเข้า backend จริง
scripts/                 # สคริปต์เครื่องมือแปลงข้อมูล (openapi_to_csv.py)
postgres-init/           # SQL script แยกฐานข้อมูล backend ออกจาก Label Studio
compose.yml              # ไฟล์ Docker Compose สำหรับรันระบบทั้งหมด
```

### D. รายละเอียดแยกตาม Component หลัก
#### 1. Core Layer (`core/`)
ทำหน้าที่จัดสรรเครื่องมือและฟังก์ชันส่วนกลางสำหรับการทำงานของโปรแกรม:
- `config.py`: โหลดตัวแปรสภาพแวดล้อมจากไฟล์ `.env` ด้วย Pydantic Settings
- `database.py`: ตัวขับเคลื่อนการเชื่อมต่อฐานข้อมูล PostgreSQL ผ่าน SQLAlchemy (Engine, SessionLocal, `get_db` dependency)
- `logger.py`: คลาสสร้าง JSON logger บันทึกลงไฟล์ `logs/app.log` บรรทัดละ 1 entry รองรับการทำ Log Rotation เมื่อขนาดครบ 5MB
- `minio_versioning.py`: ตัวเชื่อมต่อและเปิดใช้งาน Bucket Versioning บน MinIO
- `security.py`: จัดการการแฮชและตรวจสอบรหัสผ่านด้วย `bcrypt` และประมวลผล JWT access tokens สำหรับระบบยืนยันตัวตน

#### 2. Models Layer (`models/`)
กำหนดคลาส SQLAlchemy เชื่อมโยงกับตารางจริงใน PostgreSQL:
- `user.py`: ตาราง `users` เก็บข้อมูลผู้ใช้และระดับสิทธิ์ (`role`)
- `dataset.py`: ตาราง `datasets` เก็บข้อมูลการนำเข้าชุดข้อมูล สถานะ (`pending`, `ready`, `processing`) และที่เก็บใน MinIO
- `feedback.py`: ตาราง `feedbacks` บันทึกการประเมินผลการทำนายของผู้ใช้ มีความสัมพันธ์แบบอ้างอิงไอดีผลทำนาย
- `model_registry.py`:
  - `Model`: ตาราง `models` เก็บชื่อโมเดลและรายละเอียดชุดข้อมูลที่ใช้ฝึกสอน มีความสัมพันธ์แบบ One-to-Many ไปยัง `ModelVersion`
  - `ModelVersion`: ตาราง `model_versions` เก็บเวอร์ชันของโมเดล, metrics (JSON), พาธเก็บ weights ใน MinIO และสถานะการ Deploy (`is_deployed`)
- `training_job.py`: ตาราง `training_jobs` เก็บ arq job id, ไฮเปอร์พารามิเตอร์ (JSON) และสถานะการฝึกสอน

#### 3. Schemas Layer (`schemas/`)
รับผิดชอบการตรวจสอบโครงสร้างและชนิดของข้อมูล (Validation):
- `auth.py`: ตรวจสอบ Request/Response ของระบบสมาชิกและการเข้าสู่ระบบ
- `storage.py`: ตรวจสอบข้อมูลการอัปโหลดไฟล์ รายการวัตถุ และการขอ presigned URL
- `annotation.py`: ตรวจสอบการส่งออกข้อมูลโปรเจกต์และทาสก์จาก Label Studio
- `model_registry.py`: ตรวจสอบข้อมูลลงทะเบียนโมเดล อัปเดต metrics และสั่ง Deploy
- `data.py`: จัดการการยืนยันข้อมูลนำเข้าชุดข้อมูล (dataset ingestion)
- `monitoring.py`: ตรวจสอบรูปแบบการส่ง feedback และการแสดงผล logs/drift status
- `training.py`: จัดการข้อมูลการขอส่งงานฝึกสอนและเช็คสถานะการฝึกสอน

#### 4. Services Layer (`services/`)
ดำเนินการแก้ไขและควบคุม Business Logic โดยเชื่อมโยงกับเลเยอร์อื่นและระบบภายนอก:
- `auth_service.py`: บริหารการจัดการผู้ใช้ แฮชรหัสผ่าน และการตรวจสอบการเข้าใช้งานระบบ
- `storage_service.py`: ให้บริการอัปโหลดและดาวน์โหลดไฟล์รวมถึงสร้าง presigned URL ผ่าน MinIO
- `annotation_service.py`: ดึงข้อมูล Project และ Task โดยตรงจาก Label Studio SDK
- `model_registry_service.py`: ดูแลระบบจัดการโมเดล อัปเดต metrics และสั่งจำลองการ Deploy
- `data_service.py`: นำเข้า dataset และระบุชื่อไม่ให้ซ้ำกัน
- `monitoring_service.py`: รับ feedback บันทึกลงฐานข้อมูลและประมวลผลอ่านไฟล์ `app.log` จากท้ายไฟล์มาพาร์สเป็น JSON ป้องกันการทำงานวนซ้ำ
- `training_service.py`: ทำหน้าที่เชื่อมต่อ Redis เพื่อส่งคิวงาน (Enqueue Job) ไปยัง arq worker และดึงข้อมูลการฝึกสอนที่แท้จริงจากฐานข้อมูล
- `inference_service.py`: คืนค่าโมเดลที่ให้บริการทำนายผลแบบจำลอง

#### 5. Routers Layer (`api/v1/routers/`)
เลเยอร์รับ Requests เข้าสู่ระบบและทำหน้าที่ตอบกลับผ่านเส้นทาง API:
| Router | Prefix | Tag | หน้าที่หลัก |
| :--- | :--- | :--- | :--- |
| `auth.py` | `/auth` | `Auth` | จัดการการสมัครสมาชิก, เข้าสู่ระบบ และดึงโปรไฟล์ผู้ใช้ |
| `storage.py` | `/storage` | `Storage` | อัปโหลด/ดาวน์โหลดไฟล์ ตรวจสอบเวอร์ชัน และจัดการ Bucket ผ่าน MinIO |
| `annotation.py` | `/annotation` | `Annotation` | ดึงข้อมูล Project และ Task สำหรับการติดป้ายกำกับจาก Label Studio |
| `models.py` | `/api/v1/models` | `Model Registry` | ลงทะเบียนโมเดล, ดูเวอร์ชัน, อัปเดต metrics และสั่ง Deploy โมเดล |
| `data.py` | `/api/v1/data` | `Data Management` | นำเข้าไฟล์ Dataset เข้าสู่ฐานข้อมูลและแสดงรายการ Dataset |
| `monitoring.py` | `/api/v1/monitoring` | `Monitoring` | บันทึก feedback, ตรวจสอบ Drift, ดูหน้าสถิติ และอ่านไฟล์ log ระบบ |
| `training.py` | `/training` | `Training` | สร้างคิวงานฝึกสอนโมเดล และดึงสถานะความคืบหน้าของงานจริง |
| `inference.py` | `/inference` | `Inference` | ลิสต์โมเดลที่รันอินเฟอเรนซ์ได้ และประมวลผลคำนวณผลลัพธ์โมเดล |
| `health.py` | `/health` | `Health` | ตรวจสอบสถานะการเชื่อมต่อบริการภายนอก (MinIO, etc.) |

#### 6. Worker Layer (`worker/`)
- `tasks.py`: บรรจุคิวงาน `train_model_task` สำหรับจำลองการฝึกโมเดล (10 วินาที) โดยแยก process การทำงานออกจาก FastAPI process หลัก เพื่อป้องกันการบล็อกการทำงาน (Non-blocking execution) และเชื่อมต่อผ่าน Redis โดยใช้ `arq`

#### 7. Scripts Layer (`scripts/`)
- `openapi_to_csv.py`: สคริปต์เสริมสำหรับแปลงไฟล์ `openapi.json` ไปเป็นเอกสาร CSV และ Excel (.xlsx) เพื่อใช้สรุปรายชื่อ Endpoints ของระบบ จัดเก็บไว้ที่โฟลเดอร์ `docs/api-snapshots/` โดยเรียกใช้ไลบรารี `requests` และ `openpyxl`

### E. การติดตั้งโปรเจกต์ (Getting Started)

**สิ่งที่ต้องมีก่อน (Prerequisites):**
- Docker และ Docker Compose
- Python 3.13
- [uv](https://docs.astral.sh/uv/) (Python package manager)

**ขั้นตอน Clone และติดตั้ง:**
```bash
git clone https://github.com/RKXKEAN/AI_ECOSYSTEM_6710110312.git
cd AI_ECOSYSTEM_6710110312/backend
cp .env.example .env
uv sync
```
คำสั่ง `uv sync` จะติดตั้ง dependency ทั้งหมดตามที่ล็อกไว้ใน `uv.lock` ให้อัตโนมัติ พร้อมสร้าง `.venv` ให้เอง (ไม่ต้องใช้ `pip install -r requirements.txt`)

แก้ไขค่าใน `backend/.env` ให้ตรงกับสภาพแวดล้อมจริงของเครื่อง โดยเฉพาะ `LABEL_STUDIO_API_KEY` และรหัสผ่านต่าง ๆ

### F. วิธีการรันโปรเจกต์ทั้งหมด (Running Instructions)
1. **เริ่มรันบริการพื้นฐาน (Docker Containers)**:
   ```bash
   docker-compose up -d
   ```
   *หมายเหตุ: คำสั่งนี้จะเริ่มต้นระบบ Postgres, Redis, MinIO, และ Label Studio ตามค่าพารามิเตอร์ใน `compose.yml`*

2. **เปิดระบบ FastAPI Backend**:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

3. **เริ่มระบบ ARQ Worker (ประมวลผลงานคิวเบื้องหลัง)**:
   ```bash
   cd backend
   uv run arq app.worker.tasks.WorkerSettings
   ```

### G. รายชื่อ API ทั้งหมด และหน้าเอกสาร
สามารถเข้าใช้งานระบบทดสอบและตรวจสอบการทำงานของ API ได้ที่หน้า Swagger UI:
- **Swagger Documentation UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🇬🇧 English Version

### A. Project Overview
This project is the backend API service for an artificial intelligence ecosystem (AI Ecosystem), built with FastAPI and Python 3.13. It supports the lifecycle management of AI models, including dataset ingestion, system logging and feedback monitoring, model version registry, background task queue training, and inference serving.

### B. Layered Architecture
This project implements a **Layered Architecture** to achieve separation of concerns, enhance readability, ease maintenance, and allow independent scalability of domain units without breaking existing codes.
The architecture is partitioned into the following modules:
1. **API Routers (api/v1/routers/)**: Solely handles incoming HTTP requests and structures HTTP responses (HTTP level logic only).
2. **Services (services/)**: Processes and executes all core business logic and communicates with other layers and external interfaces.
3. **Schemas (schemas/)**: Validates incoming request payloads and formats outgoing responses using Pydantic models.
4. **Models (models/)**: Formulates object-relational mapping (ORM) representations of database tables utilizing SQLAlchemy.
5. **Core (core/)**: Centralizes configuration variables, security systems, database drivers, and shared logging setup.

### C. Folder Structure Diagram
```text
backend/
├── app/
│   ├── api/v1/routers/  # HTTP router layer
│   ├── core/            # Infrastructure setup (DB, log formatters, MinIO, security)
│   ├── models/          # SQLAlchemy model layer
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic operations
│   ├── worker/          # Background worker tasks (arq)
│   ├── tests/           # Unit tests per domain
├── logs/                # Storage folder for app.log (structured JSON)
├── main.py              # FastAPI application entrypoint
├── .env.example         # Example of required environment variables
├── pyproject.toml       # Dependency list managed by uv.
├── uv.lock              # Exact dependency version lockfile
sandbox/                 # Sandbox scripts, prototypes before promotion into backend/
scripts/                 # Utility scripts (openapi_to_csv.py)
postgres-init/           # SQL script separating backend DB from Label Studio's
compose.yml              # Docker Compose orchestration file
README.md                # Project main guide
```

### D. Component breakdown
#### 1. Core Layer (`core/`)
Provides foundation tools across the application:
- `config.py`: Parses global environmental variables from `.env` using Pydantic Settings.
- `database.py`: Establishes the database engine connection pool and gets the session instance (`get_db`).
- `logger.py`: Implements a JSON formatting utility printing to `logs/app.log` (rotating file handler capped at 5MB).
- `minio_versioning.py`: Initializes the object storage client and enables bucket-wide object versioning.
- `security.py`: Houses JWT token authorization logic and hashing utilities (using bcrypt).

#### 2. Models Layer (`models/`)
Maps application entities to PostgreSQL tables via SQLAlchemy:
- `user.py`: Configures the `users` table containing user information, hashed passwords, and credentials.
- `dataset.py`: Defines the `datasets` table detailing ingestion status (`pending`, `ready`, `processing`) and storage references.
- `feedback.py`: Stores predictions feedback (`feedbacks` table) indicating correctness and user remarks.
- `model_registry.py`:
  - `Model`: Stores names and training dataset records (maps to `models` table).
  - `ModelVersion`: Stores individual model versions, validation metrics (JSON), file paths, and deployment flags.
- `training_job.py`: Defines the `training_jobs` table detailing ARQ job details and hyperparameters.

#### 3. Schemas Layer (`schemas/`)
Handles validation rules and interface serialization:
- `auth.py`: Validates user registration/login parameters and token structures.
- `storage.py`: Validates file upload details, bucket registrations, and presigned URI requests.
- `annotation.py`: Standardizes output schemas for projects and tasks exported from Label Studio.
- `model_registry.py`: Governs formats for registering models, updating metrics, and deployment responses.
- `data.py`: Validates request schemas for dataset ingestion.
- `monitoring.py`: Validates feedbacks structure, drift indicators, log response details, and metrics.
- `training.py`: Outlines requirements for initiating training tasks and displaying progress metrics.

#### 4. Services Layer (`services/`)
Executes business logic operations and handles external integrations:
- `auth_service.py`: Oversees user validation, credentials authentication, and profile registrations.
- `storage_service.py`: Interacts with MinIO to upload/download binary documents and build presigned links.
- `annotation_service.py`: Calls Label Studio SDK endpoints to list projects and fetch task details.
- `model_registry_service.py`: Performs model indexing, metrics modification, and simulated deployments.
- `data_service.py`: Ingests dataset directories into the database, rejecting duplicate records.
- `monitoring_service.py`: Logs feedbacks and parses the application JSON log file from the end to retrieve recent traces without recursive logging.
- `training_service.py`: Interacts with Redis to submit background tasks to the ARQ worker queue and monitors status changes.
- `inference_service.py`: Delivers predictions mock responses using selected model keys.

#### 5. Routers Layer (`api/v1/routers/`)
Exposes HTTP endpoints and routes them to service operations:
| Router | Prefix | Tag | Primary Function |
| :--- | :--- | :--- | :--- |
| `auth.py` | `/auth` | `Auth` | Manages authentication, token generation, and profile fetching. |
| `storage.py` | `/storage` | `Storage` | Manages MinIO bucket file uploads, downloads, versioning, and listings. |
| `annotation.py` | `/annotation` | `Annotation` | Retreives labeling projects and annotated tasks from Label Studio. |
| `models.py` | `/api/v1/models` | `Model Registry` | Handles model registration, version query, metrics updates, and deployments. |
| `data.py` | `/api/v1/data` | `Data Management` | Registers file paths into datasets table and queries datasets. |
| `monitoring.py` | `/api/v1/monitoring` | `Monitoring` | Records user feedback, monitors drift status, displays dashboard, and returns logs. |
| `training.py` | `/training` | `Training` | Creates and enqueues model training jobs, and fetches actual progress from DB. |
| `inference.py` | `/inference` | `Inference` | Exposes model list and computes mock inference predictions. |
| `health.py` | `/health` | `Health` | Reports connectivity health indicators for database, MinIO, and internal nodes. |

#### 6. Worker Layer (`worker/`)
- `tasks.py`: Contains the `train_model_task` which runs async tasks independently of the FastAPI web server using `arq` and Redis to prevent blocking the HTTP execution thread.

#### 7. Scripts Layer (`scripts/`)
- `openapi_to_csv.py`: Generates flat API endpoints reports and exports them to `.csv` and `.xlsx` worksheets inside `docs/api-snapshots/` utilizing `requests` and `openpyxl` libraries.

### E. Getting Started

**Prerequisites:**
- Docker and Docker Compose
- Python 3.13
- [uv](https://docs.astral.sh/uv/) (Python package manager)

**Clone and Install:**
```bash
git clone https://github.com/RKXKEAN/AI_ECOSYSTEM_6710110312.git
cd AI_ECOSYSTEM_6710110312/backend
cp .env.example .env
uv sync
```
`uv sync` installs every dependency pinned in `uv.lock` and creates the `.venv` automatically (no `pip install -r requirements.txt` needed).

Edit `backend/.env` with values matching your local environment, especially `LABEL_STUDIO_API_KEY` and any passwords.

### F. Running Instructions
1. **Launch Infrastructure Services (Docker Containers)**:
   ```bash
   docker-compose up -d
   ```
   *Note: Starts PostgreSQL, Redis, MinIO, and Label Studio.*

2. **Launch the FastAPI Web Application**:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

3. **Launch the ARQ Worker (Job Queue Consumer)**:
   ```bash
   cd backend
   uv run arq app.worker.tasks.WorkerSettings
   ```

### G. API Domains and Documentation Link
The API endpoints are organized into all domains, checkable via Swagger UI:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)