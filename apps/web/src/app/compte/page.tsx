"use client";

import React, { useState } from "react";
import { Shield, Eye, EyeOff, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/auth";

type Mode = "connexion" | "inscription";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("connexion");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!email.trim() || !password.trim()) {
      setErrorMsg("Veuillez remplir tous les champs obligatoires.");
      return;
    }
    if (mode === "inscription" && !name.trim()) {
      setErrorMsg("Le nom complet est requis pour créer un compte.");
      return;
    }
    if (password.length < 8) {
      setErrorMsg("Le mot de passe doit comporter au moins 8 caractères.");
      return;
    }

    setIsLoading(true);

    try {
      if (mode === "connexion") {
        const result = await login(email, password);
        if (!result.ok) {
          setErrorMsg(result.error);
        } else {
          setSuccessMsg("Connexion réussie. Redirection…");
          setTimeout(() => router.push("/"), 800);
        }
      } else {
        const result = await register(name, email, password);
        if (!result.ok) {
          setErrorMsg(result.error);
        } else {
          setSuccessMsg(
            `Compte créé avec succès. Vous bénéficiez de ${result.profile.free_quota} analyses gratuites. Redirection…`
          );
          setTimeout(() => router.push("/"), 900);
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = () => {
    setMode((m) => (m === "connexion" ? "inscription" : "connexion"));
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* En-tête minimal */}
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour
          </Link>
          <div className="flex items-center gap-2.5 ml-2">
            <div className="w-8 h-8 rounded bg-blue-900 flex items-center justify-center text-white">
              <Shield className="w-4 h-4" />
            </div>
            <span className="font-bold tracking-tight text-slate-900 dark:text-white">
              SûrCheck<span className="text-blue-600 dark:text-blue-400">.bj</span>
            </span>
          </div>
        </div>
      </header>

      {/* Formulaire centré */}
      <main className="flex-1 flex items-start justify-center pt-12 px-4 pb-16">
        <div className="w-full max-w-md">
          {/* Titre */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {mode === "connexion" ? "Connexion à votre compte" : "Créer un compte"}
            </h1>
            <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
              {mode === "connexion"
                ? "Accédez à votre historique et à vos crédits d'analyse."
                : "5 analyses gratuites offertes à l'inscription."}
            </p>
          </div>

          {/* Carte formulaire */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm">
            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              {/* Nom — inscription seulement */}
              {mode === "inscription" && (
                <div>
                  <label
                    htmlFor="auth-name"
                    className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5"
                  >
                    Nom complet
                  </label>
                  <input
                    id="auth-name"
                    type="text"
                    autoComplete="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Votre prénom et nom"
                    className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    disabled={isLoading}
                  />
                </div>
              )}

              {/* Email */}
              <div>
                <label
                  htmlFor="auth-email"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5"
                >
                  Adresse email
                </label>
                <input
                  id="auth-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="vous@exemple.com"
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  disabled={isLoading}
                  required
                />
              </div>

              {/* Mot de passe */}
              <div>
                <label
                  htmlFor="auth-password"
                  className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5"
                >
                  Mot de passe
                </label>
                <div className="relative">
                  <input
                    id="auth-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete={mode === "connexion" ? "current-password" : "new-password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={mode === "inscription" ? "8 caractères minimum" : "Votre mot de passe"}
                    className="w-full px-3.5 py-2.5 pr-11 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    disabled={isLoading}
                    required
                    minLength={8}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
                    tabIndex={-1}
                    aria-label={showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Message d'erreur */}
              {errorMsg && (
                <div className="rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-300">
                  {errorMsg}
                </div>
              )}

              {/* Message de succès */}
              {successMsg && (
                <div className="rounded-lg bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-300">
                  {successMsg}
                </div>
              )}

              {/* Bouton principal */}
              <button
                id="auth-submit-btn"
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-lg bg-blue-900 hover:bg-blue-800 disabled:opacity-60 text-white font-semibold text-sm transition-colors"
              >
                {isLoading
                  ? "Chargement…"
                  : mode === "connexion"
                  ? "Se connecter"
                  : "Créer mon compte"}
              </button>
            </form>
          </div>

          {/* Lien bascule connexion/inscription */}
          <p className="mt-5 text-center text-sm text-slate-500 dark:text-slate-400">
            {mode === "connexion" ? "Pas encore de compte ? " : "Déjà inscrit ? "}
            <button
              onClick={switchMode}
              className="font-medium text-blue-600 dark:text-blue-400 hover:underline"
            >
              {mode === "connexion" ? "Créer un compte" : "Se connecter"}
            </button>
          </p>

          {/* Note confidentialité */}
          <p className="mt-4 text-center text-xs text-slate-400 dark:text-slate-600 max-w-xs mx-auto">
            Vos données sont hébergées en Europe. Aucun partage avec des tiers.
            Conforme à la législation béninoise sur la protection des données personnelles.
          </p>
        </div>
      </main>
    </div>
  );
}
