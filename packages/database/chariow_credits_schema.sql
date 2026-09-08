-- ====================================================================
-- SÛRCHECK AI — EXTENSION CRÉDITS & PAIEMENT CHARIOW
-- Compatible Supabase & PostgreSQL 14+
-- Conforme au document technique SuCheck_Chariow_API_Modele_Paiement_Credits_Antigravity.md
-- ====================================================================

-- 1. TABLE CREDIT_WALLETS (Portefeuille de crédits rattaché au compte utilisateur)
CREATE TABLE IF NOT EXISTS credit_wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    balance INT NOT NULL DEFAULT 0 CHECK (balance >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. TABLE CREDIT_TRANSACTIONS (Journal financier d'attribution et de consommation)
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id UUID REFERENCES credit_wallets(id) ON DELETE SET NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('purchase', 'consumption', 'refund', 'bonus', 'admin_adjustment', 'expiration')),
    amount INT NOT NULL, -- Positif pour ajout, négatif pour consommation
    balance_before INT NOT NULL,
    balance_after INT NOT NULL,
    reference_type VARCHAR(50), -- 'analysis_unlock', 'chariow_sale', 'admin_adjustment'
    reference_id VARCHAR(150),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. TABLE ANALYSIS_UNLOCKS (Traçabilité stricte du déblocage de l'analyse complète - anti-double clic)
CREATE TABLE IF NOT EXISTS analysis_unlocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    credit_transaction_id UUID REFERENCES credit_transactions(id) ON DELETE SET NULL,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_analysis_user_unlock UNIQUE (analysis_id, user_id)
);

-- 4. MISE À JOUR DE LA TABLE PAYMENT_TRANSACTIONS POUR CHARIOW
ALTER TABLE payment_transactions
    ADD COLUMN IF NOT EXISTS external_sale_id VARCHAR(150),
    ADD COLUMN IF NOT EXISTS external_transaction_id VARCHAR(150),
    ADD COLUMN IF NOT EXISTS product_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS pack_code VARCHAR(50),
    ADD COLUMN IF NOT EXISTS raw_event_id VARCHAR(150),
    ADD COLUMN IF NOT EXISTS raw_payload_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

-- Contrainte d'unicité pour garantir l'idempotence des ventes Chariow
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_payment_provider_external_sale'
    ) THEN
        ALTER TABLE payment_transactions
        ADD CONSTRAINT uq_payment_provider_external_sale UNIQUE (provider, external_sale_id);
    END IF;
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 5. INDEX STRATÉGIQUES POUR PERFORMANCE ET RECHERCHE
CREATE INDEX IF NOT EXISTS idx_credit_wallets_user_id ON credit_wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_unlocks_lookup ON analysis_unlocks(analysis_id, user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_sale ON payment_transactions(provider, external_sale_id);

-- 6. POLITIQUES RLS (ROW LEVEL SECURITY)
ALTER TABLE credit_wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_unlocks ENABLE ROW LEVEL SECURITY;

-- Lecture du portefeuille par son propriétaire
DO $$ BEGIN
    CREATE POLICY "Users can read own credit wallet"
    ON credit_wallets FOR SELECT
    USING (auth.uid() = user_id OR auth.role() = 'anon');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Lecture de l'historique de crédits par son propriétaire
DO $$ BEGIN
    CREATE POLICY "Users can read own credit transactions"
    ON credit_transactions FOR SELECT
    USING (auth.uid() = user_id OR auth.role() = 'anon');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Lecture des analyses débloquées
DO $$ BEGIN
    CREATE POLICY "Users can read own unlocked analyses"
    ON analysis_unlocks FOR SELECT
    USING (auth.uid() = user_id OR auth.role() = 'anon');
EXCEPTION WHEN duplicate_object THEN null;
END $$;
