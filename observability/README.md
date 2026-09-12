# Observability Stack Documentation

เอกสารสรุปการตั้งค่าระบบ Observability (Metrics, Logs, Traces) สำหรับระบบ AI Ecosystem

## 1. บริการและ Endpoint สำหรับเข้าถึง UI

| บริการ (Service) | พอร์ต (Port) | URL / วิธีการเข้าใช้งาน | ข้อมูลการล็อกอินเริ่มต้น (Credentials) | รายละเอียด |
| :--- | :--- | :--- | :--- | :--- |
| **Grafana** | `3000` | [http://localhost:3000](http://localhost:3000) | Username: `admin`<br>Password: `admin` | ศูนย์กลางการรวม Dashboards, Logs, Metrics และ Distributed Traces |
| **Prometheus** | 9090 | [http://localhost:9090](http://localhost:9090) | ไม่ต้องใช้รหัสผ่าน | ตรวจสอบสถานะ Targets และทดสอบ PromQL Metrics |
| **FastAPI Metrics** | 8000 | [http://localhost:8000/metrics](http://localhost:8000/metrics) | ไม่ต้องใช้รหัสผ่าน | Endpoint สำหรับให้ Prometheus มาดึง Metrics |
| **Tempo** | 3200 | เข้าผ่าน **Grafana Explore** เท่านั้น | เข้าใช้งานผ่าน Grafana | เก็บ Distributed Tracing (รับ OTLP gRPC :4317 และ HTTP :4318) |
| **Loki** | 3100 | เข้าผ่าน **Grafana Explore** เท่านั้น | เข้าใช้งานผ่าน Grafana | เก็บ Logs แบบรวมศูนย์ (Log Aggregation) |

> [!NOTE]
> Tempo และ Loki เป็น Storage Backends ที่ไม่มี Web UI เต็มรูปแบบในตัว การค้นหาและดูข้อมูล Traces และ Logs จะทำผ่านเมนู **Explore** บน Grafana โดยเลือก Data Source เป็น Tempo หรือ Loki

---

## 2. ข้อมูล Data Sources ที่ได้รับการ Provision อัตโนมัติ

ไฟล์การตั้งค่า Provisioning อยู่ที่ observability/grafana-provisioning/datasources/datasources.yaml ซึ่ง Grafana จะโหลดขึ้นมาทันทีเมื่อ Container เริ่มทำงาน:

1. **Prometheus (http://prometheus:9090)**
   - ชนิด: prometheus
   - รวบรวม System Metrics และ Application Metrics จาก FastAPI Backend (/metrics)

2. **Loki (http://loki:3100)**
   - ชนิด: loki
   - รวบรวมบันทึกเหตุการณ์ (Logs) จากแอปพลิเคชันและ Container ในระบบ

3. **Tempo (`http://tempo:3200`)**
   - ชนิด: `tempo` (Default Data Source)
   - รวบรวม Distributed Traces ผ่าน OpenTelemetry OTLP Exporter จาก FastAPI Backend และ Trainer/Inference Worker
   - รองรับการเชื่อมโยง Trace-to-Logs และ Trace-to-Metrics กับ Loki และ Prometheus
