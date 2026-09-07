-- ====================================================================
-- SÛRCHECK AI — SCHÉMA OFFICIEL POSTGRESQL (12 TABLES)
-- Compatible Supabase & PostgreSQL 14+
-- Conforme aux sections 8 & 33 du Cahier des Charges
-- ====================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. ENUMS
DO $$ BEGIN
    CREATE TYPE risk_level_enum AS ENUM ('faible', 'prudence', 'eleve');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE content_type_enum AS ENUM ('text', 'image', 'url');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE report_status_enum AS ENUM (
        'nouveau',
        'en_verification',
        'confirme_elements_suffisants',
        'non_confirme',
        'conteste',
        'retire'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE report_type_enum AS ENUM ('phone', 'url', 'message', 'page');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE payment_status_enum AS ENUM ('pending', 'successful', 'failed', 'refunded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 3. TABLE USERS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'moderator', 'admin')),
    free_analyses_quota INT NOT NULL DEFAULT 5,
    paid_credits_balance INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. TABLE ANALYSES
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    content_type content_type_enum NOT NULL DEFAULT 'text',
    content_hash VARCHAR(64), -- SHA-256 du contenu pour dédoublonnage
    content_excerpt TEXT NOT NULL, -- Texte anonymisé / extrait analysé
    risk_score INT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level risk_level_enum NOT NULL,
    category VARCHAR(50) NOT NULL, -- Mobile Money, Phishing, Faux emploi, etc.
    confidence_level VARCHAR(20) NOT NULL DEFAULT 'elevee', -- elevee, moyenne, incertain
    engine_version VARCHAR(20) NOT NULL DEFAULT 'v1.0.0',
    signals_count INT NOT NULL DEFAULT 0,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. TABLE ANALYSIS_FEATURES (Traçabilité et reproductibilité du scoring)
CREATE TABLE IF NOT EXISTS analysis_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    rule_code VARCHAR(50) NOT NULL,
    signal_name VARCHAR(150) NOT NULL,
    signal_category VARCHAR(50) NOT NULL,
    score_weight INT NOT NULL,
    raw_evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. TABLE ANALYSIS_FEEDBACK
CREATE TABLE IF NOT EXISTS analysis_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_helpful BOOLEAN NOT NULL,
    perceived_accuracy VARCHAR(30), -- 'juste', 'surévalué', 'sous_évalué'
    user_comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. TABLE REPORTS (Signalement communautaire)
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    report_type report_type_enum NOT NULL,
    target VARCHAR(255) NOT NULL, -- Numéro, lien ou extrait
    target_hash VARCHAR(64) NOT NULL, -- Hash pour indexation sécurisée
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    evidence_url TEXT,
    status report_status_enum NOT NULL DEFAULT 'nouveau',
    moderated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    moderation_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. TABLE REPORTED_NUMBERS (Réputation des numéros, hachés)
CREATE TABLE IF NOT EXISTS reported_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash VARCHAR(64) UNIQUE NOT NULL,
    country_code VARCHAR(5) NOT NULL DEFAULT '+229',
    report_count INT NOT NULL DEFAULT 1,
    confirmed_count INT NOT NULL DEFAULT 0,
    status report_status_enum NOT NULL DEFAULT 'nouveau',
    last_reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. TABLE REPORTED_URLS (Réputation des URLs)
CREATE TABLE IF NOT EXISTS reported_urls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_url TEXT NOT NULL,
    domain_hash VARCHAR(64) NOT NULL,
    report_count INT NOT NULL DEFAULT 1,
    phishing_feed_match BOOLEAN NOT NULL DEFAULT FALSE,
    feed_source VARCHAR(100),
    status report_status_enum NOT NULL DEFAULT 'nouveau',
    last_reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. TABLE RISK_RULES (Règles déterministes à coût nul)
CREATE TABLE IF NOT EXISTS risk_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    pattern TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    score_weight INT NOT NULL,
    explanation_template TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. TABLE SCAM_PATTERNS (Patterns locaux Afrique de l'Ouest / Bénin)
CREATE TABLE IF NOT EXISTS scam_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_name VARCHAR(100) NOT NULL,
    country VARCHAR(10) NOT NULL DEFAULT 'BJ',
    channel VARCHAR(30) NOT NULL DEFAULT 'whatsapp', -- whatsapp, sms, facebook, tiktok
    trigger_keywords TEXT[] NOT NULL,
    weight INT NOT NULL DEFAULT 20,
    engine_version VARCHAR(20) NOT NULL DEFAULT 'v1.0.0',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 12. TABLE REPUTATION_EVENTS (Journalisation des flux de réputation)
CREATE TABLE IF NOT EXISTS reputation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_type VARCHAR(20) NOT NULL, -- phone, domain, url
    target_hash VARCHAR(64) NOT NULL,
    source VARCHAR(50) NOT NULL, -- community_report, external_feed, admin
    category VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(4, 2) NOT NULL DEFAULT 0.50,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. TABLE PAYMENT_TRANSACTIONS (Transactions avec webhook idempotent)
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL DEFAULT 'fedapay',
    external_reference VARCHAR(150) UNIQUE,
    idempotency_key VARCHAR(100) UNIQUE NOT NULL,
    pack_name VARCHAR(50) NOT NULL, -- mini, standard, protection
    amount_fcfa INT NOT NULL,
    credits_purchased INT NOT NULL,
    status payment_status_enum NOT NULL DEFAULT 'pending',
    webhook_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. TABLE ADMIN_AUDIT_LOGS (Journalisation stricte de la modération)
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    target_entity VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    changes_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 15. INDEX STRATÉGIQUES POUR PERFORMANCES MOBILES & SUPABASE
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_features_analysis_id ON analysis_features(analysis_id);
CREATE INDEX IF NOT EXISTS idx_reports_target_hash ON reports(target_hash);
CREATE INDEX IF NOT EXISTS idx_reported_numbers_phone_hash ON reported_numbers(phone_hash);
CREATE INDEX IF NOT EXISTS idx_reported_urls_domain_hash ON reported_urls(domain_hash);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_idempotency ON payment_transactions(idempotency_key);
