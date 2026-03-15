import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "ECHO — Own the Sound",
    template: "%s | ECHO",
  },
  description:
    "ECHO is an autonomous AI music company. Discover, invest, and earn royalties from the music you believe in.",
  keywords: ["music", "royalties", "AI", "streaming", "investment", "artists"],
  authors: [{ name: "ECHO" }],
  openGraph: {
    title: "ECHO — Own the Sound",
    description: "Autonomous AI music company. Own the music you love.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0f",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="bg-background text-text-primary antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
