import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.config import ADMIN_EMAIL, ADMIN_PASSWORD

def run_tests():
    with TestClient(app) as client:
        print("================ CORS VERIFICATION SUITE ================")
        prod_origin = "https://traffic-sense-frontend.onrender.com"
    
    # 1. Test OPTIONS /api/auth/login
    print("\n1. Testing OPTIONS /api/auth/login preflight:")
    resp = client.options(
        "/api/auth/login",
        headers={
            "Origin": prod_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type"
        }
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
    print(f"Allow-Methods: {resp.headers.get('access-control-allow-methods')}")
    print(f"Allow-Headers: {resp.headers.get('access-control-allow-headers')}")
    print(f"Allow-Credentials: {resp.headers.get('access-control-allow-credentials')}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in resp.headers.get("access-control-allow-methods", "")
    print("PASS: Preflight for /api/auth/login succeeded!")

    # 2. Test OPTIONS /api/auth/me
    print("\n2. Testing OPTIONS /api/auth/me preflight:")
    resp = client.options(
        "/api/auth/me",
        headers={
            "Origin": prod_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization"
        }
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
    print(f"Allow-Credentials: {resp.headers.get('access-control-allow-credentials')}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    print("PASS: Preflight for /api/auth/me succeeded!")

    # 3. Test POST /api/auth/login reaches auth handler
    print("\n3. Testing POST /api/auth/login with invalid password:")
    resp = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrong_password_123"},
        headers={"Origin": prod_origin}
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
    print(f"Response Body: {resp.json()}")
    assert resp.status_code == 401, f"Expected 401 from auth handler, got {resp.status_code}"
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    assert resp.headers.get("access-control-allow-credentials") == "true"
    print("PASS: Reached auth handler and returned 401 with proper CORS headers!")

    # 4. Test POST /api/auth/login with valid password
    print("\n4. Testing POST /api/auth/login with valid admin credentials:")
    resp = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Origin": prod_origin}
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    token = resp.json().get("access_token")
    assert token is not None, "Expected access_token"
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    print("PASS: Login successful and returned token with CORS headers!")

    # 5. Test GET /api/auth/me with Bearer token
    print("\n5. Testing GET /api/auth/me with Bearer token:")
    resp = client.get(
        "/api/auth/me",
        headers={
            "Origin": prod_origin,
            "Authorization": f"Bearer {token}"
        }
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Allow-Origin: {resp.headers.get('access-control-allow-origin')}")
    print(f"User Email: {resp.json().get('email')}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.json().get("email") == ADMIN_EMAIL
    assert resp.headers.get("access-control-allow-origin") == prod_origin
    print("PASS: Session restored via /api/auth/me with CORS headers!")

    # 6. Test other API preflights (OPTIONS /api/violations, OPTIONS /api/dashboard/stats)
    print("\n6. Testing OPTIONS on other endpoints (/api/violations, /api/dashboard/stats):")
    for endpoint, method in [("/api/violations", "GET"), ("/api/dashboard/stats", "GET"), ("/api/videos/analyze", "POST")]:
        resp = client.options(
            endpoint,
            headers={
                "Origin": prod_origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization,content-type"
            }
        )
        assert resp.status_code == 200, f"Preflight failed on {endpoint} with {resp.status_code}"
        assert resp.headers.get("access-control-allow-origin") == prod_origin
        print(f"PASS: Preflight for {endpoint} ({method}) succeeded (status 200)")

    # 7. Test Localhost and other allowed origins
    print("\n7. Testing Localhost and regex origins:")
    for o in ["http://localhost:5173", "http://127.0.0.1:5173", "https://preview-deploy.onrender.com", "https://traffic-sense.vercel.app"]:
        resp = client.options(
            "/api/auth/login",
            headers={
                "Origin": o,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        assert resp.status_code == 200, f"Failed for origin {o}: {resp.status_code}"
        assert resp.headers.get("access-control-allow-origin") == o
        print(f"PASS: Origin {o} successfully accepted!")

    # 8. Test Malicious/Disallowed Origin
    print("\n8. Testing Disallowed Origin:")
    resp = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://malicious-attacker.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    assert resp.status_code == 400, f"Expected 400 for malicious origin, got {resp.status_code}"
    print(f"PASS: Malicious origin correctly rejected with status 400 ({resp.text})")

    print("\n================ ALL CORS TESTS PASSED ================")

if __name__ == "__main__":
    run_tests()
