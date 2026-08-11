from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.services.training_service.create_pool")
def test_training_flow(mock_create_pool):
    # Mock the arq redis pool and the enqueued job
    mock_redis = AsyncMock()
    mock_job = AsyncMock()
    mock_job.job_id = "mocked-arq-job-id-1234"
    mock_redis.enqueue_job.return_value = mock_job
    mock_create_pool.return_value = mock_redis

    # 1. Create a training job
    request_payload = {
        "dataset_name": "mnist",
        "epochs": 10,
        "model_name": "cnn"
    }
    response = client.post("/api/v1/training/jobs", json=request_payload)
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["job_id"] == "mocked-arq-job-id-1234"
    assert job_data["status"] == "queued"

    job_id = job_data["job_id"]

    # 2. Get status of the enqueued job
    response = client.get(f"/api/v1/training/jobs/{job_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "queued"
    assert status_data["progress"] == 0.0
    assert status_data["dataset_name"] == "mnist"

    # Test the /metrics compatibility endpoint
    response = client.get(f"/api/v1/training/jobs/{job_id}/metrics")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["job_id"] == job_id
    assert status_data["status"] == "queued"

    # 3. Test non-existent job
    response = client.get("/api/v1/training/jobs/non-existent-id")
    assert response.status_code == 404
    assert "job not found" in response.json()["detail"]

    response = client.get("/api/v1/training/jobs/non-existent-id/metrics")
    assert response.status_code == 404

if __name__ == "__main__":
    print("Running Training tests...")
    # Setup mock manually if running as script
    with patch("app.services.training_service.create_pool") as mock_pool:
        mock_redis = AsyncMock()
        mock_job = AsyncMock()
        mock_job.job_id = "mocked-arq-job-id-1234"
        mock_redis.enqueue_job.return_value = mock_job
        mock_pool.return_value = mock_redis
        
        test_training_flow()
    print("All Training tests passed successfully!")
