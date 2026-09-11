# AI ECOSYSTEM SUBJECT
### 6710110312 PATTARAPONG KHAOKHAIKAEW

---

## 🇹🇭 ส่วนภาษาไทย (Thai Version)

### A. ภาพรวมของโปรเจกต์ (Project Overview)

โปรเจกต์นี้เป็น Backend API สำหรับระบบนิเวศปัญญาประดิษฐ์ (AI Ecosystem) พัฒนาขึ้นด้วย FastAPI และภาษา Python 3.13 มีหน้าที่บริหารจัดการวงจรชีวิตของระบบ AI ครบวงจร ตั้งแต่การนำเข้าข้อมูลชุดฝึกสอน การจัดการโมเดล การฝึกสอนโมเดลจริงบน GPU ผ่านระบบคิวเบื้องหลัง การติดตามผลการทดลองด้วย MLflow ไปจนถึงการให้บริการทำนายผล (Inference) แบบ Asynchronous

ระบบประกอบด้วย 6 Container หลัก: **FastAPI Backend**, **Redis** (Message Queue), **PostgreSQL** (ฐานข้อมูล), **MinIO** (Object Storage), **MLflow** (Experiment Tracking & Model Registry) และ **Trainer/Inference Worker** (GPU Container สำหรับเทรนและทำนายผลโมเดลจริง)

### B. สถาปัตยกรรมของระบบ (Layered Architecture)

โปรเจกต์นี้เลือกใช้สถาปัตยกรรมแบบ **Layered Architecture** ในการจัดระเบียบโค้ด เพื่อแบ่งความรับผิดชอบอย่างชัดเจน (Separation of Concerns) ทำให้ระบบขยายได้ง่าย เพิ่ม Domain ใหม่ได้โดยไม่กระทบฟีเจอร์เดิม และทดสอบแต่ละเลเยอร์แยกกันได้ง่าย (Testability)

สถาปัตยกรรมประกอบด้วยเลเยอร์ดังนี้:
1. **API Routers (`api/v1/routers/`)** — รับ-ส่ง HTTP Requests/Responses เท่านั้น ไม่ประมวลผล Business Logic เอง
2. **Services (`services/`)** — บรรจุ Business Logic ทั้งหมด เชื่อมต่อฐานข้อมูล, MinIO, Redis, MLflow
3. **Schemas (`schemas/`)** — ตรวจสอบความถูกต้องของข้อมูลขาเข้า-ออกด้วย Pydantic
4. **Models (`models/`)** — นิยามโครงสร้างตาราง ORM ผ่าน SQLAlchemy เชื่อมกับ PostgreSQL
5. **Core (`core/`)** — โครงสร้างพื้นฐานส่วนกลาง (Config, Database, Logger, Security, MinIO Client)
6. **Trainer/Inference Worker (`trainer/`)** — Container แยกต่างหากที่มี GPU ทำหน้าที่ประมวลผลหนัก (เทรนโมเดล + ทำนายผล) แยกออกจาก FastAPI Process หลัก ไม่ให้ Request ปกติถูกบล็อกระหว่างเทรน

**เหตุผลที่แยก Trainer/Inference Worker เป็น Container ต่างหาก:** งานเทรนโมเดลใช้เวลานาน (หลายนาทีถึงหลายชั่วโมง) และต้องใช้ GPU โดยเฉพาะ ถ้ารันในกระบวนการเดียวกับ FastAPI จะบล็อกการตอบ Request อื่นทั้งหมด การแยก Container พร้อมระบบคิว (Redis + arq) ทำให้ FastAPI รับคำขอได้ตามปกติ ส่งงานเข้าคิว แล้ว Worker ค่อยไปหยิบงานมาทำเบื้องหลังโดยไม่กระทบ API หลัก

### C. โครงสร้างโฟลเดอร์ทั้งหมด (Full Folder Structure)

```text
AI_ECOSYSTEM_6710110312/
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/   # auth, storage, annotation, models, data,
│   │   │                     # monitoring, training, inference, health
│   │   ├── core/             # config, database, logger, security, minio_versioning
│   │   ├── models/           # user, dataset, feedback, model_registry,
│   │   │                     # training_job, inference_job
│   │   ├── schemas/          # Pydantic request/response ต่อโดเมน
│   │   ├── services/         # Business logic ต่อโดเมน
│   │   ├── tests/            # Unit tests ต่อโดเมน
│   │   └── main.py           # FastAPI entrypoint
│   ├── logs/app.log          # Custom JSON logger output
│   ├── .env.example
│   ├── pyproject.toml
│   └── uv.lock
├── trainer/                  # GPU Container: Trainer + Inference Worker
│   ├── worker.py             # arq WorkerSettings (train + inference functions)
│   ├── train.py              # Fine-tune distilbert-base-uncased (NER) + log เข้า MLflow
│   ├── inference.py          # โหลดโมเดลจาก MLflow Registry มาทำนายผล + Pipeline Caching
│   ├── db.py                 # Raw SQL อัปเดตสถานะ training_jobs / inference_jobs
│   ├── dataset_ingestion.py  # ดาวน์โหลด Dataset จาก Hugging Face เข้า MinIO
│   ├── Dockerfile            # CUDA 12.8 + PyTorch (รองรับ RTX 5060 / Blackwell)
│   ├── pyproject.toml
│   └── logs/                 # Log การเทรนแต่ละ Job (mount ออกมาเป็นไฟล์บน Host)
├── mlflow/
│   ├── Dockerfile            # MLflow Server (Backend Store: PostgreSQL, Artifact Store: MinIO)
│   └── .env.example
├── postgres-init/init-db.sql # สร้าง ai_backend และ mlflow_db แยกจาก ai_database (Label Studio)
├── scripts/openapi_to_csv.py # แปลง openapi.json เป็น CSV/Excel
├── docs/api-snapshots/       # ผลลัพธ์ Snapshot API List
├── sandbox/                  # จุดเริ่มต้นทดลอง Library ก่อนย้ายเข้าระบบจริง
├── compose.yml               # Docker Compose: postgres, redis, minio, label-studio,
│                             #   backend, mlflow, trainer-worker (GPU)
└── README.md
```

### D. รายละเอียดแยกตาม Component หลัก

#### 1. Core Layer (`backend/app/core/`)
- `config.py` — โหลดตัวแปรจาก `.env` ด้วย Pydantic Settings
- `database.py` — SQLAlchemy Engine, SessionLocal, `get_db` dependency เชื่อม PostgreSQL (`ai_backend`)
- `logger.py` — Custom JSON Logger บันทึกลง `logs/app.log` พร้อม Log Rotation (5MB)
- `minio_versioning.py` — เชื่อมต่อและเปิดใช้งาน Bucket Versioning บน MinIO
- `security.py` — แฮชรหัสผ่านด้วย `bcrypt` และจัดการ JWT Token

#### 2. Models Layer (`backend/app/models/`)
| ไฟล์ | ตาราง | รายละเอียด |
|---|---|---|
| `user.py` | `users` | ข้อมูลผู้ใช้และสิทธิ์ (`role`) |
| `dataset.py` | `datasets` | ข้อมูล Dataset ที่นำเข้า, สถานะ, ที่เก็บใน MinIO |
| `feedback.py` | `feedbacks` | ผลตอบรับของผู้ใช้ต่อผลการทำนาย |
| `model_registry.py` | `models`, `model_versions` | ทะเบียนโมเดล + เวอร์ชัน (One-to-Many), metrics (JSON), `is_deployed` |
| `training_job.py` | `training_jobs` | สถานะงานเทรน, `dataset_name`, `scheduled_at` (กำหนดเวลาเริ่ม), `mlflow_run_id` |
| `inference_job.py` | `inference_jobs` | สถานะงานทำนายผล, `input_text`, `model_version`, `result` (JSON) |

#### 3. Schemas Layer (`backend/app/schemas/`)
ตรวจสอบข้อมูลขาเข้า-ออกของแต่ละ Router แยกไฟล์ตามชื่อ Domain (`auth.py`, `storage.py`, `annotation.py`, `model_registry.py`, `data.py`, `monitoring.py`, `training.py`, `inference.py`) — โดยเฉพาะ `training.py` และ `inference.py` ที่รองรับการทำงานแบบ Asynchronous ผ่านคิว (`job_id`, `status`, ผลลัพธ์ที่ตรวจสอบภายหลังได้)

#### 4. Services Layer (`backend/app/services/`)
| ไฟล์ | หน้าที่ |
|---|---|
| `auth_service.py` | ลงทะเบียน/ยืนยันตัวตนผู้ใช้ผ่านฐานข้อมูลจริง |
| `storage_service.py` | อัปโหลด/ดาวน์โหลดไฟล์ + Presigned URL ผ่าน MinIO |
| `annotation_service.py` | ดึง Project/Task จาก Label Studio SDK |
| `model_registry_service.py` | จัดการทะเบียนโมเดล, อัปเดต metrics, Deploy |
| `data_service.py` | นำเข้า Dataset, กันชื่อซ้ำ |
| `monitoring_service.py` | บันทึก Feedback และอ่าน Log ระบบ |
| `training_service.py` | Enqueue งานเทรนเข้า arq/Redis พร้อมรองรับ `scheduled_at` (`_defer_until`) และดึงสถานะจริงจากฐานข้อมูล |
| `inference_service.py` | Enqueue งานทำนายผลเข้า arq/Redis และดึงผลลัพธ์จริงจากฐานข้อมูลด้วย `job_id` |

#### 5. Routers Layer (`backend/app/api/v1/routers/`)
| Router | Prefix | Tag | หน้าที่หลัก |
| :--- | :--- | :--- | :--- |
| `auth.py` | `/auth` | `Auth` | สมัครสมาชิก, เข้าสู่ระบบ, ดึงโปรไฟล์ |
| `storage.py` | `/api/v1/storage` | `Storage` | อัปโหลด/ดาวน์โหลด/Version/Presigned URL ผ่าน MinIO |
| `annotation.py` | `/api/v1/annotation` | `Annotation` | ดึง Project/Task จาก Label Studio |
| `models.py` | `/api/v1/models` | `Model Registry` | ลงทะเบียน, ดูเวอร์ชัน, อัปเดต metrics, Deploy |
| `data.py` | `/api/v1/data` | `Data Management` | นำเข้าและแสดงรายการ Dataset |
| `monitoring.py` | `/api/v1/monitoring` | `Monitoring` | Feedback, Drift, Dashboard, Logs |
| `training.py` | `/api/v1/training` | `Training` | **Enqueue งานเทรนโมเดลจริงบน GPU พร้อมกำหนดเวลาเริ่มงานได้ (`scheduled_at`)** และตรวจสอบสถานะ/ผล MLflow Run |
| `inference.py` | `/api/v1/inference` | `Inference` | **Enqueue งานทำนายผล (NER) และตรวจสอบผลลัพธ์ด้วย `job_id`** |
| `health.py` | `/api/v1/health` | `Health` | ตรวจสอบสถานะการเชื่อมต่อบริการภายนอก |

#### 6. Trainer / Inference Worker (`trainer/`)

Container แยกต่างหาก ใช้ GPU (ทดสอบบน NVIDIA GTX 1650 และ RTX 5060) รัน arq Worker ตัวเดียวที่ลงทะเบียน 2 ฟังก์ชันงาน:

- **`train_token_classification_task`** — งานเทรนโมเดล
  1. ดาวน์โหลด Dataset จาก MinIO (`datasets/{dataset_name}/{dataset_name}.zip`) ที่นำเข้าไว้ล่วงหน้าโดย `dataset_ingestion.py` (ดึงจาก Hugging Face `conll2003`)
  2. Fine-tune โมเดล `distilbert-base-uncased` สำหรับงาน Token Classification (NER) ตามแนวทาง Hugging Face LLM Course บทที่ 7.2
  3. บันทึก Hyperparameters, Metrics ระหว่างเทรน (ผ่าน `report_to=["mlflow"]`) และโมเดลที่เทรนเสร็จเข้า **MLflow** (Tracking + Model Registry ชื่อ `ner-conll2003`) พร้อมสำรองไฟล์ไว้ที่ MinIO bucket `models/`
  4. อัปเดตสถานะงาน (`queued → running → complete/failed`) และ `mlflow_run_id` ลงตาราง `training_jobs`

- **`run_inference_task`** — งานทำนายผล (ใช้ Container/GPU เดียวกัน ไม่แยก Container ใหม่)
  1. โหลดโมเดลจาก **MLflow Model Registry** (`models:/ner-conll2003/latest` หรือระบุเวอร์ชันเจาะจง เช่น `models:/ner-conll2003/1`)
  2. Cache โมเดลไว้ใน Memory เพื่อให้คำขอถัดไปตอบเร็วขึ้น (ไม่ต้องโหลดซ้ำ)
  3. ทำนาย NER Tag ของข้อความที่ส่งเข้ามา บันทึกผลลัพธ์ลงตาราง `inference_jobs`

*หมายเหตุ: Inference Worker ใช้ Worker เดียวกับ Trainer Worker (Container เดียวกัน) ตามข้อกำหนดที่ระบบมี GPU Container เพียงตัวเดียว — ถ้ามีงานเทรนกำลังทำงานอยู่ งาน Inference ที่ส่งเข้ามาพร้อมกันจะต้องรอคิวจนกว่า Worker จะว่าง*

#### 7. MLflow (`mlflow/`)

Container แยกต่างหาก รัน MLflow Tracking Server (เวอร์ชัน 3.16.0) ที่ Port `5000`:
- **Backend Store**: PostgreSQL (database `mlflow_db`) — เก็บ Experiment, Run, Parameters, Metrics
- **Artifact Store**: MinIO (bucket `mlflow-artifacts`) — เก็บไฟล์โมเดลจริง (ผ่าน S3-compatible API)
- Experiment หลักที่ใช้: `token-classification-ner`
- Model Registry: `ner-conll2003`

#### 8. Scripts Layer (`scripts/`)
- `openapi_to_csv.py` — แปลง `openapi.json` เป็น CSV/Excel เพื่อ Snapshot รายการ API ทั้งหมด

### E. การติดตั้งโปรเจกต์ (Getting Started)

**สิ่งที่ต้องมีก่อน (Prerequisites):**
- Docker และ Docker Compose (พร้อม NVIDIA Container Toolkit ถ้าต้องการรัน Trainer/Inference Worker บน GPU)
- Python 3.13
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- GPU NVIDIA (แนะนำ, ทดสอบบน GTX 1650 และ RTX 5060) พร้อม Driver ที่รองรับ CUDA 12.8 ขึ้นไป

**ขั้นตอน Clone และติดตั้ง:**
```bash
git clone https://github.com/RKXKEAN/AI_ECOSYSTEM_6710110312.git
cd AI_ECOSYSTEM_6710110312/backend
cp .env.example .env
uv sync
```
คำสั่ง `uv sync` จะติดตั้ง Dependency ทั้งหมดตาม `uv.lock` และสร้าง `.venv` ให้อัตโนมัติ

แก้ไขค่าใน `backend/.env` ให้ตรงกับสภาพแวดล้อมจริง (โดยเฉพาะ `LABEL_STUDIO_API_KEY`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`)

**เช็ค GPU ก่อนใช้งาน Trainer/Inference Worker (ถ้ามี):**
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

### F. วิธีการรันโปรเจกต์ทั้งหมด (Running Instructions)

1. **สร้างฐานข้อมูลที่จำเป็น** (ครั้งแรกเท่านั้น ถ้า Volume ของ PostgreSQL ยังไม่เคยรัน Init Script):
   ```bash
   docker exec -it postgres psql -U admin -d postgres -c "CREATE DATABASE ai_backend;"
   docker exec -it postgres psql -U admin -d postgres -c "CREATE DATABASE mlflow_db;"
   ```

2. **รัน Container ทั้งหมด**:
   ```bash
   docker-compose up -d
   ```
   *เริ่มต้น: postgres, redis, minio, label-studio, backend, mlflow, trainer-worker (GPU)*

3. **ตรวจสอบว่า Container ทุกตัวรันอยู่**:
   ```bash
   docker ps
   ```

4. **(ทางเลือก) รัน Backend แบบ Dev Mode นอก Docker**:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

5. **(ทางเลือก) รัน Trainer/Inference Worker แบบ Dev Mode นอก Docker**:
   ```bash
   cd trainer
   uv run arq worker.WorkerSettings
   ```

6. **เปิดใช้งาน**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - MLflow UI: http://localhost:5000
   - MinIO Console: http://localhost:9001

### G. รายชื่อ API ทั้งหมดและหน้าเอกสาร

ระบบมี API ทั้งหมด 9 กลุ่ม (Auth, Storage, Annotation, Model Registry, Data Management, Monitoring, Training, Inference, Health) รวม 30 กว่า Endpoint ตรวจสอบเอกสารครบถ้วนได้ที่:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**ตัวอย่าง Flow การใช้งาน Training + Inference:**
```
1. POST /api/v1/training/jobs        → ส่งคำสั่งเทรน (dataset_name, hyperparameters, scheduled_at)
2. GET  /api/v1/training/jobs/{id}/metrics → ตรวจสอบสถานะและ mlflow_run_id
3. POST /api/v1/inference/predict    → ส่งข้อความไปทำนายผลด้วยโมเดลที่เทรนเสร็จ
4. GET  /api/v1/inference/jobs/{job_id} → ตรวจสอบผลการทำนาย
```

---

## 🇬🇧 English Version

### A. Project Overview

This project is a backend API for an AI Ecosystem, built with FastAPI and Python 3.13. It manages the full AI lifecycle — dataset ingestion, model registry, real GPU-based model training through a background job queue, experiment tracking with MLflow, and asynchronous model inference serving.

The system is composed of 6 core containers: **FastAPI Backend**, **Redis** (message queue), **PostgreSQL** (database), **MinIO** (object storage), **MLflow** (experiment tracking & model registry), and a **Trainer/Inference Worker** (GPU container handling real training and inference).

### B. Layered Architecture

The project uses a **Layered Architecture** to enforce separation of concerns, ease of extension, and independent testability of each layer:

1. **API Routers (`api/v1/routers/`)** — HTTP request/response handling only, no business logic
2. **Services (`services/`)** — all business logic, integrates with DB, MinIO, Redis, MLflow
3. **Schemas (`schemas/`)** — Pydantic-based request/response validation
4. **Models (`models/`)** — SQLAlchemy ORM mapped to PostgreSQL
5. **Core (`core/`)** — shared infrastructure (config, database, logger, security, MinIO client)
6. **Trainer/Inference Worker (`trainer/`)** — a separate GPU-enabled container handling heavy compute (training + inference), decoupled from the main FastAPI process so normal API requests are never blocked during training.

**Why a separate worker container:** training jobs run for minutes to hours and require a dedicated GPU. Running this in-process with FastAPI would block all other requests. Decoupling via a queue (Redis + arq) lets FastAPI accept requests immediately while the worker consumes jobs in the background.

### C. Full Folder Structure

```text
AI_ECOSYSTEM_6710110312/
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/   # auth, storage, annotation, models, data,
│   │   │                     # monitoring, training, inference, health
│   │   ├── core/             # config, database, logger, security, minio_versioning
│   │   ├── models/           # user, dataset, feedback, model_registry,
│   │   │                     # training_job, inference_job
│   │   ├── schemas/          # Pydantic request/response models per domain
│   │   ├── services/         # business logic per domain
│   │   ├── tests/            # unit tests per domain
│   │   └── main.py           # FastAPI entrypoint
│   ├── logs/app.log          # custom JSON logger output
│   ├── .env.example
│   ├── pyproject.toml
│   └── uv.lock
├── trainer/                  # GPU container: Trainer + Inference Worker
│   ├── worker.py             # arq WorkerSettings (train + inference functions)
│   ├── train.py              # fine-tune distilbert-base-uncased (NER) + log to MLflow
│   ├── inference.py          # load model from MLflow Registry, run predictions, cache pipeline
│   ├── db.py                 # raw SQL updates for training_jobs / inference_jobs
│   ├── dataset_ingestion.py  # download HF dataset into MinIO
│   ├── Dockerfile            # CUDA 12.8 + PyTorch (supports RTX 5060 / Blackwell)
│   ├── pyproject.toml
│   └── logs/                 # per-job training logs (mounted to host)
├── mlflow/
│   ├── Dockerfile            # MLflow Server (backend store: PostgreSQL, artifact store: MinIO)
│   └── .env.example
├── postgres-init/init-db.sql # creates ai_backend and mlflow_db separate from ai_database
├── scripts/openapi_to_csv.py # converts openapi.json into CSV/Excel
├── docs/api-snapshots/       # generated API list snapshots
├── sandbox/                  # early prototypes before promotion into the real codebase
├── compose.yml               # postgres, redis, minio, label-studio, backend, mlflow, trainer-worker (GPU)
└── README.md
```

### D. Component Breakdown

#### 1. Core Layer (`backend/app/core/`)
- `config.py` — loads `.env` via Pydantic Settings
- `database.py` — SQLAlchemy engine, session, `get_db` dependency (PostgreSQL `ai_backend`)
- `logger.py` — custom JSON logger with rotation (5MB)
- `minio_versioning.py` — MinIO client setup and bucket versioning
- `security.py` — password hashing (bcrypt) and JWT handling

#### 2. Models Layer (`backend/app/models/`)
| File | Table | Notes |
|---|---|---|
| `user.py` | `users` | user credentials and role |
| `dataset.py` | `datasets` | ingested dataset metadata and status |
| `feedback.py` | `feedbacks` | user feedback on predictions |
| `model_registry.py` | `models`, `model_versions` | model registry, one-to-many versions, metrics JSON, deployment flag |
| `training_job.py` | `training_jobs` | training status, `dataset_name`, `scheduled_at`, `mlflow_run_id` |
| `inference_job.py` | `inference_jobs` | inference status, `input_text`, `model_version`, `result` JSON |

#### 3. Schemas Layer (`backend/app/schemas/`)
Per-domain Pydantic models (`auth.py`, `storage.py`, `annotation.py`, `model_registry.py`, `data.py`, `monitoring.py`, `training.py`, `inference.py`) — `training.py` and `inference.py` specifically support the async job pattern (`job_id`, `status`, later-checked results).

#### 4. Services Layer (`backend/app/services/`)
| File | Responsibility |
|---|---|
| `auth_service.py` | user registration/authentication against the database |
| `storage_service.py` | upload/download + presigned URLs via MinIO |
| `annotation_service.py` | fetch projects/tasks from Label Studio SDK |
| `model_registry_service.py` | model registration, metrics updates, deployment |
| `data_service.py` | dataset ingestion, duplicate-name guard |
| `monitoring_service.py` | feedback logging and reading system logs |
| `training_service.py` | enqueue training jobs to arq/Redis, supports `scheduled_at` via `_defer_until`, reads real status from DB |
| `inference_service.py` | enqueue inference jobs to arq/Redis, reads real results from DB by `job_id` |

#### 5. Routers Layer (`backend/app/api/v1/routers/`)
| Router | Prefix | Tag | Primary Function |
| :--- | :--- | :--- | :--- |
| `auth.py` | `/auth` | `Auth` | register, login, profile |
| `storage.py` | `/api/v1/storage` | `Storage` | upload/download/versions/presigned URLs via MinIO |
| `annotation.py` | `/api/v1/annotation` | `Annotation` | Label Studio projects/tasks |
| `models.py` | `/api/v1/models` | `Model Registry` | register, versions, metrics, deploy |
| `data.py` | `/api/v1/data` | `Data Management` | ingest and list datasets |
| `monitoring.py` | `/api/v1/monitoring` | `Monitoring` | feedback, drift, dashboard, logs |
| `training.py` | `/api/v1/training` | `Training` | **enqueue real GPU training with optional scheduled start (`scheduled_at`)**, check status/MLflow run |
| `inference.py` | `/api/v1/inference` | `Inference` | **enqueue NER prediction and check result by `job_id`** |
| `health.py` | `/api/v1/health` | `Health` | external service connectivity checks |

#### 6. Trainer / Inference Worker (`trainer/`)

A dedicated GPU container (tested on NVIDIA GTX 1650 and RTX 5060) running a single arq worker registering two job functions:

- **`train_token_classification_task`**
  1. Downloads the dataset zip from MinIO (`datasets/{dataset_name}/{dataset_name}.zip`), pre-ingested from Hugging Face (`conll2003`) via `dataset_ingestion.py`
  2. Fine-tunes `distilbert-base-uncased` for Token Classification (NER), following Hugging Face LLM Course Chapter 7.2
  3. Logs hyperparameters and metrics to **MLflow** during training (`report_to=["mlflow"]`), and logs/registers the trained model to the MLflow Model Registry (`ner-conll2003`), while also archiving a copy in MinIO (`models/` bucket)
  4. Updates job status (`queued → running → complete/failed`) and `mlflow_run_id` in `training_jobs`

- **`run_inference_task`** (same container/GPU, no separate container)
  1. Loads the model from the **MLflow Model Registry** (`models:/ner-conll2003/latest` or a specific version)
  2. Caches the loaded pipeline in memory for faster subsequent requests
  3. Predicts NER tags for the input text and stores the result in `inference_jobs`

*Note: inference shares the same worker/container as training since the system uses a single GPU container — concurrent training jobs will delay queued inference requests until the worker is free.*

#### 7. MLflow (`mlflow/`)

A dedicated container running the MLflow Tracking Server (v3.16.0) on port `5000`:
- **Backend Store**: PostgreSQL (`mlflow_db`) — experiments, runs, parameters, metrics
- **Artifact Store**: MinIO (`mlflow-artifacts` bucket) — actual model files via S3-compatible API
- Main experiment: `token-classification-ner`
- Registered model: `ner-conll2003`

#### 8. Scripts Layer (`scripts/`)
- `openapi_to_csv.py` — converts `openapi.json` into CSV/Excel for an API list snapshot

### E. Getting Started

**Prerequisites:**
- Docker and Docker Compose (with NVIDIA Container Toolkit for GPU-based worker)
- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- NVIDIA GPU (tested on GTX 1650 and RTX 5060) with a driver supporting CUDA 12.8+

**Clone and Install:**
```bash
git clone https://github.com/RKXKEAN/AI_ECOSYSTEM_6710110312.git
cd AI_ECOSYSTEM_6710110312/backend
cp .env.example .env
uv sync
```

Edit `backend/.env` to match your environment (especially `LABEL_STUDIO_API_KEY`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`).

**Check GPU availability (if using the Trainer/Inference Worker):**
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

### F. Running Instructions

1. **Create required databases** (first run only, if the PostgreSQL volume hasn't run the init script yet):
   ```bash
   docker exec -it postgres psql -U admin -d postgres -c "CREATE DATABASE ai_backend;"
   docker exec -it postgres psql -U admin -d postgres -c "CREATE DATABASE mlflow_db;"
   ```

2. **Start all containers**:
   ```bash
   docker-compose up -d
   ```
   *Starts: postgres, redis, minio, label-studio, backend, mlflow, trainer-worker (GPU)*

3. **Verify all containers are running**:
   ```bash
   docker ps
   ```

4. **(Optional) Run backend in dev mode outside Docker**:
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

5. **(Optional) Run the Trainer/Inference Worker outside Docker**:
   ```bash
   cd trainer
   uv run arq worker.WorkerSettings
   ```

6. **Access the services**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - MLflow UI: http://localhost:5000
   - MinIO Console: http://localhost:9001

### G. API Domains and Documentation Link

The system exposes 9 API groups (Auth, Storage, Annotation, Model Registry, Data Management, Monitoring, Training, Inference, Health) with 30+ endpoints total, fully documented at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**Example Training + Inference flow:**
```
1. POST /api/v1/training/jobs        → submit training job (dataset_name, hyperparameters, scheduled_at)
2. GET  /api/v1/training/jobs/{id}/metrics → check status and mlflow_run_id
3. POST /api/v1/inference/predict    → send text to the trained model
4. GET  /api/v1/inference/jobs/{job_id} → check the prediction result
```