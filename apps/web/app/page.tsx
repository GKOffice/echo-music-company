"use client";

import { useState } from "react";
import { redirect } from "next/navigation";

// Env gate: set NEXT_PUBLIC_COMING_SOON=false to show the real platform instead
const COMING_SOON = process.env.NEXT_PUBLIC_COMING_SOON !== "false";

export default function HomePage() {
  if (!COMING_SOON) {
    redirect("/platform");
  }
  return <ComingSoonPage />;
}

function ComingSoonPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !email.includes("@")) return;
    setStatus("loading");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("success");
        setMessage(data.message || "You are on the list.");
        setEmail("");
      } else {
        setStatus("error");
        setMessage("Something went wrong. Try again.");
      }
    } catch {
      setStatus("error");
      setMessage("Something went wrong. Try again.");
    }
  }

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-4 relative overflow-hidden"
      style={{ background: "#0a0a0a" }}
    >
      {/* Background glow blobs */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[500px] rounded-full opacity-20 blur-3xl"
          style={{
            background:
              "radial-gradient(ellipse at center, #6d28d9 0%, #4c1d95 40%, transparent 70%)",
          }}
        />
        <div
          className="absolute bottom-0 right-1/3 w-[400px] h-[400px] rounded-full opacity-10 blur-3xl"
          style={{
            background: "radial-gradient(ellipse at center, #3b82f6 0%, transparent 70%)",
          }}
        />
      </div>

      {/* Subtle grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 w-full max-w-xl text-center flex flex-col items-center gap-8">
        {/* Wordmark */}
        <div>
          <h1
            className="text-6xl sm:text-7xl md:text-8xl font-black tracking-tight leading-none select-none"
            style={{
              background:
                "linear-gradient(135deg, #ffffff 0%, #c4b5fd 40%, #818cf8 70%, #60a5fa 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              filter: "drop-shadow(0 0 40px rgba(139,92,246,0.35))",
            }}
          >
            Melodio
          </h1>
        </div>

        {/* Badge */}
        <p
          className="text-xs font-semibold uppercase tracking-[0.2em] px-4 py-1.5 rounded-full border"
          style={{
            color: "#a78bfa",
            borderColor: "rgba(139,92,246,0.3)",
            background: "rgba(139,92,246,0.08)",
          }}
        >
          The first fully autonomous AI music company.
        </p>

        {/* Tagline */}
        <p
          className="text-xl sm:text-2xl md:text-3xl font-light leading-snug"
          style={{ color: "#e5e7eb" }}
        >
          The future of music is being built.
        </p>

        {/* Sub-tagline */}
        <p className="text-sm sm:text-base max-w-sm leading-relaxed" style={{ color: "#6b7280" }}>
          21 AI agents. Zero middlemen. 100% ownership for artists.
          <br />
          Join the waitlist to get in first.
        </p>

        {/* Email capture */}
        {status === "success" ? (
          <div
            className="w-full rounded-xl px-6 py-5 text-center border"
            style={{
              background: "rgba(16,185,129,0.08)",
              borderColor: "rgba(16,185,129,0.3)",
            }}
          >
            <p className="text-[#34d399] font-semibold text-base">{message}</p>
            <p className="text-[#6b7280] text-sm mt-1">We&apos;ll reach out when we&apos;re ready.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="w-full flex flex-col sm:flex-row gap-3" noValidate>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              disabled={status === "loading"}
              className="flex-1 rounded-lg px-4 py-3 text-sm outline-none transition-all duration-200 disabled:opacity-50"
              style={{
                background: "#13131a",
                border: "1px solid #2a2a3a",
                color: "#f9fafb",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "#8b5cf6";
                e.currentTarget.style.boxShadow = "0 0 0 2px rgba(139,92,246,0.2)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "#2a2a3a";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
            <button
              type="submit"
              disabled={status === "loading" || !email}
              className="rounded-lg px-6 py-3 text-sm font-semibold text-white transition-all duration-200 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: status === "loading" ? "#6d28d9" : "#8b5cf6",
                boxShadow: "0 0 20px rgba(139,92,246,0.4)",
              }}
              onMouseEnter={(e) => {
                if (status !== "loading") e.currentTarget.style.background = "#7c3aed";
              }}
              onMouseLeave={(e) => {
                if (status !== "loading") e.currentTarget.style.background = "#8b5cf6";
              }}
            >
              {status === "loading" ? "Joining\u2026" : "Get Early Access"}
            </button>
          </form>
        )}

        {status === "error" && (
          <p className="text-sm" style={{ color: "#f87171" }}>{message}</p>
        )}

        <p className="text-xs" style={{ color: "#374151" }}>
          No spam. No nonsense. Just the future of music.
        </p>
      </div>

      {/* Bottom fade */}
      <div
        className="pointer-events-none absolute bottom-0 left-0 right-0 h-32"
        style={{ background: "linear-gradient(to top, #0a0a0a, transparent)" }}
        aria-hidden="true"
      />

      <footer className="absolute bottom-6 left-0 right-0 text-center z-10">
        <p className="text-xs" style={{ color: "#374151" }}>
          © {new Date().getFullYear()} Melodio
        </p>
      </footer>
    </main>
  );
}
