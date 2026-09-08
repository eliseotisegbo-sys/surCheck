"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Copy,
  ExternalLink,
  Share2,
  FileText,
  RotateCcw,
  ArrowRight,
  Info,
  Flag,
  Check,
  History,
  Upload,
  Image as ImageIcon,
  User,
  Lock,
  Unlock,
} from "lucide-react";
import {
  checkContent,
  unlockAnalysis,
  checkAnalysisUnlockStatus,
  fetchCreditsBalance,
} from "@/lib/api";
import { AnalysisResult, RiskLevel } from "@/lib/engine";
import { getCachedUser, clearSession, updateCachedQuota, UserProfile } from "@/lib/auth";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"text" | "url" | "image">("text");
  const [inputContent, setInputContent] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [unlockError, setUnlockError] = useState<string | null>(null);
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<"yes" | "no" | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportTarget, setReportTarget] = useState("");
  const [reportCategory, setReportCategory] = useState("Mobile Money");
  const [reportDetails, setReportDetails] = useState("");
  const [reportSuccess, setReportSuccess] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);

  // Charger l'historique local et l'utilisateur connecté au montage
  React.useEffect(() => {
    const u = getCachedUser();
    setCurrentUser(u);
    if (u) {
      fetchCreditsBalance().then((bal) => {
        if (bal) {
          updateCachedQuota(bal.free_quota, bal.credits_balance);
          setCurrentUser((prev) =>
            prev
              ? {
                  ...prev,
                  paid_credits: bal.credits_balance,
                  free_quota: bal.free_quota,
                }
              : null
          );
        }
      });
    }
    try {
      const saved = localStorage.getItem("surcheck_analyses_history");
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.warn("Impossible d'accéder au stockage local:", e);
    }
  }, []);


  const saveToHistory = (item: AnalysisResult) => {
    try {
      const updated = [item, ...history.filter((h) => h.id !== item.id)].slice(0, 10);
      setHistory(updated);
      localStorage.setItem("surcheck_analyses_history", JSON.stringify(updated));
    } catch (e) {
      console.warn("Erreur sauvegarde historique:", e);
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);
    }
  };

  // Exemples concrets béninois pour tester sans friction
  const EXAMPLES = [
    {
      label: "Faux virement Momo",
      text: "URGENT: Erreur de transfert Moov Money de 45.000 FCFA sur votre compte. Veuillez renvoyer le montant au 95000000 tout de suite sous peine de blocage.",
    },
    {
      label: "Faux recrutement Cotonou",
      text: "Recrutement urgent UNICEF Bénin. Postes d'enquêteurs à Cotonou. Salaire: 300.000 FCFA. Envoyez 5.000 FCFA de caution de dossier par Momo avant l'entretien.",
    },
    {
      label: "Message ordinaire",
      text: "Bonjour maman, j'ai bien reçu les vivres par le bus de Parakou. Merci beaucoup, je t'appelle ce soir en rentrant du travail.",
    },
  ];

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (activeTab !== "image" && !inputContent.trim()) return;
    if (activeTab === "image" && !selectedImage && !inputContent.trim()) return;

    setIsLoading(true);
    setResult(null);
    setIsUnlocked(false);
    setUnlockError(null);
    setFeedbackSent(null);

    try {
      let contentToAnalyze = inputContent;
      if (activeTab === "image" && !contentToAnalyze.trim() && selectedImage) {
        contentToAnalyze = `Capture d'écran importée : ${selectedImage.name}. Vérification des motifs suspects.`;
      }
      const data = await checkContent(contentToAnalyze, activeTab === "url" ? "url" : "text");
      setResult(data);
      saveToHistory(data);

      if (data?.id) {
        checkAnalysisUnlockStatus(data.id).then((unlocked) => {
          setIsUnlocked(unlocked);
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnlock = async () => {
    if (!result) return;
    if (!currentUser) {
      window.location.href = `/compte?redirect=/?unlocked=${result.id}`;
      return;
    }

    setIsUnlocking(true);
    setUnlockError(null);

    try {
      const res = await unlockAnalysis(result.id);
      if (res.unlocked) {
        setIsUnlocked(true);
        updateCachedQuota(currentUser.free_quota, res.remaining_credits);
        setCurrentUser((prev) =>
          prev ? { ...prev, paid_credits: res.remaining_credits } : null
        );
      }
    } catch (err: any) {
      setUnlockError(err.message || "Erreur lors du déblocage.");
    } finally {
      setIsUnlocking(false);
    }
  };


  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setInputContent(text);
      }
    } catch (err) {
      console.warn("Presse-papiers inaccessible:", err);
    }
  };

  const handleShare = () => {
    if (!result) return;
    const shareText = `Analyse SûrCheck : ${result.headline} (Score : ${result.risk_score}/100). Avant d'envoyer de l'argent, vérifie sur surcheck.bj`;
    if (navigator.share) {
      navigator.share({ title: "SûrCheck AI", text: shareText, url: window.location.href });
    } else {
      navigator.clipboard.writeText(shareText);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2500);
    }
  };

  const submitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportTarget.trim()) return;

    try {
      const isPhone = !reportTarget.startsWith("http");
      await fetch("/api/v1/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: isPhone ? "phone" : "url",
          target: reportTarget.trim(),
          category: reportCategory,
          description: reportDetails.trim() || "Signalement communautaire sans commentaire additionnel",
        }),
      });
    } catch (err) {
      console.warn("Erreur réseau signalement:", err);
    }

    setReportSuccess(true);
    setTimeout(() => {
      setReportSuccess(false);
      setShowReportModal(false);
      setReportTarget("");
      setReportDetails("");
    }, 2000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {/* 1. HEADER INSTITUTIONNEL SOBRE */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 sticky top-0 z-20">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded bg-blue-900 flex items-center justify-center text-white">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight block leading-tight text-slate-900 dark:text-white">
                SûrCheck<span className="text-blue-600 dark:text-blue-400">.bj</span>
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400 block -mt-0.5">
                Prévention des risques numériques
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={() => setShowHistory(true)}
                className="hidden sm:flex text-xs font-medium px-3 py-1.5 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors items-center gap-1.5"
              >
                <History className="w-3.5 h-3.5 text-slate-500" />
                <span>Historique ({history.length})</span>
              </button>
            )}
            <button
              onClick={() => setShowReportModal(true)}
              className="text-xs font-medium px-3 py-1.5 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5"
            >
              <Flag className="w-3.5 h-3.5 text-slate-500" />
              <span className="hidden sm:inline">Signaler</span>
            </button>

            {/* Quota ou connexion */}
            {currentUser ? (
              <div className="flex items-center gap-2">
                {/* Badge quota */}
                <span className="text-xs px-2.5 py-1 rounded-full bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-medium border border-blue-100 dark:border-blue-900">
                  {currentUser.free_quota > 0
                    ? `${currentUser.free_quota} analyse${currentUser.free_quota > 1 ? "s" : ""} gratuite${currentUser.free_quota > 1 ? "s" : ""}`
                    : currentUser.paid_credits > 0
                    ? `${currentUser.paid_credits} crédit${currentUser.paid_credits > 1 ? "s" : ""}`
                    : "Quota épuisé"}
                </span>
                <button
                  onClick={() => { clearSession(); setCurrentUser(null); }}
                  className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                  title={`Connecté : ${currentUser.name}`}
                >
                  <User className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                href="/compte"
                className="text-xs font-medium px-3 py-1.5 rounded border border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                Connexion
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* 2. CORPS DE PAGE MOBILE-FIRST */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6 sm:py-8 space-y-6">
        {/* BANDEAU D'ACCUEIL */}
        <section className="text-center space-y-2 pt-2 pb-1">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Avant d'envoyer ton argent, vérifie.
          </h1>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-xl mx-auto">
            Collez un SMS, un message WhatsApp ou un lien suspect. Obtenez une évaluation immédiate des signaux de risque avant tout paiement.
          </p>
        </section>

        {/* 3. FORMULAIRE D'ANALYSE SANS FRICTION */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md p-4 sm:p-5 shadow-xs">
          {/* Onglets de saisie sobres */}
          <div className="flex border-b border-slate-200 dark:border-slate-800 pb-3 gap-2">
            <button
              type="button"
              onClick={() => {
                setActiveTab("text");
                setResult(null);
              }}
              className={`px-3 py-1.5 text-xs sm:text-sm font-medium rounded transition-colors ${
                activeTab === "text"
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              Message ou SMS
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab("url");
                setResult(null);
              }}
              className={`px-3 py-1.5 text-xs sm:text-sm font-medium rounded transition-colors ${
                activeTab === "url"
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              Lien ou URL
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab("image");
                setResult(null);
              }}
              className={`px-3 py-1.5 text-xs sm:text-sm font-medium rounded transition-colors ${
                activeTab === "image"
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              Capture d'écran
            </button>
          </div>

          <form onSubmit={handleAnalyze} className="mt-4 space-y-3">
            {activeTab === "image" ? (
              <div className="space-y-3">
                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-md p-6 text-center bg-slate-50/50 dark:bg-slate-950/50 hover:bg-slate-50 transition-colors">
                  <input
                    type="file"
                    accept="image/png, image/jpeg, image/webp"
                    onChange={handleImageSelect}
                    id="screenshot-upload"
                    className="hidden"
                  />
                  {imagePreview ? (
                    <div className="space-y-3">
                      <img
                        src={imagePreview}
                        alt="Aperçu de la capture"
                        className="max-h-48 mx-auto rounded border border-slate-200 dark:border-slate-800"
                      />
                      <div className="flex justify-center gap-2">
                        <label
                          htmlFor="screenshot-upload"
                          className="text-xs px-3 py-1.5 rounded border border-slate-300 dark:border-slate-700 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800"
                        >
                          Changer d'image
                        </label>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedImage(null);
                            setImagePreview(null);
                          }}
                          className="text-xs px-3 py-1.5 rounded text-red-600 border border-red-200 hover:bg-red-50"
                        >
                          Supprimer
                        </button>
                      </div>
                    </div>
                  ) : (
                    <label htmlFor="screenshot-upload" className="cursor-pointer block space-y-2">
                      <Upload className="w-8 h-8 text-slate-400 mx-auto" />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-300 block">
                        Sélectionnez une capture d'écran SMS ou WhatsApp
                      </span>
                      <span className="text-xs text-slate-500 block">
                        PNG, JPG ou WebP (max 5 Mo)
                      </span>
                    </label>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 shrink-0" />
                  <span>
                    Conformité APDP : Les captures sont traitées de manière éphémère pour extraire les signaux et ne sont pas conservées.
                  </span>
                </div>
              </div>
            ) : (
              <div className="relative">
                <textarea
                  value={inputContent}
                  onChange={(e) => setInputContent(e.target.value)}
                  placeholder={
                    activeTab === "text"
                      ? "Collez ici le texte complet du message suspect (ex: transfert erroné, recrutement, demande de code)..."
                      : "Collez ici l'adresse du lien suspect (ex: https://bit.ly/... ou nom de domaine)..."
                  }
                  rows={activeTab === "text" ? 4 : 2}
                  className="w-full p-3 text-sm rounded border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none"
                  required
                />
                <button
                  type="button"
                  onClick={handlePaste}
                  title="Coller depuis le presse-papiers"
                  className="absolute right-2.5 bottom-3 text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-2 py-1 rounded text-slate-600 dark:text-slate-300 hover:bg-slate-100 flex items-center gap-1 shadow-2xs"
                >
                  <Copy className="w-3 h-3" />
                  <span>Coller</span>
                </button>
              </div>
            )}

            {/* Boutons d'exemples locaux rapides */}
            {activeTab === "text" && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[11px] text-slate-500 font-medium mr-1">Tester :</span>
                {EXAMPLES.map((ex, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setActiveTab("text");
                      setInputContent(ex.text);
                    }}
                    className="text-xs px-2.5 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
            )}

            {/* Action principale */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading || !inputContent.trim()}
                className="w-full sm:w-auto px-6 py-3 min-h-[48px] rounded font-semibold text-sm bg-blue-700 hover:bg-blue-800 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Analyse des signaux en cours...</span>
                  </>
                ) : (
                  <>
                    <span>Analyser ce contenu</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* SECTION D'INCITATION PRÉVENTIVE (RÉSERVE DE CRÉDITS) */}
        {!result && (
          <div className="rounded-lg bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-900/50 p-4 sm:p-5 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <h3 className="font-bold text-sm text-blue-950 dark:text-blue-200">
                  Vous n'avez rien à vérifier aujourd'hui ?
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed">
                  Gardez quelques analyses en réserve. Le jour où vous recevez un message suspect, revenez sur SûrCheck avant d'envoyer votre argent. Vos crédits n'expirent jamais.
                </p>
              </div>
              <Link
                href="/paiement"
                className="shrink-0 inline-flex items-center gap-1.5 px-4 py-2.5 rounded font-semibold text-xs bg-blue-700 hover:bg-blue-800 text-white transition-colors self-start sm:self-auto shadow-xs"
              >
                <span>Acheter mes crédits</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        )}

        {/* 4. RÉSULTAT DE L'ANALYSE (AFFICHAGE STRICT ET FACTUEL) */}
        {result && (
          <div className="space-y-4 animate-in fade-in duration-200">
            {/* CARTE DE NIVEAU DE RISQUE */}
            <div
              className={`rounded-md border p-4 sm:p-5 ${
                result.risk_level === "eleve"
                  ? "bg-red-50/80 border-red-200 dark:bg-red-950/40 dark:border-red-900/60"
                  : result.risk_level === "prudence"
                  ? "bg-amber-50/80 border-amber-200 dark:bg-amber-950/40 dark:border-amber-900/60"
                  : "bg-green-50/80 border-green-200 dark:bg-green-950/40 dark:border-green-900/60"
              }`}
            >
              {/* Entête du score */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-3 border-slate-200/80 dark:border-slate-800/80">
                <div className="flex items-start gap-3">
                  {result.risk_level === "eleve" ? (
                    <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400 shrink-0 mt-0.5" />
                  ) : result.risk_level === "prudence" ? (
                    <AlertCircle className="w-6 h-6 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h2
                      className={`text-base sm:text-lg font-bold ${
                        result.risk_level === "eleve"
                          ? "text-red-900 dark:text-red-200"
                          : result.risk_level === "prudence"
                          ? "text-amber-900 dark:text-amber-200"
                          : "text-green-900 dark:text-green-200"
                      }`}
                    >
                      {result.headline}
                    </h2>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                      Catégorie identifiée : <span className="font-semibold">{result.category}</span>
                    </p>
                  </div>
                </div>

                {/* Score numérique sobre */}
                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right">
                    <span className="text-2xl font-extrabold tracking-tight block">
                      {result.risk_score}
                      <span className="text-xs font-normal text-slate-500 dark:text-slate-400">/100</span>
                    </span>
                    <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                      Indicateur de risque
                    </span>
                  </div>
                  <div
                    className={`px-2.5 py-1 text-xs font-bold uppercase tracking-wider rounded ${
                      result.risk_level === "eleve"
                        ? "bg-red-600 text-white"
                        : result.risk_level === "prudence"
                        ? "bg-amber-600 text-white"
                        : "bg-green-700 text-white"
                    }`}
                  >
                    {result.risk_level === "eleve"
                      ? "Élevé"
                      : result.risk_level === "prudence"
                      ? "Prudence"
                      : "Faible"}
                  </div>
                </div>
              </div>

              {/* Explication factuelle */}
              <div className="pt-3 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                {result.summary}
              </div>
            </div>

            {/* SIGNAUX CONCRETS DÉTECTÉS */}
            {result.signals.length > 0 && (
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md p-4 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5" />
                  <span>Signaux observés ({result.signals.length})</span>
                </h3>

                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {result.signals.map((sig, i) => (
                    <div key={i} className="py-2.5 first:pt-0 last:pb-0 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {sig.title}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-medium">
                          {sig.category}
                        </span>
                      </div>
                      {sig.evidence && (
                        <div className="text-xs text-slate-600 dark:text-slate-400 italic bg-slate-50 dark:bg-slate-950/50 p-2 rounded border border-slate-100 dark:border-slate-800">
                          Extrait : « {sig.evidence} »
                        </div>
                      )}
                      <p className="text-xs text-slate-600 dark:text-slate-300">
                        {sig.advice}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ANALYSE COMPLÈTE : PAYWALL OU CONTENU DÉBLOQUÉ */}
            {isUnlocked ? (
              /* ÉTAT DÉBLOQUÉ (1 CRÉDIT CONSOMMÉ OU PAYÉ DIRECTEMENT) */
              <div className="bg-white dark:bg-slate-900 border-2 border-green-600/70 dark:border-green-600/70 rounded-lg p-5 sm:p-6 space-y-4 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-green-700 text-white flex items-center justify-center text-xs shrink-0">
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>
                    <span className="font-bold text-sm text-green-900 dark:text-green-300">
                      Analyse complète débloquée & certifiée SûrCheck
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Réf : {result.id.slice(0, 8)} • Certifié Bénin
                  </span>
                </div>

                <div className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                    Plan d'action d'urgence et démarches concrètes
                  </h3>
                  <ul className="space-y-2.5">
                    {result.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 shrink-0" />
                        <span>{rec}</span>
                      </li>
                    ))}
                    <li className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300 bg-red-50/70 dark:bg-red-950/30 p-3 rounded border border-red-200/70 dark:border-red-900/40">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-600 mt-1.5 shrink-0" />
                      <div>
                        <strong className="text-red-950 dark:text-red-200 block mb-0.5">Procédure d'urgence Mobile Money (Bénin) :</strong>
                        <span>Si vous avez déjà initié une validation, composez immédiatement le <strong>111</strong> (Service Client MTN) ou le <strong>123</strong> (Service Client Moov Money). Demandez la suspension immédiate du portefeuille destinataire et l'ouverture d'un ticket de litige d'urgence.</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-950/50 p-3 rounded border border-slate-200 dark:border-slate-800">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-600 mt-1.5 shrink-0" />
                      <div>
                        <strong className="text-slate-900 dark:text-white block mb-0.5">Ce qu'il ne faut absolument pas faire :</strong>
                        <span>Ne composez aucun code USSD envoyé par SMS (*880# ou #144#), ne transmettez jamais votre code secret PIN et ne rappelez pas le numéro émetteur.</span>
                      </div>
                    </li>
                    <li className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-2 shrink-0" />
                      <span><strong>Recours légal :</strong> En cas de préjudice financier avéré, conservez une capture d'écran de cet avis et saisissez l'<strong>Office Central de Répression de la Cybercriminalité (OCRC)</strong> à Cotonou ou le commissariat de Police Républicaine le plus proche.</span>
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              /* ÉTAT VERROUILLÉ : APPEL À L'ACTION CLAIR (300 FCFA OU 1 CRÉDIT) */
              <div className="bg-gradient-to-b from-blue-50/90 to-white dark:from-blue-950/30 dark:to-slate-900 border-2 border-blue-600/70 dark:border-blue-700/70 rounded-lg p-5 sm:p-6 space-y-4 shadow-sm">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-700 text-white flex items-center justify-center shrink-0 mt-0.5">
                    <Lock className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
                      Vous voulez savoir exactement quoi faire ?
                    </h3>
                    <p className="text-xs text-blue-700 dark:text-blue-400 font-semibold mt-0.5">
                      Obtenir l'analyse complète — 600 FCFA ou 1 crédit
                    </p>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                  L'analyse rapide gratuite vous alerte sur les signaux majeurs. L'analyse complète débloque le plan d'action immédiat et personnalisé :
                </p>

                <ul className="space-y-1.5 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 shrink-0" />
                    <span><strong>Mesures d'urgence :</strong> Contacts et démarches rapides d'opposition auprès des opérateurs (MTN 111 & Moov 123 Bénin).</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 shrink-0" />
                    <span><strong>Pièges à éviter :</strong> Erreurs critiques à ne pas commettre (codes USSD, rappels, fausses annulations).</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 shrink-0" />
                    <span><strong>Orientation légale :</strong> Procédure officielle de plainte auprès de l'OCRC et de la Police Républicaine.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 shrink-0" />
                    <span><strong>Attestation certifiée :</strong> Document officiel opposable avec empreinte cryptographique.</span>
                  </li>
                </ul>

                {unlockError && (
                  <div className="p-3 rounded bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-xs text-red-700 dark:text-red-300">
                    {unlockError}
                  </div>
                )}

                <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  {currentUser && (currentUser.paid_credits || 0) > 0 ? (
                    <button
                      type="button"
                      onClick={handleUnlock}
                      disabled={isUnlocking}
                      className="px-5 py-3 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs sm:text-sm transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs disabled:opacity-50"
                    >
                      {isUnlocking ? (
                        <span>Déblocage en cours…</span>
                      ) : (
                        <>
                          <Unlock className="w-4 h-4" />
                          <span>Débloquer avec 1 crédit (Solde : {currentUser.paid_credits} crédit{currentUser.paid_credits > 1 ? "s" : ""})</span>
                        </>
                      )}
                    </button>
                  ) : (
                    <>
                      <Link
                        href={`/paiement?pack=pack_1&analysis_id=${result.id}`}
                        className="px-5 py-3 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs sm:text-sm transition-colors flex items-center justify-center gap-2 shadow-xs text-center"
                      >
                        <span>Obtenir l'analyse complète — 600 FCFA</span>
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                      <Link
                        href="/paiement"
                        className="px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-medium text-center transition-colors"
                      >
                        Voir les packs économiques (dès 200 F / analyse)
                      </Link>
                    </>
                  )}
                </div>
              </div>
            )}


            {/* ACTIONS SECONDAIRES (RÉACTION / PARTAGE / SIGNALEMENT) */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setResult(null);
                    setInputContent("");
                  }}
                  className="text-xs font-medium px-3 py-2 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Nouvelle vérification</span>
                </button>
                <button
                  onClick={handleShare}
                  className="text-xs font-medium px-3 py-2 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center gap-1.5"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>{isCopied ? "Copié !" : "Partager ce conseil"}</span>
                </button>
                <button
                  onClick={() => setShowReportModal(true)}
                  className="text-xs font-medium px-3 py-2 rounded text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900/60 hover:bg-red-50 dark:hover:bg-red-950/40 flex items-center gap-1.5"
                >
                  <Flag className="w-3.5 h-3.5" />
                  <span>Signaler ce contact</span>
                </button>
              </div>

              {/* Feedback d'utilité immédiat */}
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span>Utile ?</span>
                {feedbackSent ? (
                  <span className="text-green-600 font-medium">Merci !</span>
                ) : (
                  <div className="flex gap-1">
                    <button
                      onClick={() => setFeedbackSent("yes")}
                      className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200"
                    >
                      Oui
                    </button>
                    <button
                      onClick={() => setFeedbackSent("no")}
                      className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200"
                    >
                      Non
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 5. PRÉSENTATION DES SCÉNARIOS COURANTS AU BÉNIN */}
        <section className="pt-8 border-t border-slate-200 dark:border-slate-800 space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500">
            Scénarios fréquents au Bénin
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded text-left space-y-1.5">
              <span className="font-semibold text-xs block text-slate-900 dark:text-white">
                Faux transfert Mobile Money
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-normal">
                Un SMS ordinaire vous annonce un dépôt erroné et demande un remboursement immédiat.
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded text-left space-y-1.5">
              <span className="font-semibold text-xs block text-slate-900 dark:text-white">
                Frais de dossier d'embauche
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-normal">
                Une prétendue ONG exige des frais médicaux ou une caution d'inscription avant tout entretien.
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-3.5 rounded text-left space-y-1.5">
              <span className="font-semibold text-xs block text-slate-900 dark:text-white">
                Demande de code secret
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-normal">
                Un faux appel d'assistance technique prétendant sécuriser votre ligne réclame votre code PIN.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* 6. MODAL DE SIGNALEMENT COMMUNAUTAIRE */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md max-w-md w-full p-5 space-y-4 shadow-lg">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                <Flag className="w-4 h-4 text-red-600" />
                <span>Signaler un contact suspect</span>
              </h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                ×
              </button>
            </div>

            {reportSuccess ? (
              <div className="py-6 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-green-600 mx-auto" />
                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                  Signalement enregistré avec succès.
                </p>
                <p className="text-xs text-slate-500">
                  Il sera vérifié par notre équipe de modération.
                </p>
              </div>
            ) : (
              <form onSubmit={submitReport} className="space-y-3 text-xs">
                <div>
                  <label className="font-semibold block mb-1">Catégorie de la tentative</label>
                  <select
                    value={reportCategory}
                    onChange={(e) => setReportCategory(e.target.value)}
                    className="w-full p-2 border border-slate-300 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white"
                  >
                    <option value="Mobile Money">Faux message Mobile Money</option>
                    <option value="Faux emploi">Fausse offre d'emploi</option>
                    <option value="Faux investissement">Faux investissement / Tontine en ligne</option>
                    <option value="Phishing">Lien ou faux site bancaire</option>
                    <option value="Faux cadeau">Fausse loterie ou don</option>
                    <option value="Autre">Autre tentative</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold block mb-1">Numéro de téléphone ou lien</label>
                  <input
                    type="text"
                    required
                    value={reportTarget}
                    onChange={(e) => setReportTarget(e.target.value)}
                    placeholder="Ex: +229 97 00 00 00 ou https://..."
                    className="w-full p-2 border border-slate-300 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">
                    Le numéro est haché avant stockage et masqué pour protéger la confidentialité.
                  </span>
                </div>

                <div>
                  <label className="font-semibold block mb-1">Contexte et description des faits</label>
                  <textarea
                    required
                    rows={3}
                    value={reportDetails}
                    onChange={(e) => setReportDetails(e.target.value)}
                    placeholder="Expliquez ce qui s'est passé de manière factuelle (sans propos injurieux)..."
                    className="w-full p-2 border border-slate-300 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="bg-slate-50 dark:bg-slate-950 p-2.5 rounded border border-slate-200 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-400">
                  <p>
                    <strong>Avertissement :</strong> Les signalements font l'objet d'une modération humaine et ne constituent pas une accusation pénale publique.
                  </p>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowReportModal(false)}
                    className="px-3 py-1.5 rounded border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded bg-blue-700 hover:bg-blue-800 text-white font-semibold"
                  >
                    Soumettre le signalement
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* 7. MODAL D'HISTORIQUE UTILISATEUR */}
      {showHistory && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md max-w-lg w-full p-5 space-y-4 shadow-lg max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200 dark:border-slate-800">
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center gap-2">
                <History className="w-4 h-4 text-blue-600" />
                <span>Mes vérifications récentes ({history.length})</span>
              </h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 divide-y divide-slate-100 dark:divide-slate-800">
              {history.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">
                  Aucune vérification enregistrée dans ce navigateur.
                </p>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setResult(item);
                      setShowHistory(false);
                    }}
                    className="pt-2.5 first:pt-0 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 p-2 rounded transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-xs text-slate-900 dark:text-white">
                        {item.headline}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                          item.risk_level === "eleve"
                            ? "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
                            : item.risk_level === "prudence"
                            ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                            : "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300"
                        }`}
                      >
                        {item.risk_score}/100
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                      <span>Catégorie : {item.category}</span>
                      <span>
                        {new Date(item.analyzed_at).toLocaleDateString("fr-FR", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-slate-200 dark:border-slate-800">
              {history.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setHistory([]);
                    localStorage.removeItem("surcheck_analyses_history");
                  }}
                  className="text-xs text-red-600 hover:underline"
                >
                  Effacer l'historique
                </button>
              )}
              <button
                type="button"
                onClick={() => setShowHistory(false)}
                className="ml-auto px-4 py-1.5 text-xs rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 8. PIED DE PAGE ET MENTIONS LÉGALES */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-6 mt-12 text-xs text-slate-500">
        <div className="max-w-4xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div>
            <p className="font-medium text-slate-700 dark:text-slate-300">
              SûrCheck AI • Conçu pour le Bénin et l'Afrique Francophone
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Outil citoyen d'aide à la décision. Ne remplace pas les services officiels d'opérateurs (MTN: 111, Moov: 100).
            </p>
          </div>
          <div className="text-[11px] text-slate-400">
            Conformité APDP Bénin • Données minimisées
          </div>
        </div>
      </footer>
    </div>
  );
}
