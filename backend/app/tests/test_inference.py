import uuid
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.services.inference_service.create_pool")
def test_inference_flow(mock_create_pool):
    # Mock ARQ Redis pool and enqueued job
    mock_redis = AsyncMock()
    mock_job = AsyncMock()

    job_uuid_1 = f"mocked-inf-job-{uuid.uuid4()}"
    mock_job.job_id = job_uuid_1
    mock_redis.enqueue_job.return_value = mock_job
    mock_create_pool.return_value = mock_redis

    # 1. Enqueue inference job with default model_version (None)
    payload_default = {
        "text": "John works at Google in California"
    }
    response = client.post("/api/v1/inference/predict", json=payload_default)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["job_id"] == job_uuid_1
    assert data["status"] == "queued"

    mock_redis.enqueue_job.assert_called_once()
    args, kwargs = mock_redis.enqueue_job.call_args
    assert args[0] == "run_inference_task"
    assert args[2] == "John works at Google in California"
    assert args[3] is None

    # 2. Get status of the enqueued job
    response = client.get(f"/api/v1/inference/jobs/{job_uuid_1}")
    assert response.status_code == 200, response.text
    job_data = response.json()
    assert job_data["job_id"] == job_uuid_1
    assert job_data["status"] == "queued"
    assert job_data["input_text"] == "John works at Google in California"
    assert job_data["model_version"] is None
    assert job_data["result"] is None

    # 3. Enqueue inference job with specific model_version
    mock_redis.enqueue_job.reset_mock()
    job_uuid_2 = f"mocked-inf-job-{uuid.uuid4()}"
    mock_job_2 = AsyncMock()
    mock_job_2.job_id = job_uuid_2
    mock_redis.enqueue_job.return_value = mock_job_2

    payload_versioned = {
        "text": "Apple is located in Cupertino",
        "model_version": "1"
    }
    response = client.post("/api/v1/inference/predict", json=payload_versioned)
    assert response.status_code == 200, response.text
    data_2 = response.json()
    assert data_2["job_id"] == job_uuid_2
    assert data_2["status"] == "queued"

    mock_redis.enqueue_job.assert_called_once()
    args_2, kwargs_2 = mock_redis.enqueue_job.call_args
    assert args_2[0] == "run_inference_task"
    assert args_2[2] == "Apple is located in Cupertino"
    assert args_2[3] == "1"

    # 4. Check status of versioned job
    response = client.get(f"/api/v1/inference/jobs/{job_uuid_2}")
    assert response.status_code == 200, response.text
    job_data_2 = response.json()
    assert job_data_2["job_id"] == job_uuid_2
    assert job_data_2["model_version"] == "1"

    # 5. Non-existent job returns 404
    response = client.get("/api/v1/inference/jobs/non-existent-inference-job-id")
    assert response.status_code == 404
    assert "job not found" in response.json()["detail"]

    # 6. Check list models endpoint
    response = client.get("/api/v1/inference/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) > 0


if __name__ == "__main__":
    print("Running Inference tests...")
    with patch("app.services.inference_service.create_pool") as mock_pool:
        mock_redis = AsyncMock()
        mock_job = AsyncMock()
        mock_job.job_id = f"mocked-inf-job-{uuid.uuid4()}"
        mock_redis.enqueue_job.return_value = mock_job
        mock_pool.return_value = mock_redis

        test_inference_flow()
    print("All Inference tests passed successfully!")
