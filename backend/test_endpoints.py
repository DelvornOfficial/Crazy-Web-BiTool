import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app

def test_full_system():
    with TestClient(app) as client:
        print("--> 1. Testing GET /api/health...")
        res = client.get("/api/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        print("   [OK] Health check response:", res.json())

        print("--> 2. Testing GET /api/v1/releases/latest...")
        res = client.get("/api/v1/releases/latest")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        release_data = res.json()
        print(f"   [OK] Latest release: {release_data.get('version')} ({release_data.get('title')})")

        print("--> 3. Testing POST /api/v1/auth/login with Valid Credentials...")
        login_payload = {
            "username": "admin",
            "password": "NextLevelAdmin@2026!"
        }
        res = client.post("/api/v1/auth/login", json=login_payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        token_data = res.json()
        access_token = token_data.get("access_token")
        assert access_token is not None
        print(f"   [OK] Logged in successfully. Token type: {token_data.get('token_type')}")

        auth_headers = {"Authorization": f"Bearer {access_token}"}

        print("--> 4. Testing GET /api/v1/admin/dashboard-stats (Protected Superadmin Route)...")
        res = client.get("/api/v1/admin/dashboard-stats", headers=auth_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        print("   [OK] Dashboard stats retrieved:", res.json())

        print("--> 5. Testing Anti-SQL Injection Defense with Malicious Payload...")
        sql_injection_payload = {
            "username": "admin' OR '1'='1' --",
            "password": "password"
        }
        res = client.post("/api/v1/auth/login", json=sql_injection_payload)
        # Pydantic v2 regex constraint ^[a-zA-Z0-9_\-\.]{3,32}$ must reject this with 422
        assert res.status_code == 422, f"Expected 422 Unprocessable Entity, got {res.status_code}"
        print("   [OK] Anti-SQL Injection successfully blocked attack payload with 422 Unprocessable Entity!")

        print("--> 6. Testing GET /admin portal static index...")
        res = client.get("/admin", follow_redirects=True)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert "NEXT LEVEL" in res.text
        print("   [OK] Admin Portal HTML successfully served.")

    print("\n=======================================================")
    print("ALL API ENDPOINT & SECURITY TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_full_system()
