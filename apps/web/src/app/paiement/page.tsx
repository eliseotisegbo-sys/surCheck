"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Shield, ArrowLeft, Check, ExternalLink, Clock, Info, AlertCircle } from "lucide-react";
import { getCachedUser, UserProfile, getToken } from "@/lib/auth";
import {
  fetchPacks,
  createCheckoutSession,
  fetchCreditsBalance,
  fetchCreditTransactions,
  CreditPack,
} from "@/lib/api";

function PaiementContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [user, setUser] = useState<UserProfile | null>(null);
  const [packs, setPacks] = useState<CreditPack[]>([]);
  const [selectedPack, setSelectedPack] = useState<string>("pack_10");
  const [phoneNumber, setPhoneNumber] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [alreadyPurchased, setAlreadyPurchased] = useState(false);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [creditsBalance, setCreditsBalance] = useState<number | null>(null);

  const preselectedPack = searchParams.get("pack");
  const analysisId = searchParams.get("analysis_id");

  useEffect(() => {
    const u = getCachedUser();
    setUser(u);

    if (preselectedPack) {
      setSelectedPack(preselectedPack);
    }

    // Charger les 4 packs
    fetchPacks().then((data) => {
      if (data && data.length > 0) {
        setPacks(data);
      }
    });

    // Charger le solde réel et l'historique si connecté
    if (getToken()) {
      fetchCreditsBalance().then((bal) => {
        if (bal) setCreditsBalance(bal.credits_balance);
      });
      fetchCreditTransactions().then((txs) => setTransactions(txs));
    }
  }, [preselectedPack]);

  const handleCheckout = async () => {
    if (!selectedPack) return;

    const token = getToken();
    if (!token) {
      router.push(`/compte?redirect=/paiement?pack=${selectedPack}`);
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    setAlreadyPurchased(false);

    try {
      const res = await createCheckoutSession(
        selectedPack,
        analysisId || undefined,
        phoneNumber.trim() || undefined
      );

      if (res.step === "already_purchased") {
        setAlreadyPurchased(true);
        return;
      }

      if (res.checkout_url) {
        // Redirection vers la page de paiement sécurisée Chariow
        window.location.href = res.checkout_url;
      } else {
        setErrorMsg("Lien de paiement indisponible. Veuillez réessayer dans quelques instants.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Erreur de connexion au serveur de paiement.");
    } finally {
      setIsLoading(false);
    }
  };

  const selectedPackData = packs.find((p) => p.id === selectedPack);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* En-tête sobre et institutionnel */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Accueil</span>
            </Link>
            <div className="h-4 w-px bg-slate-200 dark:bg-slate-800 mx-1" />
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded bg-blue-900 flex items-center justify-center text-white">
                <Shield className="w-4 h-4" />
              </div>
              <span className="font-bold tracking-tight text-slate-900 dark:text-white text-sm">
                SûrCheck<span className="text-blue-600 dark:text-blue-400">.bj</span>
              </span>
            </div>
          </div>

          {user && (
            <div className="text-xs bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium">
              Solde : <span className="font-bold text-blue-700 dark:text-blue-400">{creditsBalance !== null ? creditsBalance : user.paid_credits} crédits</span>
            </div>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-8 space-y-6">
        {/* Titre et contexte */}
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Recharger vos analyses SûrCheck
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Chaque crédit permet de débloquer une analyse complète détaillée avec recommandations concrètes et démarches d'urgence au Bénin. Vos crédits n'expirent jamais.
          </p>
        </div>

        {/* Alerte si déjà possédé (règle Chariow) */}
        {alreadyPurchased && (
          <div className="rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 p-4 space-y-2 text-amber-900 dark:text-amber-200 text-xs sm:text-sm">
            <div className="flex items-center gap-2 font-bold">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span>Commande déjà enregistrée pour ce produit</span>
            </div>
            <p>
              Votre compte a déjà finalisé une commande pour cette formule sur la passerelle. Si vos crédits ne s'affichent pas encore, veuillez patienter quelques instants le temps de la confirmation du réseau Mobile Money.
            </p>
          </div>
        )}

        {/* Sélection des 4 packs */}
        <div className="space-y-2.5">
          {packs.map((pack) => {
            const isSelected = selectedPack === pack.id;
            return (
              <button
                key={pack.id}
                id={`pack-${pack.id}`}
                type="button"
                onClick={() => setSelectedPack(pack.id)}
                className={`w-full text-left p-3.5 sm:p-4 rounded-lg border-2 transition-all cursor-pointer ${
                  isSelected
                    ? "border-blue-700 bg-blue-50/70 dark:bg-blue-950/40 dark:border-blue-500 shadow-xs"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
                        {pack.credits === 1 ? "1 analyse" : `${pack.credits} analyses`}
                      </span>
                      {pack.popular && (
                        <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded font-bold bg-blue-700 text-white">
                          Le plus populaire
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {pack.description || `${pack.unit_price} FCFA par analyse`}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className="font-extrabold text-base sm:text-lg text-slate-900 dark:text-white tracking-tight">
                      {pack.amount_fcfa.toLocaleString("fr-FR")} FCFA
                    </span>
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                        isSelected
                          ? "border-blue-700 bg-blue-700 text-white"
                          : "border-slate-300 dark:border-slate-600"
                      }`}
                    >
                      {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Champ numéro Mobile Money (optionnel pour pré-remplissage) */}
        <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
          <label className="block text-xs font-semibold text-slate-800 dark:text-slate-200">
            Numéro Mobile Money (facultatif — MTN ou Moov Bénin)
          </label>
          <input
            type="tel"
            placeholder="Ex : 97000000 ou 95000000"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            className="w-full p-2.5 text-sm rounded border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-600 focus:outline-none"
          />
          <p className="text-[11px] text-slate-500">
            Ce numéro servira uniquement à pré-renseigner la page de paiement sécurisée.
          </p>
        </div>

        {/* Message d'erreur éventuel */}
        {errorMsg && (
          <div className="rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 p-3 text-xs text-red-700 dark:text-red-300">
            {errorMsg}
          </div>
        )}

        {/* Invitation à se connecter si invité */}
        {!user && (
          <div className="rounded-lg bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 p-3.5 text-xs text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>Un compte est requis pour rattacher vos crédits achetés.</span>
            <Link
              href="/compte"
              className="font-semibold underline text-blue-700 dark:text-blue-400 shrink-0 ml-2"
            >
              Se connecter
            </Link>
          </div>
        )}

        {/* Bouton d'action principal */}
        <button
          id="checkout-btn"
          type="button"
          onClick={handleCheckout}
          disabled={isLoading || !selectedPack || !user}
          className="w-full py-3.5 px-4 rounded-lg bg-blue-700 hover:bg-blue-800 disabled:opacity-50 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
        >
          {isLoading ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Génération de la session de paiement sécurisée…</span>
            </>
          ) : selectedPackData ? (
            <>
              <span>Continuer vers le paiement ({selectedPackData.amount_fcfa.toLocaleString("fr-FR")} FCFA)</span>
              <ExternalLink className="w-4 h-4" />
            </>
          ) : (
            "Sélectionner un pack"
          )}
        </button>

        {/* Note de conformité & sécurité */}
        <div className="pt-2 text-center text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
          <p>
            Paiement certifié via la passerelle Chariow. Compatible MTN Mobile Money, Moov Money Bénin et cartes bancaires.
          </p>
          <p>
            Crédits attachés définitivement à votre compte, sans limitation de durée.
          </p>
        </div>

        {/* Historique des opérations si utilisateur connecté */}
        {transactions && transactions.length > 0 && (
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800 space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              <span>Historique récent de vos crédits</span>
            </h2>
            <div className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden">
              {transactions.slice(0, 5).map((tx) => (
                <div key={tx.id} className="p-3 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">
                      {tx.description || (tx.type === "purchase" ? "Achat de crédits" : "Consommation analyse")}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {new Date(tx.created_at).toLocaleDateString("fr-FR", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                  <div
                    className={`font-bold text-sm ${
                      tx.amount > 0 ? "text-green-600 dark:text-green-400" : "text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {tx.amount > 0 ? `+${tx.amount}` : tx.amount} crédit{Math.abs(tx.amount) > 1 ? "s" : ""}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function PaiementPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Chargement de la page de paiement…</div>}>
      <PaiementContent />
    </Suspense>
  );
}
