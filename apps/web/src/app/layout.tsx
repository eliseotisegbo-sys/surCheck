import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#0f172a",
};

export const metadata: Metadata = {
  title: "SûrCheck AI | Avant d'envoyer ton argent, vérifie.",
  description:
    "Outil citoyen d'analyse et de prévention des risques d'arnaques numériques, faux messages Mobile Money et liens suspects au Bénin et en Afrique de l'Ouest.",
  keywords: [
    "SûrCheck",
    "Bénin",
    "Mobile Money",
    "MTN",
    "Moov",
    "Arnaque",
    "Vérification",
    "Sécurité numérique",
  ],
  authors: [{ name: "SûrCheck AI" }],
  openGraph: {
    title: "SûrCheck AI | Vérifie avant de payer",
    description:
      "Analysez un SMS, un message WhatsApp ou un lien avant d'envoyer de l'argent ou de partager un code secret.",
    type: "website",
    locale: "fr_BJ",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="h-full scroll-smooth">
      <body className={`${inter.className} min-h-full flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 antialiased selection:bg-blue-600 selection:text-white`}>
        {children}
      </body>
    </html>
  );
}
