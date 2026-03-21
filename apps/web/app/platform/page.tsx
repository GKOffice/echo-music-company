"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import Navbar from "../../components/Navbar";
import { fetchPlatformStats, formatNumber } from "../../lib/api";

const FALLBACK_STATS = [
  { label: "Artists", value: "5,247" },
  { label: "Fans", value: "89,400" },
  { label: "Paid to Artists", value: "$2.4M" },
  { label: "Sync Placements", value: "85" },
];

const howItWorks = [
  {
    title: "For Artists",
    icon: "🎤",
    color: "#8b5cf6",
    steps: [
      "Submit your demo — AI reviews in minutes",
      "Keep 100% of your masters, always",
      "21 agents handle release, marketing & distribution",
      "Drop Melodio Points to fans and get paid upfront",
    ],
    cta: "Submit Your Demo",
    href: "/submit",
  },
  {
    title: "For Fans",
    icon: "🎧",
    color: "#10b981",
    steps: [
      "Browse artist point drops in the marketplace",
      "Buy points = fractional royalty ownership",
      "Earn every time your artist streams",
      "Trade points after 12-month hold period",
    ],
    cta: "Browse Points",
    href: "/points",
  },
  {
    title: "For Producers",
    icon: "🎛️",
    color: "#f59e0b",
    steps: [
      "Upload beats to the Melodio Beat Hub",
      "AI scores quality and sync readiness",
      "Hub Agent matches you to signed artists",
      "Get paid via smart contracts instantly",
    ],
    cta: "Apply as Producer",
    href: "/submit",
  },
  {
    title: "For Songwriters",
    icon: "✍️",
    color: "#10b981",
    steps: [
      "Register your catalog — we handle PRO registration",
      "We collect worldwide (ASCAP/BMI/MLC/60+ territories)",
      "Sell publishing points in the Deal Room",
      "Find co-write partners by genre and style",
    ],
    cta: "Register My Songs",
    href: "/songwriters",
  },
];

const TICKER_EVENTS = [
  "💎 Nova Vex just dropped 15 Melodio Points · $250/pt",
  "🔥 Lyra Bloom hit 142K monthly listeners",
  "⚡ Melo Cipher · 3 points sold in the last hour",
  "🎵 Dark Matter EP cleared by QC Agent",
  "📈 Khai Dusk streams up 18% this week",
  "💰 $4,960 paid to Nova Vex holders this month",
  "🎤 New submission from Lagos, Nigeria — A&R reviewing",
  "🌟 Zara Sol added to 3 editorial playlists",
  "⚡ Melodio Score updated for 12 artists",
  "🎛️ Beat Hub: 47 new beats scored this week",
];

const TESTIMONIALS = [
  {
    quote: "Melodio changed everything. I dropped my first point batch and had fans earning royalties within a week. The AI handles every step — I just make music.",
    name: "Nova Vex",
    genre: "Afrobeats",
    stat: "Earned $3,200 in first month",
    initial: "N",
  },
  {
    quote: "I used to lose 30% to middlemen. With Melodio, my fans own a piece of my catalog and I keep 90% of my publishing. This is how music should work.",
    name: "Lyra Bloom",
    genre: "Alt R&B",
    stat: "Earned $1,800 in first month",
    initial: "L",
  },
  {
    quote: "The Melodio Score gave my fans confidence to buy points early. Went from 0 to 98K monthly listeners in 3 months — all with 21 AI agents working for me 24/7.",
    name: "Khai Dusk",
    genre: "Trap Soul",
    stat: "Earned $2,400 in first month",
    initial: "K",
  },
];

const PRESS_LOGOS = ["Billboard", "Complex", "Pitchfork", "Rolling Stone", "Variety"];

function SocialProofSection() {
  const [current, setCurrent] = useState(0);
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setAnimating(true);
      setTimeout(() => {
        setCurrent((c) => (c + 1) % TESTIMONIALS.length);
        setAnimating(false);
      }, 300);
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const t = TESTIMONIALS[current];

  return (
    <section className="py-24 px-4 bg-[#13131a]">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 bg-[#10b981]/10 text-[#34d399] border border-[#10b981]/30 rounded-full px-4 py-2 text-sm mb-4">
            Artist Stories
          </div>
          <h2 className="text-3xl md:text-4xl font-black text-[#f9fafb]">
            Heard from the artists themselves
          </h2>
        </div>

        {/* Testimonial carousel */}
        <div className="relative overflow-hidden rounded-2xl border border-[#2a2a3a] bg-[#0a0a0f] p-8 md:p-12 mb-6 min-h-[220px] flex flex-col justify-between">
          <div
            className="transition-all duration-300"
            style={{ opacity: animating ? 0 : 1, transform: animating ? "translateY(12px)" : "translateY(0)" }}
          >
            <p className="text-[#d1d5db] text-lg md:text-xl leading-relaxed mb-8 italic">
              &ldquo;{t.quote}&rdquo;
            </p>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-white text-sm"
                  style={{ background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)" }}>
                  {t.initial}
                </div>
                <div>
                  <div className="text-[#f9fafb] font-semibold text-sm">{t.name}</div>
                  <div className="text-[#6b7280] text-xs">{t.genre}</div>
                </div>
              </div>
              <div className="bg-[#10b981]/10 border border-[#10b981]/30 rounded-full px-4 py-1.5 text-[#34d399] text-sm font-semibold">
                {t.stat}
              </div>
            </div>
          </div>

          {/* Dots */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
            {TESTIMONIALS.map((_, i) => (
              <button
                key={i}
                onClick={() => { setAnimating(false); setCurrent(i); }}
                className="transition-all duration-300"
                aria-label={`Go to testimonial ${i + 1}`}
              >
                <span className={`block rounded-full transition-all duration-300 ${i === current ? "w-5 h-1.5 bg-[#8b5cf6]" : "w-1.5 h-1.5 bg-[#2a2a3a]"}`} />
              </button>
            ))}
          </div>
        </div>

        {/* 3-card preview row (desktop) */}
        <div className="hidden md:grid grid-cols-3 gap-4 mb-16">
          {TESTIMONIALS.map((testimonial, i) => (
            <button
              key={i}
              onClick={() => { setAnimating(false); setCurrent(i); }}
              className={`text-left p-5 rounded-xl border transition-all duration-200 ${
                i === current
                  ? "border-[#8b5cf6] bg-[#8b5cf6]/5"
                  : "border-[#2a2a3a] bg-[#0a0a0f] hover:border-[#8b5cf6]/40"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-white text-xs"
                  style={{ background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)" }}>
                  {testimonial.initial}
                </div>
                <span className="text-sm font-semibold text-[#f9fafb]">{testimonial.name}</span>
              </div>
              <p className="text-xs text-[#6b7280] line-clamp-2">{testimonial.quote.slice(0, 80)}…</p>
              <p className="text-xs text-[#34d399] mt-2 font-medium">{testimonial.stat}</p>
            </button>
          ))}
        </div>

        {/* As Featured In */}
        <div className="text-center">
          <p className="text-xs font-semibold text-[#6b7280] uppercase tracking-widest mb-6">As Featured In</p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {PRESS_LOGOS.map((name) => (
              <div
                key={name}
                className="bg-[#1a1a24] border border-[#2a2a3a] rounded-lg px-5 py-2.5 text-[#9ca3af] text-sm font-semibold"
              >
                {name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function PlatformPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const [tickerOffset, setTickerOffset] = useState(0);

  const { data: apiStats } = useQuery({
    queryKey: ["platform-stats"],
    queryFn: fetchPlatformStats,
  });

  const platformStats = apiStats
    ? [
        { label: "Artists", value: formatNumber(apiStats.artists) },
        { label: "Fans", value: formatNumber(apiStats.fans) },
        { label: "Paid to Artists", value: `$${(apiStats.paid_to_artists / 1_000_000).toFixed(1)}M` },
        { label: "Sync Placements", value: String(apiStats.sync_placements) },
      ]
    : FALLBACK_STATS;

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!heroRef.current) return;
      const rect = heroRef.current.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      heroRef.current.style.setProperty("--mouse-x", `${x}%`);
      heroRef.current.style.setProperty("--mouse-y", `${y}%`);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      setTickerOffset((prev) => (prev + 1) % (TICKER_EVENTS.length * 280));
    }, 40);
    return () => clearInterval(id);
  }, []);

  return (
    <main className="min-h-screen bg-[#0a0a0f] overflow-x-hidden">
      <Navbar />

      {/* Hero */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex flex-col items-center justify-center text-center px-4 pt-20"
        style={{
          background:
            "radial-gradient(ellipse at var(--mouse-x, 50%) var(--mouse-y, 40%), rgba(139,92,246,0.15) 0%, transparent 60%), #0a0a0f",
        }}
      >
        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
          }}
        />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#8b5cf6]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-[#10b981]/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-8">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            21 AI agents online — Phase 3 Release Engine active
          </div>

          <h1 className="text-6xl md:text-8xl font-black tracking-tight mb-6 leading-none">
            <span className="text-[#f9fafb]">Own the</span>
            <br />
            <span
              style={{
                background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Sound.
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-[#9ca3af] max-w-3xl mx-auto mb-10 leading-relaxed">
            The AI-powered music company where artists keep their masters, fans earn royalties, and
            one song can change everything.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/submit"
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-lg px-8 py-4 rounded-lg transition-colors duration-200 w-full sm:w-auto text-center"
              style={{ boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
            >
              I&apos;m an Artist
            </Link>
            <Link
              href="/points"
              className="border border-[#8b5cf6] text-[#8b5cf6] hover:bg-[#8b5cf6]/10 font-semibold text-lg px-8 py-4 rounded-lg transition-colors duration-200 w-full sm:w-auto text-center"
            >
              Browse Points
            </Link>
          </div>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-[#9ca3af] text-xs animate-bounce">
          <span>Scroll to explore</span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-y border-[#2a2a3a] bg-[#13131a]">
        <div className="max-w-5xl mx-auto px-4 py-8 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {platformStats.map((s) => (
            <div key={s.label}>
              <div className="text-2xl font-black text-[#f9fafb]">{s.value}</div>
              <div className="text-sm text-[#9ca3af] mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-4 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-black text-[#f9fafb] mb-4">
            How{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Melodio Works
            </span>
          </h2>
          <p className="text-[#9ca3af] text-lg max-w-2xl mx-auto">
            One platform for artists, fans, producers, and songwriters — all powered by 21 autonomous AI agents.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {howItWorks.map((col) => (
            <div
              key={col.title}
              className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-8 flex flex-col hover:border-[#8b5cf6] transition-colors duration-200"
            >
              <div className="text-4xl mb-4">{col.icon}</div>
              <h3 className="text-xl font-bold text-[#f9fafb] mb-6">{col.title}</h3>
              <ul className="space-y-3 flex-1 mb-8">
                {col.steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm text-[#9ca3af]">
                    <span className="text-[#10b981] font-bold mt-0.5 shrink-0">{i + 1}.</span>
                    {step}
                  </li>
                ))}
              </ul>
              <Link
                href={col.href}
                className="block text-center border border-[#2a2a3a] hover:border-[#8b5cf6] font-semibold text-sm px-5 py-2.5 rounded-lg transition-colors duration-200"
                style={{ color: col.color }}
              >
                {col.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Live Activity Feed */}
      <section className="py-12 border-y border-[#2a2a3a] bg-[#13131a] overflow-hidden">
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 text-sm text-[#9ca3af]">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            Live Activity
          </div>
        </div>
        <div className="overflow-hidden">
          <div
            className="flex gap-8 whitespace-nowrap"
            style={{
              transform: `translateX(-${tickerOffset}px)`,
              transition: "transform 0.04s linear",
            }}
          >
            {[...TICKER_EVENTS, ...TICKER_EVENTS, ...TICKER_EVENTS].map((event, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-2 text-sm text-[#9ca3af] bg-[#0a0a0f] border border-[#2a2a3a] rounded-full px-4 py-2 shrink-0"
              >
                {event}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <SocialProofSection />

      {/* ECHO Points CTA */}
      <section className="py-24 px-4 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/20 text-[#a78bfa] border border-[#8b5cf6]/30 rounded-full px-4 py-2 text-sm mb-6">
          Now Live
        </div>
        <h2 className="text-4xl md:text-5xl font-black text-[#f9fafb] mb-6">
          Buy in.{" "}
          <span
            style={{
              background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Earn forever.
          </span>
        </h2>
        <p className="text-[#9ca3af] text-lg max-w-2xl mx-auto mb-10">
          Melodio Points give fans fractional royalty ownership in the artists they love. Buy points.
          Earn every time they stream. Share in the success.
        </p>
        <Link
          href="/points"
          className="inline-block bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-lg px-10 py-4 rounded-lg transition-colors duration-200"
          style={{ boxShadow: "0 0 30px rgba(139,92,246,0.4)" }}
        >
          Browse the Points Store
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#2a2a3a] py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
            <div className="flex items-center gap-2">
              <span className="text-[#8b5cf6] font-black text-xl">🎵 Melodio</span>
              <span className="text-[#9ca3af] text-sm ml-2">Autonomous AI Music Company</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-[#9ca3af]">
              <Link href="/points" className="hover:text-[#f9fafb] transition-colors">Points Store</Link>
              <Link href="/submit" className="hover:text-[#f9fafb] transition-colors">Submit Demo</Link>
              <Link href="/dashboard" className="hover:text-[#f9fafb] transition-colors">Dashboard</Link>
            </div>
          </div>
          <div className="border-t border-[#2a2a3a] pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-[#9ca3af]">
            <span className="font-semibold text-[#f9fafb]">No long-term contracts. Ever.</span>
            <span>© {new Date().getFullYear()} Melodio — All rights to artists</span>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-[#10b981] rounded-full animate-pulse" />
              All 21 agents operational
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
