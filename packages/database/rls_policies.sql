-- ====================================================================
-- SÛRCHECK AI — POLITIQUES DE SÉCURITÉ ROW LEVEL SECURITY (RLS)
-- À exécuter dans le Supabase SQL Editor
-- Active les permissions pour l'application web et l'API
-- ====================================================================

-- 1. ACTIVER RLS SUR TOUTES LES TABLES CLÉS
ALTER TABLE IF EXISTS risk_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS scam_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analysis_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analysis_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS reported_numbers ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS reported_urls ENABLE ROW LEVEL SECURITY;

-- 2. POLITIQUES POUR RISK_RULES (Lecture publique pour le moteur)
DROP POLICY IF EXISTS "Allow public read on risk_rules" ON risk_rules;
CREATE POLICY "Allow public read on risk_rules"
ON risk_rules FOR SELECT
TO anon, authenticated
USING (active = true);

-- 3. POLITIQUES POUR SCAM_PATTERNS (Lecture publique pour le moteur)
DROP POLICY IF EXISTS "Allow public read on scam_patterns" ON scam_patterns;
CREATE POLICY "Allow public read on scam_patterns"
ON scam_patterns FOR SELECT
TO anon, authenticated
USING (active = true);

-- 4. POLITIQUES POUR ANALYSES (Création anonyme ou connectée, lecture de son analyse)
DROP POLICY IF EXISTS "Allow public insert on analyses" ON analyses;
CREATE POLICY "Allow public insert on analyses"
ON analyses FOR INSERT
TO anon, authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow public read on analyses" ON analyses;
CREATE POLICY "Allow public read on analyses"
ON analyses FOR SELECT
TO anon, authenticated
USING (true);

-- 5. POLITIQUES POUR ANALYSIS_FEATURES (Enregistrement des signaux)
DROP POLICY IF EXISTS "Allow public insert on analysis_features" ON analysis_features;
CREATE POLICY "Allow public insert on analysis_features"
ON analysis_features FOR INSERT
TO anon, authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow public read on analysis_features" ON analysis_features;
CREATE POLICY "Allow public read on analysis_features"
ON analysis_features FOR SELECT
TO anon, authenticated
USING (true);

-- 6. POLITIQUES POUR ANALYSIS_FEEDBACK (Retour utilisateur)
DROP POLICY IF EXISTS "Allow public insert on analysis_feedback" ON analysis_feedback;
CREATE POLICY "Allow public insert on analysis_feedback"
ON analysis_feedback FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- 7. POLITIQUES POUR REPORTS (Signalements communautaires)
DROP POLICY IF EXISTS "Allow public insert on reports" ON reports;
CREATE POLICY "Allow public insert on reports"
ON reports FOR INSERT
TO anon, authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow read on reports" ON reports;
CREATE POLICY "Allow read on reports"
ON reports FOR SELECT
TO anon, authenticated
USING (true);

-- 8. POLITIQUES POUR REPORTED_NUMBERS (Vérification de réputation des numéros)
DROP POLICY IF EXISTS "Allow public read on reported_numbers" ON reported_numbers;
CREATE POLICY "Allow public read on reported_numbers"
ON reported_numbers FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "Allow public insert/update on reported_numbers" ON reported_numbers;
CREATE POLICY "Allow public insert/update on reported_numbers"
ON reported_numbers FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- 9. POLITIQUES POUR REPORTED_URLS (Vérification de réputation des URLs)
DROP POLICY IF EXISTS "Allow public read on reported_urls" ON reported_urls;
CREATE POLICY "Allow public read on reported_urls"
ON reported_urls FOR SELECT
TO anon, authenticated
USING (true);

DROP POLICY IF EXISTS "Allow public insert/update on reported_urls" ON reported_urls;
CREATE POLICY "Allow public insert/update on reported_urls"
ON reported_urls FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- 10. POLITIQUES POUR USERS (Gestion profil autonome)
ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow user registration" ON users;
CREATE POLICY "Allow user registration"
ON users FOR INSERT
TO anon, authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "Allow read own user profile" ON users;
CREATE POLICY "Allow read own user profile"
ON users FOR SELECT
TO anon, authenticated
USING (true);

-- VÉRIFICATION FINALE DES TABLES
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
