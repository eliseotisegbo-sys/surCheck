-- ====================================================================
-- SÛRCHECK AI — DONNÉES INITIALES ET RÈGLES CALIBRÉES (SEEDS)
-- Données adaptées aux scénarios réels Bénin / Afrique de l'Ouest
-- ====================================================================

-- 1. Insertion des règles déterministes (risk_rules)
INSERT INTO risk_rules (rule_code, pattern, category, score_weight, explanation_template, recommendation_text) VALUES
('RULE_OTP_PIN', '(?i)(code\s*secret|code\s*otp|mot\s*de\s*passe|code\s*de\s*retrait|pin\s*moov|pin\s*mtn|votre\s*pin|mon\s*code)', 'Sécurité des comptes', 50, 'Demande explicite ou implicite de code secret, code OTP ou code PIN Mobile Money.', 'Ne transmettez jamais votre code secret ou code OTP. Aucun agent ou opérateur officiel ne vous demandera votre mot de passe ou code de retrait.')
ON CONFLICT (rule_code) DO NOTHING;

INSERT INTO risk_rules (rule_code, pattern, category, score_weight, explanation_template, recommendation_text) VALUES
('RULE_MONEY_REQ', '(?i)(envoyez|frais\s*de\s*dossier|frais\s*d['']inscription|caution|transfert\s*d['']argent|frais\s*de\s*d[eé]blocage|d[eé]p[oô]t\s*pr[eé]alable|commission\s*avant)', 'Demande d''argent', 35, 'Exigence d''un paiement d''argent préalable avant l''obtention d''un gain, d''un service ou d''un emploi.', 'Refusez tout versement d''argent ou de frais préalables. Les recruteurs sérieux et les concours officiels n''exigent jamais de caution par Mobile Money.')
ON CONFLICT (rule_code) DO NOTHING;

INSERT INTO risk_rules (rule_code, pattern, category, score_weight, explanation_template, recommendation_text) VALUES
('RULE_URGENCY', '(?i)(urgent|imm[eé]diat|dans\s*les\s*24h|imm[eé]diatement|votre\s*compte\s*sera\s*bloqu[eé]|derni[eè]re\s*chance|expire\s*aujourd['']hui|d[eé]lai\s*de\s*rigueur)', 'Pression psychologique', 20, 'Création d''une urgence artificielle incitant à agir sous la panique sans vérifier.', 'Prenez le temps de respirer et de vérifier auprès de la source officielle. L''empressement injustifié est l''indicateur de manipulation le plus fréquent.')
ON CONFLICT (rule_code) DO NOTHING;

INSERT INTO risk_rules (rule_code, pattern, category, score_weight, explanation_template, recommendation_text) VALUES
('RULE_UNREAL_GAIN', '(?i)(gagnant|f[eé]licitations|vous\s*avez\s*gagn[eé]|tirage\s*au\s*sort|somme\s*de\s*[0-9]+(\s*000|\s*millions)|subvention|aide\s*financi[eè]re|b[eé]n[eé]ficiaire\s*s[eé]lectionn[eé])', 'Promesse de gain', 25, 'Promesse d''un gain important, d''une loterie ou d''une subvention sans participation vérifiable.', 'Si vous n''avez participé à aucun jeu ou concours officiel, vous ne pouvez rien avoir gagné. Méfiez-vous des faux tirages au sort.')
ON CONFLICT (rule_code) DO NOTHING;

INSERT INTO risk_rules (rule_code, pattern, category, score_weight, explanation_template, recommendation_text) VALUES
('RULE_SUSPICIOUS_LINK', '(?i)(https?://(bit\.ly|tinyurl\.com|is\.gd|t\.co|cutt\.ly|rb\.gy|wa\.me|goo\.su)/[a-zA-Z0-9_-]+)', 'Lien suspect', 30, 'Présence d''un lien raccourci ou masqué empêchant l''identification du domaine réel.', 'Ne cliquez pas sur ce lien raccourci. Les services officiels utilisent leurs propres noms de domaine connus et vérifiés.')
ON CONFLICT (rule_code) DO NOTHING;

INSERT INTO risk_rules (rule_code, pattern, category, score_weight, explanation_template, recommendation_text) VALUES
('RULE_USURPATION_MOMO', '(?i)(service\s*client\s*mtn|assistance\s*moov|direction\s*g[eé]n[eé]rale\s*mtn|moov\s*money\s*benin|mtn\s*momo\s*bj|agent\s*agr[eé][eé])', 'Usurpation d''opérateur', 30, 'Utilisation non vérifiée du nom d''un opérateur Mobile Money béninois.', 'Contactez directement le service client officiel de votre opérateur (ex: 111 pour MTN Bénin, 100 pour Moov Bénin) depuis votre propre téléphone pour vous assurer de la légitimité du contact.')
ON CONFLICT (rule_code) DO NOTHING;

-- 2. Insertion des scénarios locaux Afrique de l'Ouest / Bénin (scam_patterns)
INSERT INTO scam_patterns (scenario_name, country, channel, trigger_keywords, weight, engine_version) VALUES
('Faux agent Mobile Money (Annulation de transaction)', 'BJ', 'sms', ARRAY['erreur de transfert', 'annulation', 'veuillez renvoyer', 'dépôt erroné', 'code de confirmation'], 40, 'v1.0.0'),
('Faux recrutement ONG / Ambassade', 'BJ', 'whatsapp', ARRAY['recrutement urgent', 'frais médicaux', 'dépôt de dossier', 'frais d''étude', 'commission de sélection'], 35, 'v1.0.0'),
('Faux investissement à rendement rapide', 'BJ', 'whatsapp', ARRAY['multipliez votre argent', 'gagnez 50%', 'en 24 heures', 'rendement garanti', 'tontine vip'], 45, 'v1.0.0'),
('Fausse commande / Fausse livraison e-commerce', 'BJ', 'facebook', ARRAY['payez l''avance', 'frais de livraison avant départ', 'reçu mobile money falsifié', 'livreur en route'], 30, 'v1.0.0'),
('Faux don de matériel / Véhicule', 'BJ', 'facebook', ARRAY['don pour raison de santé', 'frais de transport à votre charge', 'départ à l''étranger', 'notaire en charge'], 35, 'v1.0.0'),
('Faux déblocage de compte bancaire ou compte Momo', 'BJ', 'sms', ARRAY['compte restreint', 'cliquez ici pour réactiver', 'mise à jour obligatoire', 'suspension temporaire'], 40, 'v1.0.0')
ON CONFLICT DO NOTHING;
