/**
 * Source unique de vérité pour les contacts opérateurs Mobile Money au Bénin.
 * 
 * Tous les numéros d'urgence, de blocage et d'assistance doivent être
 * référencés depuis ce fichier unique.
 * 
 * ⚠️ IMPORTANT : Vérifier manuellement chaque numéro auprès des opérateurs
 * avant publication. Les numéros peuvent changer sans préavis.
 * 
 * Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 4.2
 */

export const OPERATOR_CONTACTS = {
  mtn_bj: {
    name: "MTN Bénin",
    shortCode: "111",
    fullNumber: "+229 111",
    description: "Opposition et blocage compte Mobile Money",
    services: [
      "Opposition carte SIM volée/perdue",
      "Blocage compte Mobile Money",
      "Signalement transaction frauduleuse",
      "Assistance technique 24/7",
    ],
    hours: "24h/24, 7j/7",
    cost: "Gratuit depuis MTN",
  },
  
  moov_bj: {
    name: "Moov Money Bénin",
    shortCode: "100",
    fullNumber: "+229 100",
    description: "Assistance et litige transfert Mobile Money",
    services: [
      "Blocage compte Moov Money",
      "Contestation transaction",
      "Réclamation transfert",
      "Support technique",
    ],
    hours: "24h/24, 7j/7",
    cost: "Gratuit depuis Moov",
  },
  
  ocrc: {
    name: "OCRC — Police Cybercriminalité Cotonou",
    shortCode: null,
    fullNumber: "+229 21 30 08 62",
    description: "Office Central de Répression de la Cybercriminalité",
    services: [
      "Dépôt de plainte arnaque en ligne",
      "Signalement fraude Mobile Money",
      "Escroquerie par SMS/WhatsApp",
      "Usurpation d'identité numérique",
    ],
    hours: "Lundi-Vendredi 8h-18h",
    cost: "Tarif appel national",
    address: "Cotonou, Bénin",
    email: "ocrc@interieur.bj",
  },
  
  police_secours: {
    name: "Police Secours",
    shortCode: "117",
    fullNumber: "+229 117",
    description: "Urgences policières nationales",
    services: [
      "Signalement urgence",
      "Demande d'intervention",
    ],
    hours: "24h/24, 7j/7",
    cost: "Gratuit",
  },
} as const;


export type OperatorId = keyof typeof OPERATOR_CONTACTS;


/**
 * Retourne les informations de contact d'un opérateur.
 */
export function getOperatorContact(operatorId: OperatorId) {
  return OPERATOR_CONTACTS[operatorId];
}


/**
 * Retourne tous les contacts d'urgence Mobile Money (MTN + Moov).
 */
export function getMobileMoneyEmergencyContacts() {
  return [
    OPERATOR_CONTACTS.mtn_bj,
    OPERATOR_CONTACTS.moov_bj,
  ];
}


/**
 * Retourne tous les contacts d'autorités (Police, OCRC).
 */
export function getAuthorityContacts() {
  return [
    OPERATOR_CONTACTS.ocrc,
    OPERATOR_CONTACTS.police_secours,
  ];
}


/**
 * Formate un numéro de téléphone pour affichage.
 */
export function formatPhoneNumber(operator: typeof OPERATOR_CONTACTS[OperatorId]): string {
  if (operator.shortCode) {
    return `${operator.shortCode} (${operator.fullNumber})`;
  }
  return operator.fullNumber;
}


/**
 * Génère un lien tel: pour appel direct.
 */
export function getCallLink(operatorId: OperatorId): string {
  const operator = OPERATOR_CONTACTS[operatorId];
  const number = operator.shortCode || operator.fullNumber.replace(/\s+/g, "");
  return `tel:${number}`;
}


/**
 * Retourne une recommandation d'action selon le type de fraude.
 */
export function getRecommendedContact(fraudType: "mobile_money" | "cybercrime" | "emergency"): OperatorId {
  switch (fraudType) {
    case "mobile_money":
      return "mtn_bj"; // Par défaut MTN (plus commun)
    case "cybercrime":
      return "ocrc";
    case "emergency":
      return "police_secours";
    default:
      return "ocrc";
  }
}
