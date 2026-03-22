import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Providers from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Melodio — The First Fully Autonomous AI Music Company",
    template: "%s | Melodio",
  },
  description:
    "23 AI agents. Zero middlemen. 100% ownership. Melodio signs artists, releases music, and collects royalties — autonomously.",
  keywords: [
    "music",
    "royalties",
    "AI",
    "streaming",
    "ownership",
    "artists",
    "autonomous",
    "music company",
    "melodio",
    "melodio points",
  ],
  authors: [{ name: "Melodio" }],
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Melodio",
  },
  openGraph: {
    title: "Melodio — The First Fully Autonomous AI Music Company",
    description:
      "23 AI agents. Zero middlemen. 100% ownership. Melodio signs artists, releases music, and collects royalties — autonomously.",
    type: "website",
    siteName: "Melodio",
    images: [
      {
        url: "https://melodio.io/og-image.png",
        width: 1200,
        height: 630,
        alt: "Melodio — Autonomous AI Music Company",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Melodio — The First Fully Autonomous AI Music Company",
    description:
      "23 AI agents. Zero middlemen. 100% ownership. Melodio signs artists, releases music, and collects royalties — autonomously.",
    images: ["https://melodio.io/og-image.png"],
  },
};

export const viewport: Viewport = {
  themeColor: "#8b5cf6",
  colorScheme: "dark light",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        {/* Anti-FOUC: apply saved theme before first paint */}
        <script
          dangerouslySetInnerHTML={{
            __html: `try{var t=localStorage.getItem('melodio_theme');if(t==='light')document.documentElement.setAttribute('data-theme','light');}catch(e){}`,
          }}
        />
        {/* PWA icons */}
        <link rel="apple-touch-icon" sizes="180x180" href="/icons/icon-192x192.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/icons/icon-192x192.png" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Melodio" />
      </head>
      <body className="bg-background text-text-primary antialiased min-h-screen">
        <Providers>{children}</Providers>
        {/* Service Worker registration */}
        <script
          dangerouslySetInnerHTML={{
            __html: `if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){});})}`,
          }}
        />
      </body>
    </html>
  );
}
