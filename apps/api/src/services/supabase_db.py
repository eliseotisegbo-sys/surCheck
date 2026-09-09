"""Service d'intégration et persistance Supabase pour SûrCheck AI.
Gère les interactions avec PostgreSQL via l'API PostgREST Supabase.
Conforme aux règles de résilience, d'anonymisation et d'audit.
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import httpx
from ..config import settings
from ..schemas import AnalysisResult, DetectedSignal, CreateReportRequest, AnalysisFeedbackRequest
from ..engine.reputation import (
    normalize_phone_number,
    hash_phone_number,
    mask_phone_number,
    mask_url,
)
from ..engine.normalizer import normalize_url

logger = logging.getLogger("surcheck.database")


class SupabaseService:
    """Client asynchrone résilient pour interagir avec Supabase."""

    def __init__(self):
        self.url = settings.SUPABASE_URL.rstrip("/")
        # Utilise la clé service_role si disponible (contourne RLS côté backend), sinon la clé anon
        self.api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY

    def _get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def save_analysis(
        self,
        result: AnalysisResult,
        raw_content: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Enregistre une analyse dans la table 'analyses' et ses signaux dans 'analysis_features'."""
        try:
            content_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
            # Anonymisation de l'extrait conservé (tronqué à 250 caractères)
            content_excerpt = raw_content.strip()[:250]

            analysis_payload = {
                "id": result.id,
                "user_id": user_id,
                "content_type": result.content_type.value,
                "content_hash": content_hash,
                "content_excerpt": content_excerpt,
                "risk_score": result.risk_score,
                "risk_level": result.risk_level.value,
                "category": result.category,
                "confidence_level": result.confidence_level,
                "engine_version": result.engine_version,
                "signals_count": len(result.signals),
                "is_public": False,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(
                    f"{self.url}/rest/v1/analyses",
                    headers=self._get_headers(),
                    json=analysis_payload,
                )

                if res.status_code not in (200, 201):
                    logger.warning(f"Échec insertion analyses dans Supabase ({res.status_code}): {res.text}")
                    return False

                # Insertion des signaux dans analysis_features pour traçabilité
                if result.signals:
                    features_payload = [
                        {
                            "analysis_id": result.id,
                            "rule_code": s.code,
                            "signal_name": s.title,
                            "signal_category": s.category,
                            "score_weight": s.weight,
                            "raw_evidence": s.evidence[:300] if s.evidence else None,
                        }
                        for s in result.signals
                    ]

                    await client.post(
                        f"{self.url}/rest/v1/analysis_features",
                        headers=self._get_headers(),
                        json=features_payload,
                    )

                return True

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde Supabase de l'analyse {result.id}: {e}")
            return False

    async def save_report(
        self,
        report_data: CreateReportRequest,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Enregistre un signalement communautaire et met à jour l'index de réputation."""
        try:
            target_str = report_data.target.strip()

            if report_data.report_type.value == "phone":
                norm_target = normalize_phone_number(target_str)
                target_hash = hash_phone_number(norm_target)
                target_masked = mask_phone_number(norm_target)
            elif report_data.report_type.value == "url":
                norm_target = normalize_url(target_str)
                target_hash = hashlib.sha256(norm_target.encode("utf-8")).hexdigest()
                target_masked = mask_url(norm_target)
            else:
                norm_target = target_str[:250]
                target_hash = hashlib.sha256(norm_target.encode("utf-8")).hexdigest()
                target_masked = target_str[:20] + "•••"

            report_payload = {
                "user_id": user_id,
                "report_type": report_data.report_type.value,
                "target": target_masked,
                "target_hash": target_hash,
                "category": report_data.category,
                "description": report_data.description,
                "evidence_url": report_data.evidence_url,
                "status": "nouveau",
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(
                    f"{self.url}/rest/v1/reports",
                    headers=self._get_headers(),
                    json=report_payload,
                )

                if res.status_code in (200, 201):
                    created_report = res.json()[0] if isinstance(res.json(), list) else res.json()

                    # Mise à jour ou insertion dans reported_numbers
                    if report_data.report_type.value == "phone":
                        await self._increment_reported_number(client, target_hash)
                    elif report_data.report_type.value == "url":
                        await self._increment_reported_url(client, norm_target, target_hash)

                    return created_report
                else:
                    logger.warning(f"Erreur enregistrement report ({res.status_code}): {res.text}")
                    return None

        except Exception as e:
            logger.error(f"Exception lors de la sauvegarde du signalement: {e}")
            return None

    async def _increment_reported_number(self, client: httpx.AsyncClient, phone_hash: str):
        """Incrémente le compteur de signalement d'un numéro haché."""
        try:
            # Vérifier si le numéro existe déjà
            check_res = await client.get(
                f"{self.url}/rest/v1/reported_numbers?phone_hash=eq.{phone_hash}&select=*",
                headers=self._get_headers(),
            )
            data = check_res.json() if check_res.status_code == 200 else []

            if data and len(data) > 0:
                current_count = data[0].get("report_count", 1)
                await client.patch(
                    f"{self.url}/rest/v1/reported_numbers?phone_hash=eq.{phone_hash}",
                    headers=self._get_headers(),
                    json={"report_count": current_count + 1},
                )
            else:
                await client.post(
                    f"{self.url}/rest/v1/reported_numbers",
                    headers=self._get_headers(),
                    json={
                        "phone_hash": phone_hash,
                        "country_code": "+229",
                        "report_count": 1,
                        "confirmed_count": 0,
                        "status": "nouveau",
                    },
                )
        except Exception as e:
            logger.warning(f"Erreur incrément reported_number: {e}")

    async def _increment_reported_url(self, client: httpx.AsyncClient, normalized_url: str, domain_hash: str):
        """Incrémente le compteur de signalement d'une URL."""
        try:
            check_res = await client.get(
                f"{self.url}/rest/v1/reported_urls?domain_hash=eq.{domain_hash}&select=*",
                headers=self._get_headers(),
            )
            data = check_res.json() if check_res.status_code == 200 else []

            if data and len(data) > 0:
                current_count = data[0].get("report_count", 1)
                await client.patch(
                    f"{self.url}/rest/v1/reported_urls?domain_hash=eq.{domain_hash}",
                    headers=self._get_headers(),
                    json={"report_count": current_count + 1},
                )
            else:
                await client.post(
                    f"{self.url}/rest/v1/reported_urls",
                    headers=self._get_headers(),
                    json={
                        "normalized_url": normalized_url,
                        "domain_hash": domain_hash,
                        "report_count": 1,
                        "status": "nouveau",
                    },
                )
        except Exception as e:
            logger.warning(f"Erreur incrément reported_url: {e}")

    async def check_phone_reputation(self, phone: str) -> Tuple[int, str]:
        """Interroge la réputation communautaire d'un numéro.
        Retourne (report_count, status).
        """
        try:
            norm_phone = normalize_phone_number(phone)
            phone_hash = hash_phone_number(norm_phone)

            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/reported_numbers?phone_hash=eq.{phone_hash}&select=report_count,status",
                    headers=self._get_headers(),
                )

                if res.status_code == 200:
                    data = res.json()
                    if data and len(data) > 0:
                        return data[0].get("report_count", 0), data[0].get("status", "nouveau")

        except Exception as e:
            logger.warning(f"Impossible d'interroger la réputation du numéro: {e}")

        return 0, "inconnu"

    async def check_url_reputation(self, url: str) -> Tuple[int, bool, str]:
        """Interroge la réputation communautaire d'un lien.
        Retourne (report_count, phishing_feed_match, status).
        """
        try:
            norm_url = normalize_url(url)
            domain_hash = hashlib.sha256(norm_url.encode("utf-8")).hexdigest()

            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/reported_urls?domain_hash=eq.{domain_hash}&select=report_count,phishing_feed_match,status",
                    headers=self._get_headers(),
                )

                if res.status_code == 200:
                    data = res.json()
                    if data and len(data) > 0:
                        return (
                            data[0].get("report_count", 0),
                            data[0].get("phishing_feed_match", False),
                            data[0].get("status", "nouveau")
                        )

        except Exception as e:
            logger.warning(f"Impossible d'interroger la réputation de l'URL: {e}")

        return 0, False, "inconnu"

    async def save_feedback(self, feedback: AnalysisFeedbackRequest, user_id: Optional[str] = None) -> bool:
        """Enregistre le retour utilisateur sur une analyse."""
        try:
            payload = {
                "analysis_id": feedback.analysis_id,
                "user_id": user_id,
                "is_helpful": feedback.is_helpful,
                "perceived_accuracy": feedback.perceived_accuracy,
                "user_comment": feedback.user_comment,
            }

            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(
                    f"{self.url}/rest/v1/analysis_feedback",
                    headers=self._get_headers(),
                    json=payload,
                )
                return res.status_code in (200, 201)
        except Exception as e:
            logger.error(f"Erreur enregistrement feedback: {e}")
            return False

    async def create_user(self, name: str, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """Crée un utilisateur dans la table 'users' de Supabase."""
        try:
            payload = {
                "name": name.strip(),
                "email": email.strip().lower(),
                "password_hash": password_hash,
                "role": "user",
                "free_analyses_quota": 5,
                "paid_credits_balance": 0,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(
                    f"{self.url}/rest/v1/users",
                    headers=self._get_headers(),
                    json=payload,
                )

                if res.status_code in (200, 201):
                    data = res.json()
                    return data[0] if isinstance(data, list) else data
                else:
                    logger.warning(f"Erreur création utilisateur ({res.status_code}): {res.text}")
                    return None
        except Exception as e:
            logger.error(f"Exception lors de la création d'utilisateur: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Recherche un utilisateur par son adresse email."""
        try:
            clean_email = email.strip().lower()
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/users?email=eq.{clean_email}&select=*",
                    headers=self._get_headers(),
                )

                if res.status_code == 200:
                    data = res.json()
                    if data and len(data) > 0:
                        return data[0]
        except Exception as e:
            logger.warning(f"Erreur recherche utilisateur: {e}")
        return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Recherche un utilisateur par son ID."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/users?id=eq.{user_id}&select=*",
                    headers=self._get_headers(),
                )

                if res.status_code == 200:
                    data = res.json()
                    if data and len(data) > 0:
                        return data[0]
        except Exception as e:
            logger.warning(f"Erreur recherche utilisateur par id: {e}")
        return None

    async def get_user_analyses(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Récupère l'historique d'analyses d'un utilisateur connecté."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/analyses?user_id=eq.{user_id}&order=created_at.desc&limit={limit}&select=*",
                    headers=self._get_headers(),
                )

                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Erreur récupération historique: {e}")
        return []

    async def get_admin_reports(
        self,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Récupère les signalements communautaires pour la console de modération."""
        try:
            url = f"{self.url}/rest/v1/reports?order=created_at.desc&limit={limit}&offset={offset}&select=*"
            if status_filter:
                url += f"&status=eq.{status_filter}"

            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Erreur get_admin_reports: {e}")
        return []

    async def moderate_report(
        self,
        report_id: str,
        new_status: str,
        moderation_notes: Optional[str] = None,
        admin_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Met à jour le statut d'un signalement et consigne l'action dans le journal d'audit."""
        try:
            now = datetime.now().isoformat()
            payload = {
                "status": new_status,
                "moderated_by": admin_id,
                "moderation_notes": moderation_notes,
                "updated_at": now,
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                # 1. Récupérer le rapport actuel pour le diff d'audit
                current_res = await client.get(
                    f"{self.url}/rest/v1/reports?id=eq.{report_id}&select=*",
                    headers=self._get_headers(),
                )
                old_report = current_res.json()[0] if current_res.status_code == 200 and current_res.json() else {}
                old_status = old_report.get("status", "inconnu")

                # 2. Mettre à jour le signalement
                res = await client.patch(
                    f"{self.url}/rest/v1/reports?id=eq.{report_id}",
                    headers=self._get_headers(),
                    json=payload,
                )

                if res.status_code in (200, 204):
                    updated_data = res.json()[0] if res.status_code == 200 and isinstance(res.json(), list) and res.json() else {**old_report, **payload}

                    # 3. Si confirmé, incrémenter confirmed_count sur le numéro ou l'URL
                    if new_status == "confirme_elements_suffisants" and old_report:
                        target_hash = old_report.get("target_hash")
                        report_type = old_report.get("report_type")
                        if target_hash and report_type == "phone":
                            await client.patch(
                                f"{self.url}/rest/v1/reported_numbers?phone_hash=eq.{target_hash}",
                                headers=self._get_headers(),
                                json={"status": "confirme_elements_suffisants"},
                            )
                        elif target_hash and report_type == "url":
                            await client.patch(
                                f"{self.url}/rest/v1/reported_urls?domain_hash=eq.{target_hash}",
                                headers=self._get_headers(),
                                json={"status": "confirme_elements_suffisants"},
                            )

                    # 4. Enregistrer dans admin_audit_logs
                    await self.record_audit_log(
                        admin_id=admin_id,
                        action="moderate_report",
                        target_entity="reports",
                        entity_id=report_id,
                        changes={
                            "old_status": old_status,
                            "new_status": new_status,
                            "notes": moderation_notes,
                        },
                    )

                    return updated_data
        except Exception as e:
            logger.error(f"Erreur moderate_report ({report_id}): {e}")
        return None

    async def record_audit_log(
        self,
        admin_id: Optional[str],
        action: str,
        target_entity: str,
        entity_id: str,
        changes: Dict[str, Any]
    ) -> bool:
        """Enregistre une ligne d'audit inaltérable dans admin_audit_logs."""
        try:
            audit_payload = {
                "admin_id": admin_id,
                "action": action,
                "target_entity": target_entity,
                "entity_id": str(entity_id),
                "changes_json": changes,
            }

            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(
                    f"{self.url}/rest/v1/admin_audit_logs",
                    headers=self._get_headers(),
                    json=audit_payload,
                )
                return res.status_code in (200, 201)
        except Exception as e:
            logger.warning(f"Erreur record_audit_log: {e}")
            return False

    async def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère l'historique chronologique des actions administratives."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    f"{self.url}/rest/v1/admin_audit_logs?order=created_at.desc&limit={limit}&select=*",
                    headers=self._get_headers(),
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Erreur get_audit_logs: {e}")
        return []

    async def get_admin_dashboard_stats(self) -> Dict[str, Any]:
        """Agrège les statistiques clés de modération et d'activité."""
        stats = {
            "reports_total": 0,
            "reports_nouveau": 0,
            "reports_en_verification": 0,
            "reports_confirme": 0,
            "reports_non_confirme": 0,
            "analyses_total": 0,
            "users_total": 0,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Total analyses
                r_an = await client.get(
                    f"{self.url}/rest/v1/analyses?select=id",
                    headers={**self._get_headers(), "Range": "0-0", "Prefer": "count=exact"},
                )
                if "content-range" in r_an.headers:
                    parts = r_an.headers["content-range"].split("/")
                    if len(parts) > 1 and parts[1].isdigit():
                        stats["analyses_total"] = int(parts[1])

                # Reports
                r_rep = await client.get(
                    f"{self.url}/rest/v1/reports?select=status",
                    headers=self._get_headers(),
                )
                if r_rep.status_code == 200:
                    reports = r_rep.json()
                    stats["reports_total"] = len(reports)
                    for r in reports:
                        st = r.get("status")
                        if st == "nouveau":
                            stats["reports_nouveau"] += 1
                        elif st == "en_verification":
                            stats["reports_en_verification"] += 1
                        elif st == "confirme_elements_suffisants":
                            stats["reports_confirme"] += 1
                        elif st == "non_confirme":
                            stats["reports_non_confirme"] += 1

                # Total users
                r_usr = await client.get(
                    f"{self.url}/rest/v1/users?select=id",
                    headers={**self._get_headers(), "Range": "0-0", "Prefer": "count=exact"},
                )
                if "content-range" in r_usr.headers:
                    parts = r_usr.headers["content-range"].split("/")
                    if len(parts) > 1 and parts[1].isdigit():
                        stats["users_total"] = int(parts[1])

        except Exception as e:
            logger.warning(f"Erreur get_admin_dashboard_stats: {e}")

        return stats


# Instance unique partagée
supabase_db = SupabaseService()
