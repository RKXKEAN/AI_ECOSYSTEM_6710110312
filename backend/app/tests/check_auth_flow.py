import os
import sys

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.auth_service import authenticate_user, get_user_by_username
from app.core.security import create_access_token, verify_token

def run_unit_tests():
    print("=== Running Auth Unit Tests ===")
    
    # 1. Test authenticating users
    print("[1] Testing authenticate_user...")
    admin_user = authenticate_user("admin", "adminpassword123")
    assert admin_user is not None, "Failed to authenticate admin user"
    assert admin_user["username"] == "admin", "Admin username mismatch"
    assert admin_user["role"] == "admin", "Admin role mismatch"
    assert "password" not in admin_user, "Password should not be returned in authenticated user dict"
    
    demo_user = authenticate_user("demo_user", "userpassword456")
    assert demo_user is not None, "Failed to authenticate demo user"
    assert demo_user["username"] == "demo_user", "Demo user username mismatch"
    assert demo_user["role"] == "user", "Demo user role mismatch"
    
    # Test invalid credentials
    invalid_user = authenticate_user("admin", "wrong_password")
    assert invalid_user is None, "Should fail authentication with wrong password"
    
    invalid_username = authenticate_user("unknown_user", "some_password")
    assert invalid_username is None, "Should fail authentication for non-existing user"
    print("[OK] authenticate_user tests passed!")

    # 2. Test get_user_by_username
    print("[2] Testing get_user_by_username...")
    admin_lookup = get_user_by_username("admin")
    assert admin_lookup is not None
    assert admin_lookup["username"] == "admin"
    assert "password" not in admin_lookup
    print("[OK] get_user_by_username tests passed!")

    # 3. Test token creation and verification
    print("[3] Testing create_access_token and verify_token...")
    token_payload = {"sub": "admin"}
    token = create_access_token(token_payload)
    assert isinstance(token, str), "Token must be a string"
    assert len(token) > 0, "Token should not be empty"
    
    decoded = verify_token(token)
    assert decoded is not None, "Failed to verify valid token"
    assert decoded.get("sub") == "admin", "Subject in token mismatch"
    assert "exp" in decoded, "Token should contain expiration claim"
    
    # Test invalid token
    invalid_decoded = verify_token(token + "invalid_suffix")
    assert invalid_decoded is None, "Should fail to verify mutated token"
    print("[OK] token verification tests passed!")
    
    # 4. Optional: Run FastAPI TestClient integration test if httpx is available
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        print("[4] Testing FastAPI Endpoints using TestClient...")
        client = TestClient(app)
        
        # Test login post
        login_res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword123"})
        assert login_res.status_code == 200, f"Expected 200, got {login_res.status_code}"
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Test get me with token
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_data['access_token']}"})
        assert me_res.status_code == 200, f"Expected 200, got {me_res.status_code}"
        me_data = me_res.json()
        assert me_data["username"] == "admin"
        assert me_data["role"] == "admin"
        
        # Test login failed
        bad_login_res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
        assert bad_login_res.status_code == 401
        
        # Test get me invalid token
        bad_me_res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer badtoken"})
        assert bad_me_res.status_code == 401
        
        print("[OK] API endpoint tests passed!")
    except ImportError:
        print("[i] httpx not installed, skipping TestClient integration tests.")
    except Exception as e:
        print(f"[FAIL] Integration test failed: {e}")
        sys.exit(1)

    print("\n[SUCCESS] All checks passed successfully!")

if __name__ == "__main__":
    run_unit_tests()
