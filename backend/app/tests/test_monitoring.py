from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_monitoring_flow():
    # 1. Submit feedback
    feedback_payload = {
        "prediction_id": "pred-12345",
        "is_correct": True,
        "comment": "Accurate prediction"
    }
    response = client.post("/api/v1/monitoring/feedback", json=feedback_payload)
    assert response.status_code == 201
    fb_data = response.json()
    assert "id" in fb_data
    assert fb_data["prediction_id"] == "pred-12345"
    assert fb_data["is_correct"] is True
    assert fb_data["comment"] == "Accurate prediction"
    assert "created_at" in fb_data

    # 2. Get drift status
    response = client.get("/api/v1/monitoring/drift")
    assert response.status_code == 200
    drift_data = response.json()
    assert "status" in drift_data
    assert "drift_score" in drift_data
    assert "message" in drift_data

    # 3. Get dashboard metrics
    response = client.get("/api/v1/monitoring/dashboard")
    assert response.status_code == 200
    db_data = response.json()
    assert "uptime_seconds" in db_data
    assert db_data["total_predictions"] >= 1  # Should count the feedback we just submitted
    assert "active_alerts" in db_data

    # 4. Get system logs
    response = client.get("/api/v1/monitoring/logs?limit=5")
    assert response.status_code == 200
    logs_data = response.json()
    assert "logs" in logs_data
    assert "count" in logs_data
    assert isinstance(logs_data["logs"], list)

if __name__ == "__main__":
    print("Running Monitoring tests...")
    test_monitoring_flow()
    print("All Monitoring tests passed successfully!")
