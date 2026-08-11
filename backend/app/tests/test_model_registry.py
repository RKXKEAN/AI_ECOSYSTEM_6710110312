from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_model_registry_flow():
    # 1. Register a model
    register_payload = {
        "name": "churn_prediction",
        "created_by": "data_scientist_1",
        "dataset_used": "customer_churn_v2"
    }
    response = client.post("/api/v1/models/register", json=register_payload)
    assert response.status_code == 201
    model_data = response.json()
    assert "id" in model_data
    assert model_data["name"] == "churn_prediction"
    assert model_data["created_by"] == "data_scientist_1"
    assert model_data["dataset_used"] == "customer_churn_v2"
    assert "created_at" in model_data

    model_id = model_data["id"]

    # 2. Get versions of this model
    response = client.get(f"/api/v1/models/{model_id}/versions")
    assert response.status_code == 200
    versions_data = response.json()
    assert versions_data["model_id"] == model_id
    assert len(versions_data["versions"]) >= 1
    
    version = versions_data["versions"][0]
    assert version["version"] == "v1"
    assert version["is_deployed"] is False
    assert "metrics" in version
    
    version_id = version["id"]

    # 3. Update metrics
    new_metrics = {"accuracy": 0.96, "loss": 0.08}
    response = client.put(f"/api/v1/models/{model_id}/metrics?version_id={version_id}", json={"metrics": new_metrics})
    assert response.status_code == 200
    updated_version = response.json()
    assert updated_version["id"] == version_id
    assert updated_version["metrics"] == new_metrics

    # 4. Deploy model
    response = client.post(f"/api/v1/models/{model_id}/deploy?version_id={version_id}")
    assert response.status_code == 200
    deploy_data = response.json()
    assert deploy_data["model_id"] == model_id
    assert deploy_data["version_id"] == version_id
    assert deploy_data["deployed"] is True
    assert "deployed successfully" in deploy_data["message"]

    # 5. Non-existent model tests
    response = client.get("/api/v1/models/99999/versions")
    assert response.status_code == 404

    response = client.put(f"/api/v1/models/99999/metrics?version_id={version_id}", json={"metrics": new_metrics})
    assert response.status_code == 404

    response = client.put(f"/api/v1/models/{model_id}/metrics?version_id=99999", json={"metrics": new_metrics})
    assert response.status_code == 404

    response = client.post(f"/api/v1/models/99999/deploy?version_id={version_id}")
    assert response.status_code == 404

    response = client.post(f"/api/v1/models/{model_id}/deploy?version_id=99999")
    assert response.status_code == 404

if __name__ == "__main__":
    print("Running Model Registry tests...")
    test_model_registry_flow()
    print("All Model Registry tests passed successfully!")
