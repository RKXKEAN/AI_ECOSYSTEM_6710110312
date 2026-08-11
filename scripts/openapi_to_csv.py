"""
scripts/openapi_to_csv.py

แปลงไฟล์ openapi.json (ที่ FastAPI สร้างให้อัตโนมัติ) เป็น CSV/Excel
เพื่อทำ "Snapshot API List" ของระบบไว้ดูย้อนหลัง หรือแนบในรายงาน

วิธีการทำงาน:
    1. ดึง openapi.json จาก server ที่รันอยู่ (http://localhost:8000/openapi.json)
       หรืออ่านจากไฟล์ที่ดาวน์โหลดไว้แล้วก็ได้
    2. เดินลูปผ่านโครงสร้าง JSON ส่วน "paths" ซึ่งเป็น dict ของทุก endpoint
       แต่ละ endpoint มี key เป็น HTTP method (get, post, put, delete, ...)
    3. ดึงข้อมูลสำคัญของแต่ละ endpoint: path, method, tag, summary, description
    4. เขียนออกเป็นไฟล์ .csv (ใช้ csv module มาตรฐาน) และ .xlsx (ใช้ openpyxl)

Library ที่ใช้:
    - requests   : ดึง openapi.json จาก server ที่รันอยู่
    - csv        : เขียนไฟล์ CSV (Python standard library)
    - openpyxl   : เขียนไฟล์ Excel (.xlsx)

วิธีใช้ (ต้องรันจาก root โปรเจกต์เสมอ เพราะไฟล์ผลลัพธ์จะไปอยู่ที่ <root>/docs/api-snapshots/):
    uv add requests openpyxl
    uv run --project backend scripts/openapi_to_csv.py
    uv run --project backend scripts/openapi_to_csv.py --url http://localhost:8000/openapi.json
    uv run --project backend scripts/openapi_to_csv.py --file ./openapi.json   # ใช้ไฟล์ที่ดาวน์โหลดไว้แล้วแทน
"""

import argparse
import csv
import json
from pathlib import Path

import requests
from openpyxl import Workbook

OUTPUT_DIR = Path.cwd() / "docs" / "api-snapshots"


def load_openapi_spec(url: str | None, file_path: str | None) -> dict:
    """โหลด openapi spec จาก URL (server ที่รันอยู่) หรือจากไฟล์ที่มีอยู่แล้ว"""
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def extract_endpoint_rows(spec: dict) -> list[dict]:
    """
    เดินลูปผ่าน spec["paths"] เพื่อดึงข้อมูลของทุก endpoint ออกมาเป็นแถวข้อมูล (flat list)
    โครงสร้าง openapi.json: paths -> { "/path": { "get": {...}, "post": {...} } }
    """
    rows = []
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, detail in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue  # ข้าม key อื่นที่ไม่ใช่ HTTP method เช่น "parameters"

            tags = detail.get("tags", [])
            rows.append(
                {
                    "Method": method.upper(),
                    "Path": path,
                    "Tag": ", ".join(tags) if tags else "-",
                    "Summary": detail.get("summary", "-"),
                    "Description": detail.get("description", "-"),
                }
            )

    # เรียงตาม Tag แล้วตาม Path ให้ดูง่ายเป็นหมวดหมู่
    rows.sort(key=lambda r: (r["Tag"], r["Path"]))
    return rows


def write_csv(rows: list[dict], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["Method", "Path", "Tag", "Summary", "Description"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[+] บันทึก CSV แล้ว: {output_path}")


def write_excel(rows: list[dict], output_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "API List"

    headers = ["Method", "Path", "Tag", "Summary", "Description"]
    ws.append(headers)

    for row in rows:
        ws.append([row[h] for h in headers])

    # ปรับความกว้างคอลัมน์ให้อ่านง่ายขึ้นเล็กน้อย
    widths = {"A": 10, "B": 35, "C": 18, "D": 30, "E": 50}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    wb.save(output_path)
    print(f"[+] บันทึก Excel แล้ว: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="แปลง openapi.json เป็น CSV/Excel")
    parser.add_argument("--url", default="http://localhost:8000/openapi.json", help="URL ของ openapi.json")
    parser.add_argument("--file", default=None, help="ใช้ไฟล์ openapi.json ที่มีอยู่แล้วแทนการดึงจาก URL")
    args = parser.parse_args()

    spec = load_openapi_spec(url=args.url, file_path=args.file)
    rows = extract_endpoint_rows(spec)

    print(f"[i] พบทั้งหมด {len(rows)} endpoint")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows, OUTPUT_DIR / "api-list.csv")
    write_excel(rows, OUTPUT_DIR / "api-list.xlsx")