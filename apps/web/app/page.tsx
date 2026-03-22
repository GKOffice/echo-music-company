"use client";

import { useState } from "react";
import { redirect } from "next/navigation";

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
      className="min-h-screen flex flex-col items-center px-4 relative overflow-hidden"
      style={{ background: "#0a0a0a", fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] rounded-full opacity-15 blur-3xl"
          style={{ background: "radial-gradient(ellipse at center, #6d28d9 0%, #4c1d95 40%, transparent 70%)" }}
        />
        <div
          className="absolute bottom-1/3 right-0 w-[500px] h-[500px] rounded-full opacity-10 blur-3xl"
          style={{ background: "radial-gradient(ellipse at center, #3b82f6 0%, transparent 70%)" }}
        />
        <div
          className="absolute bottom-0 left-1/4 w-[400px] h-[400px] rounded-full opacity-8 blur-3xl"
          style={{ background: "radial-gradient(ellipse at center, #ec4899 0%, transparent 70%)" }}
        />
      </div>

      {/* Grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
        aria-hidden="true"
      />

      {/* Nav */}
      <nav className="relative z-10 w-full max-w-6xl flex items-center justify-between py-6">
        <span
          className="text-2xl font-black tracking-tight"
          style={{
            background: "linear-gradient(135deg, #ffffff 0%, #c4b5fd 60%, #60a5fa 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          Melodio
        </span>
        <span
          className="text-xs font-semibold uppercase tracking-[0.15em] px-3 py-1 rounded-full border"
          style={{ color: "#a78bfa", borderColor: "rgba(139,92,246,0.3)", background: "rgba(139,92,246,0.08)" }}
        >
          Coming Soon
        </span>
      </nav>

      {/* Hero */}
      <section className="relative z-10 w-full max-w-4xl text-center flex flex-col items-center gap-6 pt-16 pb-20">
        <div
          className="text-xs font-semibold uppercase tracking-[0.2em] px-4 py-1.5 rounded-full border mb-2"
          style={{ color: "#a78bfa", borderColor: "rgba(139,92,246,0.3)", background: "rgba(139,92,246,0.08)" }}
        >
          The first fully autonomous AI music company
        </div>

        <h1
          className="text-5xl sm:text-6xl md:text-8xl font-black tracking-tight leading-[0.9] select-none"
          style={{
            background: "linear-gradient(135deg, #ffffff 0%, #c4b5fd 40%, #818cf8 70%, #60a5fa 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            filter: "drop-shadow(0 0 60px rgba(139,92,246,0.4))",
          }}
        >
          Music has<br />a new boss.
        </h1>

        <p className="text-lg sm:text-xl max-w-2xl leading-relaxed" style={{ color: "#9ca3af" }}>
          Melodio is an AI-powered music company that signs artists, releases music,
          collects royalties, and builds careers — autonomously, 24/7. No gatekeepers.
          No middlemen. Just your music and your money.
        </p>

        {/* Email capture */}
        <div className="w-full max-w-lg mt-4">
          {status === "success" ? (
            <div
              className="w-full rounded-xl px-6 py-5 text-center border"
              style={{ background: "rgba(16,185,129,0.08)", borderColor: "rgba(16,185,129,0.3)" }}
            >
              <p className="text-[#34d399] font-semibold text-base">{message}</p>
              <p className="text-[#6b7280] text-sm mt-1">We&apos;ll be in touch when we&apos;re ready for you.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3" noValidate>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                disabled={status === "loading"}
                className="flex-1 rounded-lg px-4 py-3.5 text-sm outline-none transition-all duration-200 disabled:opacity-50"
                style={{ background: "#13131a", border: "1px solid #2a2a3a", color: "#f9fafb" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "#8b5cf6"; e.currentTarget.style.boxShadow = "0 0 0 2px rgba(139,92,246,0.2)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "#2a2a3a"; e.currentTarget.style.boxShadow = "none"; }}
              />
              <button
                type="submit"
                disabled={status === "loading" || !email}
                className="rounded-lg px-6 py-3.5 text-sm font-semibold text-white transition-all duration-200 whitespace-nowrap disabled:opacity-50"
                style={{ background: "#8b5cf6", boxShadow: "0 0 24px rgba(139,92,246,0.4)" }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "#7c3aed"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "#8b5cf6"; }}
              >
                {status === "loading" ? "Joining…" : "Get Early Access"}
              </button>
            </form>
          )}
          {status === "error" && <p className="text-sm mt-2" style={{ color: "#f87171" }}>{message}</p>}
          <p className="text-xs mt-3" style={{ color: "#374151" }}>No spam. No nonsense. Just the future of music.</p>
        </div>
      </section>

      {/* What we do */}
      <section className="relative z-10 w-full max-w-5xl pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              icon: "🎤",
              title: "Label",
              desc: "We sign artists on 1-song deals. You keep 60% of revenue and get your masters back in 5 years. Always.",
            },
            {
              icon: "💰",
              title: "Publishing",
              desc: "We collect your royalties from 60+ PROs worldwide. We keep 0% — just a 10% admin fee. 90% goes to you.",
            },
            {
              icon: "📈",
              title: "Platform",
              desc: "À la carte services for independent artists. Distribution, marketing, sync pitching, PR — pick what you need.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-2xl p-6 flex flex-col gap-3 border"
              style={{ background: "rgba(255,255,255,0.03)", borderColor: "rgba(255,255,255,0.07)" }}
            >
              <span className="text-3xl">{item.icon}</span>
              <h3 className="text-white font-bold text-lg">{item.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: "#6b7280" }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats */}
      <section className="relative z-10 w-full max-w-5xl pb-20">
        <div
          className="rounded-2xl p-8 border grid grid-cols-2 sm:grid-cols-4 gap-8 text-center"
          style={{ background: "rgba(139,92,246,0.05)", borderColor: "rgba(139,92,246,0.15)" }}
        >
          {[
            { number: "23", label: "AI Agents" },
            { number: "0%", label: "Publishing cut" },
            { number: "60%", label: "Revenue to artist" },
            { number: "24/7", label: "Always working" },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col gap-1">
              <span
                className="text-4xl font-black"
                style={{
                  background: "linear-gradient(135deg, #c4b5fd, #818cf8)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {stat.number}
              </span>
              <span className="text-xs uppercase tracking-wider" style={{ color: "#6b7280" }}>{stat.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="relative z-10 w-full max-w-4xl pb-20 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-12">How it works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {[
            { step: "01", title: "Submit your demo", desc: "Our A&R agent screens it in 60 seconds using 6 scoring dimensions. No waiting months." },
            { step: "02", title: "We build your career", desc: "23 agents handle distribution, marketing, PR, sync, and royalties. You focus on making music." },
            { step: "03", title: "You get paid", desc: "Royalties collected from 60+ PROs worldwide. Quarterly payouts. Full transparency always." },
          ].map((item) => (
            <div key={item.step} className="flex flex-col items-center gap-4">
              <span
                className="text-5xl font-black opacity-20"
                style={{ color: "#8b5cf6" }}
              >
                {item.step}
              </span>
              <h3 className="text-white font-bold text-lg">{item.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: "#6b7280" }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Melodio Points teaser */}
      <section className="relative z-10 w-full max-w-4xl pb-24">
        <div
          className="rounded-2xl p-8 sm:p-12 border text-center flex flex-col items-center gap-6"
          style={{ background: "rgba(139,92,246,0.06)", borderColor: "rgba(139,92,246,0.2)" }}
        >
          <div
            className="text-xs font-semibold uppercase tracking-[0.2em] px-4 py-1.5 rounded-full border"
            style={{ color: "#a78bfa", borderColor: "rgba(139,92,246,0.3)", background: "rgba(139,92,246,0.08)" }}
          >
            Introducing Melodio Points
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Own a piece of the music.</h2>
          <p className="max-w-xl leading-relaxed" style={{ color: "#9ca3af" }}>
            Buy fractional royalty rights on songs you believe in. 1 point = 1% of a song&apos;s revenue.
            Hold and earn quarterly royalties, or trade on the Melodio Exchange after 12 months.
          </p>
          <span className="text-sm font-semibold" style={{ color: "#a78bfa" }}>Launching soon →</span>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-5xl border-t pb-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-2" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        <span
          className="text-lg font-black"
          style={{
            background: "linear-gradient(135deg, #ffffff 0%, #c4b5fd 60%, #60a5fa 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          Melodio
        </span>
        <p className="text-xs" style={{ color: "#374151" }}>
          © {new Date().getFullYear()} Melodio · The future of music is being built.
        </p>
      </footer>
    </main>
  );
}
