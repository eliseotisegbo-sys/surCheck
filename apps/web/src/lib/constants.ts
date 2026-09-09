/**
 * Constantes globales de l'application SûrCheck AI
 * Source de vérité unique pour les informations critiques
 */

/**
 * Numéros d'urgence officiels des opérateurs Mobile Money au Bénin
 * Source : Sites officiels MTN Bénin et Moov Africa Bénin
 * Dernière vérification : 2025-01-09
 */
export const OPERATOR_EMERGENCY_CONTACTS = {
  MTN: {
    number: "111",
    name: "MTN Mobile Money",
    description: "Service Client MTN - Opposition & blocage compte (gratuit 24h/7)",
  },
  MOOV: {
    number: "100",
    name: "Moov Money Bénin", 
    description: "Service Client Moov Money - Assistance & litige transfert (gratuit)",
  },
} as const;

/**
 * URL de l'application (utilisé pour les partages et liens)
 */
export const APP_NAME = "SûrCheck AI";
export const APP_URL = "https://sur-check.vercel.app";
export const APP_DESCRIPTION = "Outil citoyen d'analyse et de prévention des risques d'arnaques numériques au Bénin";
