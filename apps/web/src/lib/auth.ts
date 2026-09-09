/**
 * SûrCheck AI — Client d'authentification
 * Gère inscription, connexion, déconnexion et état de la session utilisateur.
 * Persiste le JWT dans localStorage, jamais en cookie tiers.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001/api/v1";
const TOKEN_KEY = "surcheck_access_token";
const USER_KEY = "surcheck_user_profile";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: string;
  free_quota: number;
  paid_credits: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_name: string;
  user_email: string;
  free_quota: number;
  paid_credits: number;
}

export interface AuthError {
  detail: string;
}

/** Sauvegarde le token et le profil utilisateur en localStorage. */
function persistSession(token: string, profile: UserProfile): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(profile));
  } catch {
    // Session non persistée (mode privé, etc.) — non bloquant
  }
}

/** Récupère le token JWT de la session courante. */
export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/** Récupère le profil utilisateur depuis le cache local. */
export function getCachedUser(): UserProfile | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserProfile) : null;
  } catch {
    return null;
  }
}

/** Vérifie si un utilisateur est connecté (token présent). */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/** Efface la session (déconnexion). */
export function clearSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    // Silencieux
  }
}

/** Inscrit un nouvel utilisateur. */
export async function register(
  name: string,
  email: string,
  password: string
): Promise<{ ok: true; profile: UserProfile } | { ok: false; error: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim(), email: email.trim().toLowerCase(), password }),
    });

    const data = await res.json();

    if (!res.ok) {
      return { ok: false, error: (data as AuthError).detail || "Inscription impossible. Réessayez." };
    }

    const auth = data as AuthResponse;
    const profile: UserProfile = {
      id: "",
      name: auth.user_name,
      email: auth.user_email,
      role: "user",
      free_quota: auth.free_quota,
      paid_credits: auth.paid_credits,
    };

    persistSession(auth.access_token, profile);
    return { ok: true, profile };
  } catch {
    return { ok: false, error: "Impossible de joindre le serveur. Vérifiez votre connexion." };
  }
}

/** Connecte un utilisateur existant. */
export async function login(
  email: string,
  password: string
): Promise<{ ok: true; profile: UserProfile } | { ok: false; error: string }> {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    });

    const data = await res.json();

    if (!res.ok) {
      return { ok: false, error: (data as AuthError).detail || "Identifiants incorrects." };
    }

    const auth = data as AuthResponse;
    const profile: UserProfile = {
      id: "",
      name: auth.user_name,
      email: auth.user_email,
      role: "user",
      free_quota: auth.free_quota,
      paid_credits: auth.paid_credits,
    };

    persistSession(auth.access_token, profile);
    return { ok: true, profile };
  } catch {
    return { ok: false, error: "Impossible de joindre le serveur. Vérifiez votre connexion." };
  }
}

/** Récupère le profil à jour depuis l'API (vérifie que le token est valide). */
export async function fetchMe(): Promise<UserProfile | null> {
  const token = getToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      clearSession();
      return null;
    }

    const data = await res.json();
    const profile: UserProfile = {
      id: data.id,
      name: data.name,
      email: data.email,
      role: data.role,
      free_quota: data.free_quota,
      paid_credits: data.paid_credits,
    };

    // Mise à jour du cache local
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(profile));
    } catch {
      // Silencieux
    }

    return profile;
  } catch {
    return null;
  }
}

/** Met à jour le quota et les crédits dans le cache local. */
export function updateCachedQuota(freeQuota: number, paidCredits: number): void {
  try {
    const current = getCachedUser();
    if (current) {
      current.free_quota = freeQuota;
      current.paid_credits = paidCredits;
      localStorage.setItem(USER_KEY, JSON.stringify(current));
    }
  } catch {
    // Silencieux
  }
}

