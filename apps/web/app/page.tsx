"use client";

import { useEffect, useRef } from "react";

const stats = [
  { label: "Artists Signed", value: "0", suffix: "", prefix: "" },
  { label: "Streams Generated", value: "0", suffix: "M", prefix: "" },
  { label: "Royalties Distributed", value: "$0", suffix: "", prefix: "" },
  { label: "Agent Operations", value: "21", suffix: "", prefix: "" },
];

const agents = [
  { id: "CEO", label: "CEO Agent", desc: "Orchestrates all 21 agents and company strategy", color: "#8b5cf6" },
  { id: "A&R", label: "A&R Agent", desc: "Discovers and signs talent via AI analysis", color: "#7c3aed" },
  { id: "PROD", label: "Production Agent", desc: "Manages recording, mixing, and mastering", color: "#6d28d9" },
  { id: "DIST", label: "Distribution Agent", desc: "Deploys releases to all DSPs globally", color: "#10b981" },
  { id: "MKT", label: "Marketing Agent", desc: "Runs campaigns across all platforms", color: "#059669" },
  { id: "FIN", label: "Finance Agent", desc: "Tracks revenue, royalties, and advances", color: "#0d9488" },
];

const phases = [
  { num: "01", label: "Scout", desc: "AI discovers talent from millions of signals", done: true },
  { num: "02", label: "Sign", desc: "Smart contracts drafted and executed autonomously", done: true },
  { num: "03", label: "Release", desc: "Full release engine — from recording to DSPs", active: true },
  { num: "04", label: "Monetize", desc: "ECHO Points: fractional royalty ownership", done: false },
  { num: "05", label: "Scale", desc: "Catalog growth and sync licensing", done: false },
];

export default function HomePage() {
  const heroRef = useRef<HTMLDivElement>(null);

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

  return (
    <main className="min-h-screen bg-background overflow-x-hidden">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-4 bg-background/80 backdrop-blur-xl border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-echo flex items-center justify-center font-black text-white text-sm">
            E
          </div>
          <span className="font-bold text-lg tracking-tight text-text-primary">ECHO</span>
          <span className="badge badge-primary text-xs ml-1">Phase 3</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm text-text-muted">
          <a href="#agents" className="hover:text-text-primary transition-colors">Agents</a>
          <a href="#phases" className="hover:text-text-primary transition-colors">Roadmap</a>
          <a href="#hub" className="hover:text-text-primary transition-colors">Beat Hub</a>
          <a href="#points" className="hover:text-text-primary transition-colors">ECHO Points</a>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary text-sm py-2 px-4">Sign In</button>
          <button className="btn-primary text-sm py-2 px-4">Get Access</button>
        </div>
      </nav>

      {/* Hero */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex flex-col items-center justify-center text-center px-4 pt-20"
        style={{
          background:
            "radial-gradient(ellipse at var(--mouse-x, 50%) var(--mouse-y, 40%), rgba(139,92,246,0.15) 0%, transparent 60%), #0a0a0f",
        }}
      >
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
          }}
        />

        {/* Glow orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-5xl mx-auto animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-surface border border-border rounded-full px-4 py-2 text-sm text-text-muted mb-8">
            <span className="w-2 h-2 bg-accent rounded-full animate-pulse" />
            21 AI agents online — Phase 3 Release Engine active
          </div>

          <h1 className="text-6xl md:text-8xl font-black tracking-tight mb-6 leading-none">
            <span className="text-text-primary">Own the</span>
            <br />
            <span className="gradient-text">Sound</span>
          </h1>

          <p className="text-xl md:text-2xl text-text-muted max-w-3xl mx-auto mb-4 leading-relaxed">
            The world's first fully autonomous AI music company. 21 specialized agents handle every
            aspect of artist discovery, release, and monetization — 24/7, with no human bottlenecks.
          </p>

          <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-12">
            Buy <span className="text-primary font-semibold">ECHO Points</span> and earn royalties
            from the music you believe in.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <button className="btn-primary text-lg px-8 py-4 w-full sm:w-auto glow-primary">
              Explore Beat Hub
            </button>
            <button className="btn-secondary text-lg px-8 py-4 w-full sm:w-auto">
              Submit Your Demo
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
            {stats.map((stat) => (
              <div key={stat.label} className="card text-center">
                <div className="text-2xl font-black text-text-primary mb-1">
                  {stat.prefix}
                  <span className="gradient-text">{stat.value}</span>
                  {stat.suffix}
                </div>
                <div className="text-xs text-text-muted">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-text-muted text-xs animate-bounce">
          <span>Scroll to explore</span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </section>

      {/* Agents */}
      <section id="agents" className="py-24 px-4 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-4">
            21 Agents.{" "}
            <span className="gradient-text">One Company.</span>
          </h2>
          <p className="text-text-muted text-lg max-w-2xl mx-auto">
            Every function of a music label — A&R, production, distribution, marketing, legal,
            finance — handled by specialized AI agents operating in concert.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div key={agent.id} className="card-hover group">
              <div className="flex items-start gap-4">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-xs shrink-0 transition-all duration-200 group-hover:scale-110"
                  style={{ backgroundColor: agent.color }}
                >
                  {agent.id}
                </div>
                <div>
                  <div className="font-semibold text-text-primary mb-1">{agent.label}</div>
                  <div className="text-sm text-text-muted">{agent.desc}</div>
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
                <span className="text-xs text-accent">Online</span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <p className="text-text-muted text-sm">
            + 15 more agents: Legal, Creative, Sync, Artist Dev, PR, Comms, QC, Infrastructure, Intake, Merch, YouTube, Hub, Vault, Social, Analytics
          </p>
        </div>
      </section>

      {/* Phases */}
      <section id="phases" className="py-24 px-4 bg-surface border-y border-border">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-4">
              The ECHO <span className="gradient-text">Playbook</span>
            </h2>
            <p className="text-text-muted text-lg">
              Five phases from zero to a fully autonomous global music operation.
            </p>
          </div>

          <div className="space-y-4">
            {phases.map((phase) => (
              <div
                key={phase.num}
                className={`flex items-center gap-6 p-6 rounded-xl border transition-all duration-200 ${
                  phase.active
                    ? "bg-primary/10 border-primary/50 glow-primary"
                    : phase.done
                    ? "bg-surface-2 border-accent/30"
                    : "bg-surface-2 border-border opacity-60"
                }`}
              >
                <div
                  className={`text-4xl font-black tabular-nums shrink-0 ${
                    phase.active ? "gradient-text" : phase.done ? "text-accent/60" : "text-border"
                  }`}
                >
                  {phase.num}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-bold text-lg text-text-primary">{phase.label}</span>
                    {phase.active && <span className="badge badge-primary">Current</span>}
                    {phase.done && <span className="badge badge-accent">Complete</span>}
                  </div>
                  <p className="text-text-muted text-sm">{phase.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ECHO Points */}
      <section id="points" className="py-24 px-4 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div>
            <div className="badge badge-primary mb-4">Coming Soon</div>
            <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-6">
              ECHO <span className="gradient-text">Points</span>
            </h2>
            <p className="text-text-muted text-lg mb-6 leading-relaxed">
              Buy fractional ownership stakes in individual tracks and releases. When streams flow,
              royalties flow directly to your wallet — proportional to your points.
            </p>
            <ul className="space-y-3 mb-8">
              {[
                "Master rights points — earn from streaming royalties",
                "Publishing points — earn from mechanical & performance",
                "Bundle points — both master + publishing in one",
                "12-month holding period, then freely tradeable",
                "Real-time royalty tracking dashboard",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-text-secondary text-sm">
                  <span className="text-accent mt-0.5">✓</span>
                  {item}
                </li>
              ))}
            </ul>
            <button className="btn-primary" disabled>
              Whitelist Opening Soon
            </button>
          </div>

          <div className="card glow-primary">
            <div className="text-xs text-text-muted uppercase tracking-wider mb-4">Sample Portfolio</div>
            <div className="space-y-3">
              {[
                { track: "Midnight Drive", artist: "Artist TBD", type: "Master", points: "250", value: "$500", roi: "+12%" },
                { track: "Neon Lights", artist: "Artist TBD", type: "Bundle", points: "100", value: "$350", roi: "+8%" },
                { track: "Dark Matter", artist: "Artist TBD", type: "Publishing", points: "500", value: "$750", roi: "+21%" },
              ].map((item) => (
                <div key={item.track} className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
                  <div>
                    <div className="font-medium text-text-primary text-sm">{item.track}</div>
                    <div className="text-xs text-text-muted">{item.artist} · {item.type}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-text-primary">{item.value}</div>
                    <div className="text-xs text-accent">{item.roi}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-border flex justify-between text-sm">
              <span className="text-text-muted">Total Value</span>
              <span className="font-bold text-text-primary">$1,600</span>
            </div>
          </div>
        </div>
      </section>

      {/* Beat Hub */}
      <section id="hub" className="py-24 px-4 bg-surface border-y border-border">
        <div className="max-w-7xl mx-auto text-center">
          <div className="badge badge-accent mb-4">Producer Network</div>
          <h2 className="text-4xl md:text-5xl font-black text-text-primary mb-4">
            The Beat <span className="gradient-text">Hub</span>
          </h2>
          <p className="text-text-muted text-lg max-w-2xl mx-auto mb-12">
            A curated marketplace where ECHO's AI-scored beats meet our signed artists.
            Producers earn placements. Artists get premium production. The Hub agent connects them.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-8">
            {[
              { emoji: "🎛️", title: "AI Quality Scoring", desc: "Every beat scored for quality, uniqueness, and sync readiness before listing" },
              { emoji: "🤝", title: "Smart Matching", desc: "Hub agent matches beats to artists based on genre, mood, and upcoming releases" },
              { emoji: "💰", title: "Instant Licensing", desc: "Non-exclusive and exclusive deals executed automatically via smart contracts" },
            ].map((item) => (
              <div key={item.title} className="card text-left">
                <div className="text-3xl mb-3">{item.emoji}</div>
                <div className="font-semibold text-text-primary mb-2">{item.title}</div>
                <div className="text-sm text-text-muted">{item.desc}</div>
              </div>
            ))}
          </div>
          <button className="btn-accent">Apply as Producer</button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-gradient-echo flex items-center justify-center font-black text-white text-xs">
              E
            </div>
            <span className="font-bold text-text-primary">ECHO</span>
            <span className="text-text-muted text-sm">Autonomous AI Music Company</span>
          </div>
          <div className="text-sm text-text-muted">
            Phase 3 — Release Engine — {new Date().getFullYear()}
          </div>
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
            All systems operational
          </div>
        </div>
      </footer>
    </main>
  );
}
