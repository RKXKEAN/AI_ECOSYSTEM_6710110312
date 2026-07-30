from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_ready():
    response = client.get("/api/v1/health/ready")
    # Even if MinIO is not running, it must catch the error and return 503 instead of 500
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        assert response.json() == {"status": "ok", "minio": "connected"}
    else:
        assert response.json() == {"status": "degraded", "minio": "unreachable"}

def test_inference():
    response = client.get("/api/v1/inference/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert any(m["name"] == "default" for m in models)
    
    response = client.post("/api/v1/inference/predict", json={"input_text": "hello", "model_name": "default"})
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "default"
    assert "prediction" in data
    assert 0.7 <= data["confidence"] <= 0.99
    
    response = client.post("/api/v1/inference/predict", json={"input_text": "hello", "model_name": "unknown-model"})
    assert response.status_code == 404
    assert response.json()["detail"] == "model not found"

def test_training():
    response = client.post("/api/v1/training/jobs", json={"dataset_name": "mnist", "epochs": 5})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    
    job_id = data["job_id"]
    
    response = client.get(f"/api/v1/training/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "running"
    assert data["progress"] > 0.0
    
    # Poll until completed
    for _ in range(10):
        response = client.get(f"/api/v1/training/jobs/{job_id}")
        data = response.json()
        if data["status"] == "completed":
            assert data["progress"] == 1.0
            break
            
    response = client.get("/api/v1/training/jobs/non-existent-id")
    assert response.status_code == 404

if __name__ == "__main__":
    print("Running tests...")
    test_health()
    print("[OK] test_health passed")
    test_health_ready()
    print("[OK] test_health_ready passed")
    test_inference()
    print("[OK] test_inference passed")
    test_training()
    print("[OK] test_training passed")
    print("All tests passed successfully!")
