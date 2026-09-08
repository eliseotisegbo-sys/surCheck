"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { Shield, CheckCircle2, ArrowRight, RotateCw } from "lucide-react";
import { fetchCreditsBalance } from "@/lib/api";
import { getCachedUser, updateCachedQuota } from "@/lib/auth";

function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderRef = searchParams.get("order_ref");
  const analysisId = searchParams.get("analysis_id");

  const [balance, setBalance] = useState<number | null>(null);
  const [checking, setChecking] = useState(true);
  const [pollCount, setPollCount] = useState(0);

  useEffect(() => {
    let interval: any;

    const checkBalance = async () => {
      const data = await fetchCreditsBalance();
      if (data) {
        setBalance(data.credits_balance);
        const user = getCachedUser();
        if (user) {
          updateCachedQuota(user.free_quota, data.credits_balance);
        }
      }
      setChecking(false);
    };

    checkBalance();

    // Vérifier 5 fois toutes les 3 secondes pour détecter l'arrivée du webhook
    interval = setInterval(() => {
      setPollCount((prev) => {
        if (prev < 5) {
          checkBalance();
          return prev + 1;
        }
        clearInterval(interval);
        return prev;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 sm:p-8 space-y-6 text-center shadow-sm">
        <div className="w-12 h-12 bg-green-100 dark:bg-green-950/60 text-green-700 dark:text-green-400 rounded-full flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Paiement enregistré
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            Votre demande a été traitée par la passerelle de paiement. Vos crédits d'analyse sont activés sur votre compte dès validation automatique du réseau opérateur.
          </p>
        </div>

        {balance !== null && (
          <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold block">
              Solde de crédits confirmé
            </span>
            <span className="text-2xl font-extrabold text-blue-700 dark:text-blue-400">
              {balance} crédit{balance > 1 ? "s" : ""}
            </span>
          </div>
        )}

        <div className="space-y-2 pt-2">
          {analysisId ? (
            <Link
              href={`/?unlocked=${analysisId}`}
              className="w-full py-3 px-4 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              <span>Accéder à mon analyse complète</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <Link
              href="/"
              className="w-full py-3 px-4 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              <span>Vérifier un message suspect</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}

          <Link
            href="/paiement"
            className="w-full py-2.5 px-4 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 font-medium text-xs transition-colors block text-center"
          >
            Consulter mon portefeuille de crédits
          </Link>
        </div>

        <div className="text-[11px] text-slate-400 flex items-center justify-center gap-1.5 pt-2">
          <Shield className="w-3.5 h-3.5" />
          <span>Plateforme certifiée SûrCheck Bénin</span>
        </div>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-slate-500">Validation de votre paiement…</div>}>
      <SuccessContent />
    </Suspense>
  );
}
