from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_data_management_flow():
    # 1. Ingest a new dataset
    ingest_payload = {
        "name": "mnist_dataset",
        "storage_path": "datasets/mnist.zip"
    }
    response = client.post("/api/v1/data/ingest", json=ingest_payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "mnist_dataset"
    assert data["storage_path"] == "datasets/mnist.zip"
    assert data["status"] == "pending"
    assert "created_at" in data

    # 2. Ingest duplicate dataset (should fail with 409)
    response_dup = client.post("/api/v1/data/ingest", json=ingest_payload)
    assert response_dup.status_code == 409
    assert "already exists" in response_dup.json()["detail"]

    # 3. List datasets
    response_list = client.get("/api/v1/data/datasets")
    assert response_list.status_code == 200
    datasets_data = response_list.json()
    assert "datasets" in datasets_data
    assert isinstance(datasets_data["datasets"], list)
    
    # Verify our ingested dataset is in the list
    datasets = datasets_data["datasets"]
    assert len(datasets) >= 1
    matching = [d for d in datasets if d["name"] == "mnist_dataset"]
    assert len(matching) == 1
    dataset_info = matching[0]
    assert dataset_info["storage_path"] == "datasets/mnist.zip"
    assert dataset_info["status"] == "pending"
    assert dataset_info["row_count"] is None

if __name__ == "__main__":
    print("Running Data Management tests...")
    test_data_management_flow()
    print("All Data Management tests passed successfully!")
