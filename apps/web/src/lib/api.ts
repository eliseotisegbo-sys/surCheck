import { AnalysisResult, analyzeContentLocally } from "./engine";
import { getToken } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

/** Construit les headers HTTP en injectant le JWT si disponible. */
function buildHeaders(extra?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...extra,
  };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/** Analyse un contenu texte ou une URL via le backend FastAPI. */
export async function checkContent(
  content: string,
  type: "text" | "url" = "text"
): Promise<AnalysisResult> {
  const endpoint =
    type === "url" ? `${API_BASE_URL}/analyze/url` : `${API_BASE_URL}/analyze/text`;
  const body = type === "url" ? { url: content } : { content };

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      throw new Error(`API returned ${res.status}`);
    }

    const data = await res.json();
    return {
      id: data.id,
      risk_score: data.risk_score,
      risk_level: data.risk_level,
      category: data.category,
      confidence_level: data.confidence_level,
      headline: data.headline,
      summary: data.summary,
      signals: data.signals,
      recommendations: data.recommendations,
      engine_version: data.engine_version,
      analyzed_at: data.created_at || new Date().toISOString(),
    };
  } catch (err) {
    console.warn(
      "Backend FastAPI non joignable, utilisation du moteur embarqué résilient:",
      err
    );
    // Fallback instantané sans friction — l'utilisateur ne voit aucune erreur
    return analyzeContentLocally(content, type);
  }
}

/** Analyse une capture d'écran via OCR backend. */
export async function checkImage(imageFile: File): Promise<AnalysisResult> {
  try {
    const formData = new FormData();
    formData.append("file", imageFile);

    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE_URL}/analyze/image`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || `API returned ${res.status}`);
    }

    const data = await res.json();
    return {
      id: data.id,
      risk_score: data.risk_score,
      risk_level: data.risk_level,
      category: data.category,
      confidence_level: data.confidence_level,
      headline: data.headline,
      summary: data.summary,
      signals: data.signals,
      recommendations: data.recommendations,
      engine_version: data.engine_version,
      analyzed_at: data.created_at || new Date().toISOString(),
    };
  } catch (err: any) {
    console.warn("Erreur OCR backend:", err);
    // Fallback : indiquer clairement que l'OCR a échoué
    throw new Error(
      err.message || "Impossible d'extraire le texte de l'image. Veuillez saisir le texte manuellement."
    );
  }
}

/** Envoie un signalement communautaire. */
export async function submitReport(payload: {
  report_type: "phone" | "url" | "sms" | "email";
  target: string;
  category: string;
  description: string;
}): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/reports`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/** Envoie un feedback sur une analyse. */
export async function sendFeedback(payload: {
  analysis_id: string;
  is_helpful: boolean;
  perceived_accuracy?: "correct" | "trop_haut" | "trop_bas";
  user_comment?: string;
}): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/analyze/feedback`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/** Récupère l'historique d'analyses du compte connecté. */
export async function fetchAnalysisHistory(): Promise<AnalysisResult[]> {
  const token = getToken();
  if (!token) return [];

  try {
    const res = await fetch(`${API_BASE_URL}/auth/analyses`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    return (await res.json()) as AnalysisResult[];
  } catch {
    return [];
  }
}

export interface CreditPack {
  id: string;
  credits: number;
  amount_fcfa: number;
  label: string;
  unit_price: number;
  popular?: boolean;
  description?: string;
}

/** Récupère la liste des packs de crédits disponibles. */
export async function fetchPacks(): Promise<CreditPack[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/payment/packs`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.packs || [];
  } catch {
    return [
      { id: "pack_1", credits: 1, amount_fcfa: 600, label: "Analyse unique", unit_price: 600, description: "1 analyse complète immédiate" },
      { id: "pack_5", credits: 5, amount_fcfa: 1500, label: "Petit pack", unit_price: 300, description: "5 analyses complètes réutilisables" },
      { id: "pack_10", credits: 10, amount_fcfa: 2500, label: "Pack recommandé", unit_price: 250, popular: true, description: "10 analyses complètes — Le plus populaire" },
      { id: "pack_25", credits: 25, amount_fcfa: 5000, label: "Gros pack", unit_price: 200, description: "25 analyses complètes" },
    ];

  }
}

/** Initie une session de paiement SasPay pour un pack. */
export async function createCheckoutSession(
  packId: string,
  analysisId?: string,
  phoneNumber?: string
): Promise<{
  step: string;
  checkout_url?: string;
  transaction_id?: string;
  message?: string;
}> {
  const token = getToken();
  if (!token) {
    throw new Error("Authentification requise pour effectuer un achat.");
  }

  const res = await fetch(`${API_BASE_URL}/payment/checkout`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({
      pack_id: packId,
      analysis_id: analysisId || null,
      phone_number: phoneNumber || null,
      country_code: "BJ",
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Erreur lors de la création de la session de paiement.");
  }
  return data;
}

/** Récupère le solde réel de crédits de l'utilisateur. */
export async function fetchCreditsBalance(): Promise<{
  credits_balance: number;
  free_quota: number;
} | null> {
  const token = getToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/credits`, {
      headers: buildHeaders(),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Récupère le journal des transactions financières de crédits. */
export async function fetchCreditTransactions(): Promise<any[]> {
  const token = getToken();
  if (!token) return [];

  try {
    const res = await fetch(`${API_BASE_URL}/credits/transactions`, {
      headers: buildHeaders(),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.transactions || [];
  } catch {
    return [];
  }
}

/** Débloque une analyse complète avec 1 crédit (atomique, idempotent). */
export async function unlockAnalysis(analysisId: string): Promise<{
  unlocked: boolean;
  message: string;
  remaining_credits: number;
}> {
  const token = getToken();
  if (!token) {
    throw new Error("Veuillez vous connecter pour débloquer cette analyse.");
  }

  const res = await fetch(`${API_BASE_URL}/analyses/${analysisId}/unlock`, {
    method: "POST",
    headers: buildHeaders(),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Impossible de débloquer l'analyse.");
  }
  return data;
}

/** Vérifie si une analyse a déjà été débloquée. */
export async function checkAnalysisUnlockStatus(analysisId: string): Promise<boolean> {
  const token = getToken();
  if (!token || !analysisId) return false;

  try {
    const res = await fetch(`${API_BASE_URL}/analyses/${analysisId}/status`, {
      headers: buildHeaders(),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return !!data.is_unlocked;
  } catch {
    return false;
  }
}

