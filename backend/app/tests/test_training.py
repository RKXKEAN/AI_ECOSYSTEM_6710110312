import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.services.training_service.create_pool")
def test_training_flow(mock_create_pool):
    # Mock the arq redis pool and the enqueued job
    mock_redis = AsyncMock()
    mock_job = AsyncMock()
    
    # Use random UUID for job_id to prevent UniqueViolation database errors
    job_uuid_immediate = f"mocked-arq-job-id-{uuid.uuid4()}"
    mock_job.job_id = job_uuid_immediate
    mock_redis.enqueue_job.return_value = mock_job
    mock_create_pool.return_value = mock_redis

    # 1. Create a training job (Immediate - no scheduled_at)
    request_payload = {
        "dataset_name": "mnist",
        "epochs": 10,
        "model_name": "cnn"
    }
    response = client.post("/api/v1/training/jobs", json=request_payload)
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["job_id"] == job_uuid_immediate
    assert job_data["status"] == "queued"
    assert job_data["scheduled_at"] is None

    # Verify arq call for immediate job
    mock_redis.enqueue_job.assert_called_once()
    args, kwargs = mock_redis.enqueue_job.call_args
    assert args[0] == "train_token_classification_task"
    assert "_defer_until" not in kwargs

    # 2. Get status of the enqueued job
    response = client.get(f"/api/v1/training/jobs/{job_uuid_immediate}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["job_id"] == job_uuid_immediate
    assert status_data["status"] == "queued"
    assert status_data["progress"] == 0.0
    assert status_data["dataset_name"] == "mnist"

    # Test the /metrics compatibility endpoint
    response = client.get(f"/api/v1/training/jobs/{job_uuid_immediate}/metrics")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["job_id"] == job_uuid_immediate
    assert status_data["status"] == "queued"

    # 3. Create a training job (Scheduled - with scheduled_at)
    mock_redis.enqueue_job.reset_mock()
    job_uuid_scheduled = f"mocked-arq-job-id-{uuid.uuid4()}"
    mock_job_scheduled = AsyncMock()
    mock_job_scheduled.job_id = job_uuid_scheduled
    mock_redis.enqueue_job.return_value = mock_job_scheduled

    scheduled_time = datetime(2026, 8, 31, 18, 0, 0)
    request_payload_scheduled = {
        "dataset_name": "mnist",
        "epochs": 10,
        "model_name": "cnn",
        "scheduled_at": scheduled_time.isoformat()
    }
    response = client.post("/api/v1/training/jobs", json=request_payload_scheduled)
    assert response.status_code == 200
    job_data_scheduled = response.json()
    assert job_data_scheduled["job_id"] == job_uuid_scheduled
    assert job_data_scheduled["status"] == "queued"
    assert job_data_scheduled["scheduled_at"] is not None

    # Verify arq call for scheduled job
    mock_redis.enqueue_job.assert_called_once()
    args_sched, kwargs_sched = mock_redis.enqueue_job.call_args
    assert args_sched[0] == "train_token_classification_task"
    assert "_defer_until" in kwargs_sched
    assert kwargs_sched["_defer_until"] == scheduled_time

    # 4. Test non-existent job
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
        mock_job.job_id = f"mocked-arq-job-id-{uuid.uuid4()}"
        mock_redis.enqueue_job.return_value = mock_job
        mock_pool.return_value = mock_redis
        
        test_training_flow()
    print("All Training tests passed successfully!")
