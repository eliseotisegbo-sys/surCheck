"""Tests d'intégration des endpoints FastAPI de SûrCheck AI."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["engine_version"] == "v1.0.0"


def test_api_v1_healthcheck():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_analyze_text_endpoint_success():
    payload = {
        "content": "Bonjour, votre compte MTN Mobile Money va être suspendu. Envoyez votre code secret pour annuler."
    }
    response = client.post("/api/v1/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 70
    assert data["risk_level"] == "eleve"
    assert len(data["signals"]) > 0
    assert len(data["recommendations"]) > 0
    signal_codes = [s["code"] for s in data["signals"]]
    assert "RULE_OTP_PIN" in signal_codes or "RULE_USURPATION_MOMO" in signal_codes


def test_analyze_text_empty_error():
    payload = {"content": "   "}
    response = client.post("/api/v1/analyze/text", json=payload)
    assert response.status_code in (400, 422)


def test_analyze_url_endpoint():
    payload = {"url": "https://bit.ly/momo-promo-benin"}
    response = client.post("/api/v1/analyze/url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["content_type"] == "url"
    assert len(data["signals"]) > 0


def test_submit_report_endpoint():
    payload = {
        "report_type": "phone",
        "target": "+22997123456",
        "category": "Mobile Money",
        "description": "Appel vocal prétendant être le service client Moov demandant des informations sensibles.",
        "evidence_url": None
    }
    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "nouveau"
    assert "97" in data["target_masked"]
    assert "••" in data["target_masked"]


def test_submit_feedback_endpoint():
    feedback_payload = {
        "analysis_id": "test-analysis-uuid",
        "is_helpful": True,
        "perceived_accuracy": "juste",
        "user_comment": "Très clair et rapide."
    }
    response = client.post("/api/v1/analyze/feedback", json=feedback_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"


def test_auth_register_and_login_flow():
    import uuid
    unique_email = f"user_{uuid.uuid4().hex[:8]}@surcheck.bj"
    register_payload = {
        "name": "Koffi Mensah",
        "email": unique_email,
        "password": "SecurPass123_BJ",
    }
    # 1. Inscription
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["free_quota"] == 5
    assert reg_data["user_email"] == unique_email

    token = reg_data["access_token"]

    # 2. Vérification /me avec Bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == unique_email
    assert me_data["name"] == "Koffi Mensah"

    # 3. Connexion (Login)
    login_res = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "SecurPass123_BJ",
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data

    # 4. Connexion mauvais mot de passe
    bad_login = client.post("/api/v1/auth/login", json={
        "email": unique_email,
        "password": "WrongPassword999",
    })
    assert bad_login.status_code == 401

