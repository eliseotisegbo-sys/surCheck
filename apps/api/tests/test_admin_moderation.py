"""Tests automatisés pour la Phase 7 : Administration, Modération des signalements et Journal d'audit."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from src.main import app
from src.routers.auth import get_current_user
from src.schemas import ReportStatus
import src.routers.reports as reports_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_in_memory_reports():
    """Nettoie IN_MEMORY_REPORTS avant chaque test pour éviter la pollution entre tests."""
    reports_module.IN_MEMORY_REPORTS.clear()
    yield
    reports_module.IN_MEMORY_REPORTS.clear()


@pytest.fixture
def admin_user():
    return {"id": "admin_uuid_123", "role": "admin", "email": "admin@surcheck.bj"}


@pytest.fixture
def normal_user():
    return {"id": "user_uuid_456", "role": "user", "email": "citoyen@surcheck.bj"}


def test_admin_endpoints_require_admin_role(normal_user):
    """Vérifie le blocage HTTP 403 pour un utilisateur normal sans rôle admin."""
    app.dependency_overrides[get_current_user] = lambda: normal_user

    res = client.get("/api/v1/admin/stats")
    assert res.status_code == 403
    assert "réservé aux administrateurs" in res.json().get("detail", "")

    res = client.get("/api/v1/admin/reports")
    assert res.status_code == 403

    res = client.get("/api/v1/admin/audit-logs")
    assert res.status_code == 403

    app.dependency_overrides.clear()


def test_admin_stats_endpoint(admin_user):
    """Vérifie le bon fonctionnement du endpoint de métriques globales."""
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Mock Supabase pour ne pas dépendre d'une vraie connexion réseau
    async def mock_stats():
        return {
            "reports_total": 0,
            "reports_nouveau": 0,
            "reports_en_verification": 0,
            "reports_confirme": 0,
            "reports_non_confirme": 0,
            "analyses_total": 42,
            "users_total": 10,
        }

    with patch("src.services.supabase_db.supabase_db.get_admin_dashboard_stats", side_effect=mock_stats):
        res = client.get("/api/v1/admin/stats")
        assert res.status_code == 200
        data = res.json()
        assert "reports_total" in data
        assert "reports_nouveau" in data
        assert "analyses_total" in data
        assert data["analyses_total"] == 42

    app.dependency_overrides.clear()


def test_admin_reports_listing_and_moderation_flow(admin_user):
    """Vérifie le cycle de vie complet de modération d'un signalement."""
    app.dependency_overrides[get_current_user] = lambda: admin_user

    # Mock Supabase pour isolation complète (pas de réseau en CI)
    async def mock_save_report(request):
        return True

    async def mock_supabase_reports(status_filter=None, limit=50, offset=0):
        # Retourne liste vide pour forcer le fallback sur IN_MEMORY_REPORTS
        return []

    async def mock_moderate_report(report_id, new_status, moderation_notes=None, admin_id=None):
        return {"id": report_id, "status": new_status}

    async def mock_record_audit_log(**kwargs):
        return True

    with patch("src.services.supabase_db.supabase_db.save_report", side_effect=mock_save_report), \
         patch("src.services.supabase_db.supabase_db.get_admin_reports", side_effect=mock_supabase_reports), \
         patch("src.services.supabase_db.supabase_db.moderate_report", side_effect=mock_moderate_report), \
         patch("src.services.supabase_db.supabase_db.record_audit_log", side_effect=mock_record_audit_log):

        # 1. Créer un signalement via l'API publique
        rep_res = client.post(
            "/api/v1/reports",
            json={
                "report_type": "phone",
                "target": "+22997001122",
                "category": "faux_transfert_erreur",
                "description": "Faux appel pour soi-disant annuler un transfert",
            }
        )
        assert rep_res.status_code == 201
        report_id = rep_res.json()["id"]

        # Vérifier que le signalement est bien en IN_MEMORY_REPORTS
        assert len(reports_module.IN_MEMORY_REPORTS) == 1
        assert reports_module.IN_MEMORY_REPORTS[0]["id"] == report_id

        # 2. Lister les signalements côté admin (Supabase mocké retourne [], fallback mémoire activé)
        list_res = client.get("/api/v1/admin/reports")
        assert list_res.status_code == 200
        reports = list_res.json()["reports"]
        assert len(reports) >= 1, f"Aucun rapport trouvé. IN_MEMORY: {reports_module.IN_MEMORY_REPORTS}"
        assert any(r["id"] == report_id for r in reports), f"Report {report_id} absent de {reports}"

        # 3. Passer en 'en_verification'
        mod_res1 = client.patch(
            f"/api/v1/admin/reports/{report_id}/moderate",
            json={
                "status": "en_verification",
                "moderation_notes": "En cours de recoupement avec la base OCRC",
            }
        )
        assert mod_res1.status_code == 200
        assert mod_res1.json()["new_status"] == "en_verification"

        # 4. Confirmer le signalement avec éléments suffisants
        mod_res2 = client.patch(
            f"/api/v1/admin/reports/{report_id}/moderate",
            json={
                "status": "confirme_elements_suffisants",
                "moderation_notes": "3 victimes concordantes, numéro frauduleux confirmé",
            }
        )
        assert mod_res2.status_code == 200
        assert mod_res2.json()["new_status"] == "confirme_elements_suffisants"

        # 5. Consulter le journal d'audit
        with patch("src.services.supabase_db.supabase_db.get_audit_logs", new_callable=AsyncMock, return_value=[
            {"id": "log1", "action": "moderate_report", "admin_id": "admin_uuid_123"}
        ]):
            audit_res = client.get("/api/v1/admin/audit-logs")
            assert audit_res.status_code == 200
            assert "logs" in audit_res.json()

    app.dependency_overrides.clear()
