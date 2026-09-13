"""Tests de validation des secrets au démarrage.

Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 1.5
"""

import os
import sys
import pytest
from unittest.mock import patch


def test_validation_skipped_in_development():
    """La validation doit être ignorée en development."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "development"
        mock_settings.JWT_SECRET_KEY = ""
        mock_settings.PHONE_HASH_SALT = ""
        
        from src.main import validate_production_secrets
        
        # Ne doit pas lever d'exception
        validate_production_secrets()


def test_validation_skipped_in_test():
    """La validation doit être ignorée en test."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "test"
        mock_settings.JWT_SECRET_KEY = ""
        
        from src.main import validate_production_secrets
        
        # Ne doit pas lever d'exception
        validate_production_secrets()


def test_validation_fails_with_empty_jwt_secret():
    """Doit refuser démarrage si JWT_SECRET_KEY vide en production."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        mock_settings.JWT_SECRET_KEY = ""
        mock_settings.PHONE_HASH_SALT = "valid_salt_123"
        mock_settings.DATABASE_URL = "postgresql://user:pass@host/db"
        mock_settings.SASPAY_API_KEY = "sk_live_valid_key"
        mock_settings.SASPAY_WEBHOOK_SECRET = "valid_webhook_secret"
        
        from src.main import validate_production_secrets
        
        with pytest.raises(SystemExit) as exc_info:
            validate_production_secrets()
        
        assert exc_info.value.code == 1


def test_validation_fails_with_dev_jwt_secret():
    """Doit refuser démarrage si JWT_SECRET_KEY = valeur dev en production."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        mock_settings.JWT_SECRET_KEY = "surcheck_jwt_secret_key_production_grade_super_secret_bj"
        mock_settings.PHONE_HASH_SALT = "valid_salt_123"
        mock_settings.DATABASE_URL = "postgresql://user:pass@host/db"
        mock_settings.SASPAY_API_KEY = "sk_live_valid_key"
        mock_settings.SASPAY_WEBHOOK_SECRET = "valid_webhook_secret"
        
        from src.main import validate_production_secrets
        
        with pytest.raises(SystemExit) as exc_info:
            validate_production_secrets()
        
        assert exc_info.value.code == 1


def test_validation_warns_with_test_saspay_key():
    """Doit refuser démarrage si SASPAY_API_KEY en sk_test_* en production."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        mock_settings.JWT_SECRET_KEY = "valid_jwt_secret_123"
        mock_settings.PHONE_HASH_SALT = "valid_salt_123"
        mock_settings.DATABASE_URL = "postgresql://user:pass@host/db"
        mock_settings.SASPAY_API_KEY = "sk_test_should_not_be_used_in_prod"
        mock_settings.SASPAY_WEBHOOK_SECRET = "valid_webhook_secret"
        
        from src.main import validate_production_secrets
        
        with pytest.raises(SystemExit) as exc_info:
            validate_production_secrets()
        
        assert exc_info.value.code == 1


def test_validation_passes_with_all_valid_secrets():
    """Doit démarrer normalement si tous les secrets sont valides en production."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        mock_settings.JWT_SECRET_KEY = "valid_production_jwt_secret_key_12345"
        mock_settings.PHONE_HASH_SALT = "valid_production_salt_67890"
        mock_settings.DATABASE_URL = "postgresql://postgres.ref:SecurePass123@host.supabase.com:6543/postgres"
        mock_settings.SASPAY_API_KEY = "sk_live_VALID_TEST_KEY_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        mock_settings.SASPAY_WEBHOOK_SECRET = "valid_webhook_secret_hash_12345678901234567890123456789012"
        
        from src.main import validate_production_secrets
        
        # Ne doit pas lever d'exception
        validate_production_secrets()


def test_validation_fails_with_empty_database_url():
    """Doit refuser démarrage si DATABASE_URL vide en production."""
    with patch("src.main.settings") as mock_settings:
        mock_settings.ENVIRONMENT = "production"
        mock_settings.JWT_SECRET_KEY = "valid_jwt_secret_123"
        mock_settings.PHONE_HASH_SALT = "valid_salt_123"
        mock_settings.DATABASE_URL = ""
        mock_settings.SASPAY_API_KEY = "sk_live_valid_key"
        mock_settings.SASPAY_WEBHOOK_SECRET = "valid_webhook_secret"
        
        from src.main import validate_production_secrets
        
        with pytest.raises(SystemExit) as exc_info:
            validate_production_secrets()
        
        assert exc_info.value.code == 1
