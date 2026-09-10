/**
 * Moteur d'analyse hybride embarqué côté client pour SûrCheck AI.
 * Fournit une analyse instantanée hors-ligne et sert de fallback résilient
 * en cas de latence réseau sur mobile.
 * Conforme aux règles de neutralité de REGLES_ANTIGRAVITY_SURCHECK_AI.md
 */

export interface DetectedSignal {
  code: string;
  title: string;
  category: string;
  weight: number;
  evidence: string;
  advice: string;
}

export type RiskLevel = "faible" | "prudence" | "eleve";

export interface AnalysisResult {
  id: string;
  risk_score: number;
  risk_level: RiskLevel;
  category: string;
  confidence_level: "elevee" | "moyenne" | "incertain";
  headline: string;
  summary: string;
  signals: DetectedSignal[];
  recommendations: string[];
  engine_version: string;
  analyzed_at: string;
}

const LOCAL_RULES = [
  {
    code: "RULE_OTP_PIN",
    pattern: /(code\s*secret|code\s*otp|mot\s*de\s*passe|code\s*de\s*retrait|pin\s*moov|pin\s*mtn|votre\s*pin|mon\s*code)/i,
    category: "Sécurité des comptes",
    weight: 50,
    title: "Demande d'identifiant secret ou code de validation",
    advice: "Ne transmettez jamais votre code secret, code OTP ou mot de passe. Aucun opérateur ni banque ne vous demandera votre code de retrait.",
  },
  {
    code: "RULE_MONEY_REQ",
    pattern: /(frais\s*de\s*dossier|frais\s*d['']inscription|caution\s*exig[eé]e|frais\s*de\s*d[eé]blocage|d[eé]p[oô]t\s*pr[eé]alable|commission\s*avant|envoyez\s*(?:d['']abord|rapidement)\s*[0-9]+)/i,
    category: "Demande financière",
    weight: 40,
    title: "Exigence d'un versement d'argent préalable",
    advice: "Refusez tout envoi d'argent avant la prestation. Les recruteurs sérieux et concours officiels n'exigent pas de caution par Mobile Money.",
  },
  {
    code: "RULE_URGENCY",
    pattern: /(urgent|imm[eé]diat|dans\s*les\s*24h|imm[eé]diatement|votre\s*compte\s*sera\s*bloqu[eé]|derni[eè]re\s*chance|expire\s*aujourd['']hui|d[eé]lai\s*de\s*rigueur|sous\s*peine\s*de\s*suspension)/i,
    category: "Pression psychologique",
    weight: 30,
    title: "Pression temporelle ou urgence artificielle",
    advice: "Prenez le temps d'analyser la situation à tête reposée. L'urgence injustifiée est le levier de manipulation le plus fréquent.",
  },
  {
    code: "RULE_UNREAL_GAIN",
    pattern: /(tirage\s*au\s*sort|vous\s*avez\s*gagn[eé]|somme\s*de\s*[0-9]+(?:\s*000|\s*millions)|subvention\s*exceptionnelle|aide\s*financi[eè]re\s*accord[eé]e|b[eé]n[eé]ficiaire\s*s[eé]lectionn[eé])/i,
    category: "Promesse de gain",
    weight: 40,
    title: "Promesse de gain, loterie ou subvention sans inscription",
    advice: "Si vous n'avez pas souscrit à un concours officiel certifié, vous ne pouvez pas être gagnant. Méfiez-vous des faux tirages.",
  },
  {
    code: "RULE_SUSPICIOUS_LINK",
    pattern: /(https?:\/\/(?:bit\.ly|tinyurl\.com|is\.gd|t\.co|cutt\.ly|rb\.gy|wa\.link|goo\.su|short\.io|rebrand\.ly|lnkd\.in|s\.id|tiny\.cc)\/[a-zA-Z0-9_-]+)/i,
    category: "Lien de redirection",
    weight: 30,
    title: "Présence d'un lien raccourci masquant la destination",
    advice: "Évitez de cliquer sur les liens raccourcis envoyés par SMS ou messagerie. Les institutions officielles communiquent sur leur domaine propre.",
  },
  {
    code: "RULE_USURPATION_MOMO",
    pattern: /(service\s*client\s*mtn|assistance\s*moov|direction\s*mtn|moov\s*money\s*b[eé]nin|mtn\s*momo\s*bj|agent\s*agr[eé][eé]\s*momo)/i,
    category: "Identité d'opérateur",
    weight: 35,
    title: "Mention non authentifiée d'un opérateur Mobile Money béninois",
    advice: "Contactez directement le service officiel de votre opérateur (111 pour MTN Bénin, 100 pour Moov Bénin) depuis votre téléphone.",
  },
  {
    code: "RULE_FALSE_TRANSFER",
    pattern: /(erreur\s*de\s*transfert|veuillez\s*renvoyer|d[eé]p[oô]t\s*erron[eé]|annulation\s*de\s*la\s*transaction|fonds\s*envoy[eé]s\s*par\s*erreur)/i,
    category: "Fausse transaction",
    weight: 35,
    title: "Scénario de prétendu transfert envoyé par erreur",
    advice: "Consultez toujours votre solde réel via votre code opérateur (*880# ou *855#) sans jamais vous fier à un simple SMS entrant.",
  },
  {
    code: "RULE_PARCEL_CUSTOMS",
    pattern: /(colis|paquet|envoi|livraison|dhl|fedex|ups|chronopost).*(?:bloqu[eé]|retenu|en\s*attente|douane|d[eé]douanement|frais\s*de\s*livraison|frais\s*de\s*traitement)/i,
    category: "Arnaque colis/douane",
    weight: 40,
    title: "Arnaque au colis bloqué ou frais de douane frauduleux",
    advice: "Les vraies entreprises de livraison ne demandent jamais de paiement Mobile Money par SMS. Contactez directement le service client officiel.",
  },
  {
    code: "RULE_CRYPTO_INVESTMENT",
    pattern: /(bitcoin|crypto|cryptomonnaie|binance|forex|trading\s*automatique|plateforme\s*d['']investissement|investissement\s*garanti|rendement\s*assur[eé]|multipliez\s*vos\s*gains)/i,
    category: "Faux investissement crypto",
    weight: 38,
    title: "Promesse d'investissement crypto ou trading suspect",
    advice: "Méfiez-vous des promesses de gains rapides et garantis. Les investissements légitimes comportent toujours des risques clairement mentionnés.",
  },
  {
    code: "RULE_VISA_IMMIGRATION",
    pattern: /(visa|immigration|ambassade|consulat|green\s*card|bourse\s*[eé]tudes?|[eé]tudes?\s*[aà]\s*l[''][eé]tranger).*(?:garanti|frais|paiement|versement|caution|s[eé]lectionn[eé])/i,
    category: "Arnaque visa/immigration",
    weight: 37,
    title: "Arnaque visa, immigration ou bourse d'études",
    advice: "Les ambassades et programmes officiels ne demandent jamais de paiement Mobile Money. Vérifiez sur les sites officiels gouvernementaux.",
  },
  {
    code: "RULE_INHERITANCE_SCAM",
    pattern: /(h[eé]ritage|h[eé]ritier|notaire|testament|d[eé]c[eé]d[eé]|défunt|fonds?\s*bloqu[eé]s?|millions?\s*de\s*dollars?|banque\s*centrale|transfert\s*international)/i,
    category: "Arnaque à l'héritage",
    weight: 42,
    title: "Arnaque à l'héritage ou fonds bloqués",
    advice: "C'est une arnaque classique internationale. Aucun notaire légitime ne vous contactera par SMS pour un héritage inattendu.",
  },
  {
    code: "RULE_ROMANTIC_EMERGENCY",
    pattern: /(h[oô]pital|urgence\s*m[eé]dicale|accident|maladie\s*grave|op[eé]ration\s*chirurgicale|frais\s*m[eé]dicaux|soins\s*urgents).*(?:besoin\s*d['']aide|envoie|transfert|aide[-\s]moi)/i,
    category: "Urgence médicale suspecte",
    weight: 32,
    title: "Urgence médicale ou sentimentale suspecte",
    advice: "Avant tout transfert, appelez la personne directement pour vérifier. Les arnaqueurs ciblent les émotions en simulant des urgences.",
  },
];

export function analyzeContentLocally(content: string, type: "text" | "url" = "text"): AnalysisResult {
  const text = content.trim();
  const signals: DetectedSignal[] = [];
  let rawScore = 0;

  for (const rule of LOCAL_RULES) {
    const match = text.match(rule.pattern);
    if (match) {
      const matchIndex = match.index || 0;
      const start = Math.max(0, matchIndex - 10);
      const end = Math.min(text.length, matchIndex + match[0].length + 10);
      const snippet = text.slice(start, end).trim();

      signals.push({
        code: rule.code,
        title: rule.title,
        category: rule.category,
        weight: rule.weight,
        evidence: snippet.length < text.length ? `...${snippet}...` : snippet,
        advice: rule.advice,
      });
      rawScore += rule.weight;
    }
  }

  // Calcul du score calibré
  let finalScore = 10;
  if (signals.length > 0) {
    finalScore = Math.min(Math.max(Math.round(rawScore * 0.85), 35), 95);
    // Plancher de sécurité pour code secret ou fausse transaction
    if (signals.some((s) => s.code === "RULE_OTP_PIN" || s.code === "RULE_FALSE_TRANSFER")) {
      finalScore = Math.max(finalScore, 75);
    }
  } else {
    finalScore = 12; // Message ordinaire
  }

  let riskLevel: RiskLevel = "faible";
  let headline = "Aucun signal majeur détecté dans les éléments analysés";
  let summary =
    "L'analyse des éléments fournis n'a mis en évidence aucune demande de code, d'urgence artificielle ou de lien masqué. Restez vigilant lors de tout échange financier.";

  if (finalScore >= 70) {
    riskLevel = "eleve";
    headline = "Risque potentiel élevé détecté";
    summary =
      "Plusieurs indicateurs critiques ont été identifiés dans ce contenu. Il est fortement recommandé de ne procéder à aucun transfert d'argent et de ne communiquer aucun code secret.";
  } else if (finalScore >= 30) {
    riskLevel = "prudence";
    headline = "Plusieurs signaux nécessitent une vérification";
    summary =
      "Des éléments inhabituels ou des formulations suspectes ont été relevés. Une vérification préalable auprès de la source officielle est indispensable avant tout engagement.";
  }

  const recommendations: string[] = [];
  if (riskLevel === "eleve") {
    recommendations.push("Ne communiquez jamais votre code secret, mot de passe ou code OTP.");
    recommendations.push("N'envoyez aucun frais ni caution préalable par Mobile Money.");
    recommendations.push("En cas de doute sur un prétendu agent, appelez le numéro vert officiel de l'opérateur (111 pour MTN, 100 pour Moov).");
  } else if (riskLevel === "prudence") {
    recommendations.push("Vérifiez l'identité de l'expéditeur par un appel direct ou canal indépendant.");
    recommendations.push("Ne cliquez pas sur les liens reçus d'un numéro non enregistré.");
    recommendations.push("Si une somme d'argent vous est demandée pour un recrutement, refusez.");
  } else {
    recommendations.push("Conservez toujours vos identifiants Mobile Money confidentiels.");
    recommendations.push("Vérifiez toujours votre solde réel via votre menu officiel (*880# ou *855#).");
  }

  const category = signals.length > 0 ? signals[0].category : "Message ordinaire";

  return {
    id: `local_${Date.now()}`,
    risk_score: finalScore,
    risk_level: riskLevel,
    category,
    confidence_level: signals.length >= 2 ? "elevee" : "moyenne",
    headline,
    summary,
    signals,
    recommendations,
    engine_version: "v1.0.0",
    analyzed_at: new Date().toISOString(),
  };
}
