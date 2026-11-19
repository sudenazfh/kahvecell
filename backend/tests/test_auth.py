"""End-to-end auth flow against a throwaway database. Run: python -m pytest"""

import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Role, User  # noqa: E402
from app.security import create_token  # noqa: E402

PHONE = "5559998877"


def login(client: TestClient, phone: str) -> dict:
    r = client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "code": "1234"})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_register_login_profile_refresh_and_roles():
    with TestClient(app) as client:
        # Register: invalid phone rejected, valid phone gets an OTP.
        bad_phone = client.post("/api/v1/auth/register", json={"phone_number": "123"})
        assert bad_phone.status_code == 422
        assert bad_phone.json()["error"]["code"] == "VALIDATION_ERROR"
        assert client.post("/api/v1/auth/register", json={"phone_number": PHONE}).json()["success"]

        # Wrong OTP fails and creates no account.
        wrong = client.post("/api/v1/auth/verify-otp", json={"phone_number": PHONE, "code": "0000"})
        assert wrong.status_code == 400
        assert wrong.json() == {"success": False, "data": None,
                                "error": {"code": "INVALID_OTP", "message": "Doğrulama kodu hatalı"}}

        # Correct OTP: new customer with an incomplete profile.
        data = login(client, PHONE)
        assert data["user"]["role"] == "CUSTOMER"
        assert data["user"]["profile_completed"] is False

        # Protected endpoint needs a token.
        assert client.get("/api/v1/users/me").status_code == 401
        me = client.get("/api/v1/users/me", headers=bearer(data["access_token"]))
        assert me.json()["data"]["phone_number"] == PHONE

        # Profile completion.
        updated = client.patch("/api/v1/users/me", headers=bearer(data["access_token"]),
                               json={"full_name": "Ayşe Yılmaz", "preferences": {"coffee": ["latte"]}})
        assert updated.json()["data"]["profile_completed"] is True

        # Second login reuses the same account.
        assert login(client, PHONE)["user"]["id"] == data["user"]["id"]

        # Refresh gives a working access token; an access token cannot be used as a refresh token.
        refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert client.get("/api/v1/users/me", headers=bearer(refreshed.json()["data"]["access_token"])).status_code == 200
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": data["access_token"]}).status_code == 401
        # And a refresh token cannot be used as an access token.
        assert client.get("/api/v1/users/me", headers=bearer(data["refresh_token"])).status_code == 401

        # Customers cannot reach admin endpoints.
        assert client.get("/api/v1/users", headers=bearer(data["access_token"])).status_code == 403

        # Admin can promote the customer to shop owner, and it applies to the existing token at once.
        with SessionLocal() as db:
            admin = User(phone_number="5550000099", role=Role.ADMIN)
            db.add(admin)
            db.commit()
            admin_token = create_token(admin.id, "access")
        promoted = client.patch(f"/api/v1/users/{data['user']['id']}/role",
                                headers=bearer(admin_token), json={"role": "SHOP_OWNER"})
        assert promoted.json()["data"]["role"] == "SHOP_OWNER"
        assert client.get("/api/v1/users/me", headers=bearer(data["access_token"])).json()["data"]["role"] == "SHOP_OWNER"
