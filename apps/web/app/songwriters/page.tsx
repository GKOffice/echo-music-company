"use client";

import Link from "next/link";
import Navbar from "../../components/Navbar";

const STATS = [
  { value: "1,247", label: "Songs Registered" },
  { value: "$2.1M", label: "Collected" },
  { value: "85", label: "Sync Placements" },
  { value: "340", label: "Active Deals" },
];

const HOW_IT_WORKS = [
  {
    icon: "📝",
    title: "Register Your Songs",
    desc: "Add your existing catalog or upload new works. We register with ASCAP/BMI/MLC automatically.",
  },
  {
    icon: "💰",
    title: "Collect Everywhere",
    desc: "We collect performance, mechanical, sync, and neighboring rights from 60+ territories.",
  },
  {
    icon: "💎",
    title: "Sell Publishing Points",
    desc: "List your publishing points in the Deal Room. Fans and creators buy. You earn upfront + keep royalties.",
  },
  {
    icon: "🤝",
    title: "Find Co-writers",
    desc: "Post a co-write opportunity. Match with songwriters by genre and style. Split points, not cash.",
  },
];

const REVENUE_SOURCES = [
  { icon: "🎼", name: "Performance Royalties", org: "ASCAP/BMI/SESAC", desc: "Earned when your song is performed or broadcast" },
  { icon: "💿", name: "Mechanical Royalties", org: "MLC", desc: "Earned from digital downloads and streams" },
  { icon: "🎬", name: "Sync Licensing", org: "film, TV, ads", desc: "One-time fees for using your song in visual media" },
  { icon: "📺", name: "YouTube Content ID", org: "YouTube", desc: "Revenue from videos using your song on YouTube" },
  { icon: "📡", name: "Digital Performance", org: "SoundExchange", desc: "Earned from internet radio and satellite play" },
  { icon: "🌍", name: "International Collection", org: "60+ territories", desc: "Royalties collected worldwide through sub-publishers" },
  { icon: "🎤", name: "Cover Song Royalties", org: "when others cover you", desc: "Mechanical royalties when artists cover your work" },
  { icon: "📄", name: "Print/Lyric Licensing", org: "print & digital", desc: "Revenue from sheet music and lyric display sites" },
];

const COWRITE_OPPS = [
  {
    avatar: "🎤",
    seeker: "Marcus Reid",
    genre: "R&B",
    need: "Looking for R&B co-writer for upcoming EP. Need emotional hooks.",
    offer: "20% publishing points",
    deadline: "Rolling",
    color: "#8b5cf6",
  },
  {
    avatar: "🎛️",
    seeker: "Neon Flux (Producer)",
    genre: "Pop",
    need: "Seeking topline writer for Pop single. Track ready to record.",
    offer: "$500 + 15% publishing",
    deadline: "Mar 30",
    color: "#f59e0b",
  },
  {
    avatar: "🎵",
    seeker: "Aaliya J",
    genre: "Hip-Hop",
    need: "Seeking lyricist for Hip-Hop EP (4 tracks). Open to publishing split.",
    offer: "25% publishing pts / track",
    deadline: "Apr 15",
    color: "#10b981",
  },
];

const TIERS = [
  {
    name: "Starter",
    price: "Free",
    color: "#9ca3af",
    features: [
      "Register up to 5 songs",
      "Basic worldwide collection",
      "12% admin fee",
      "PRO registration",
    ],
    cta: "Start Free",
  },
  {
    name: "Growth",
    price: "$29/mo",
    color: "#8b5cf6",
    popular: true,
    features: [
      "Unlimited songs",
      "10% admin fee",
      "Sync pitching (15% commission)",
      "Deal Room access",
      "Priority A&R review",
    ],
    cta: "Get Growth",
  },
  {
    name: "Pro",
    price: "$99/mo",
    color: "#f59e0b",
    features: [
      "8% admin fee",
      "Priority sync pitching",
      "Dedicated AI Sync Agent",
      "Full publishing analytics",
      "White-glove onboarding",
    ],
    cta: "Go Pro",
  },
];

const FAQS = [
  {
    q: "What is a publishing point?",
    a: "A publishing point is a fractional share of your song's publishing rights. If you sell 10 points of a song, the buyer earns 10% of the publishing royalties — while you keep the copyright.",
  },
  {
    q: "How much does Melodio keep?",
    a: "We charge an admin fee only: 12% on Starter, 10% on Growth, 8% on Pro. No hidden fees. No percentage of your masters. You keep the copyright, always.",
  },
  {
    q: "Can I list songs I already released?",
    a: "Yes. You can register songs you've already released to streaming platforms. We'll pull your ISRC and existing royalty history automatically and set up collection going forward.",
  },
  {
    q: "How long until I get paid?",
    a: "PROs typically pay quarterly with a 3–6 month lag. MLC and SoundExchange pay quarterly. International collection can take 6–12 months for first payment. We display all status in your dashboard.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes. You can cancel your subscription anytime. Songs you've registered stay registered — your PRO registration is yours forever. We just stop providing the management service.",
  },
];

export default function SongwritersPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      {/* Hero */}
      <section
        className="relative pt-32 pb-20 px-4 text-center overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.18) 0%, transparent 60%), #0a0a0f",
        }}
      >
        <div className="absolute top-1/2 left-1/4 w-80 h-80 bg-[#8b5cf6]/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-[#10b981]/8 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-pulse" />
            Sync Agent pitching songs now
          </div>

          <h1 className="text-5xl md:text-7xl font-black text-[#f9fafb] mb-4 leading-tight">
            Your Songs.{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Your Rights.
            </span>
            <br />
            Your Income.
          </h1>

          <p className="text-lg md:text-xl text-[#9ca3af] max-w-3xl mx-auto mb-10">
            List your catalog. Find co-write partners. Sell publishing points.
            Get placed by 21 AI agents working for you.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Link
              href="/songwriters/register"
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-base px-8 py-4 rounded-xl transition-colors w-full sm:w-auto text-center"
              style={{ boxShadow: "0 0 24px rgba(139,92,246,0.4)" }}
            >
              List My Catalog
            </Link>
            <Link
              href="/songwriters/cowrite"
              className="border border-[#8b5cf6] text-[#8b5cf6] hover:bg-[#8b5cf6]/10 font-bold text-base px-8 py-4 rounded-xl transition-colors w-full sm:w-auto text-center"
            >
              Find Co-write Partners
            </Link>
          </div>

          {/* Stat row */}
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
            {STATS.map((s, i) => (
              <span key={s.label} className="flex items-center gap-2">
                <span className="text-[#f9fafb] font-bold">{s.value}</span>
                <span className="text-[#9ca3af]">{s.label}</span>
                {i < STATS.length - 1 && (
                  <span className="text-[#2a2a3a] hidden sm:inline">·</span>
                )}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-[#f9fafb] mb-3">How It Works</h2>
          <p className="text-[#9ca3af]">Four steps to a fully managed publishing setup.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {HOW_IT_WORKS.map((step, i) => (
            <div
              key={step.title}
              className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 hover:border-[#8b5cf6]/50 transition-colors"
            >
              <div className="text-3xl mb-3">{step.icon}</div>
              <div className="text-xs font-bold text-[#8b5cf6] uppercase tracking-wider mb-2">
                Step {i + 1}
              </div>
              <h3 className="text-base font-bold text-[#f9fafb] mb-2">{step.title}</h3>
              <p className="text-sm text-[#9ca3af] leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* What We Collect */}
      <section className="py-20 px-4 bg-[#13131a] border-y border-[#2a2a3a]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-black text-[#f9fafb] mb-3">
              What We Collect
            </h2>
            <p className="text-[#9ca3af]">
              Every royalty stream. Every territory. All on autopilot.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {REVENUE_SOURCES.map((src) => (
              <div
                key={src.name}
                className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-5 hover:border-[#8b5cf6]/40 transition-colors"
              >
                <div className="text-2xl mb-2">{src.icon}</div>
                <div className="font-bold text-[#f9fafb] text-sm mb-0.5">{src.name}</div>
                <div className="text-xs text-[#8b5cf6] mb-2">{src.org}</div>
                <p className="text-xs text-[#9ca3af] leading-relaxed mb-3">{src.desc}</p>
                <div className="inline-flex items-center gap-1 bg-[#10b981]/10 border border-[#10b981]/20 text-[#10b981] text-xs rounded-full px-2 py-0.5">
                  ✓ collected automatically
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Publishing Points Comparison */}
      <section className="py-20 px-4 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-[#f9fafb] mb-3">
            Rethink Your Publisher
          </h2>
          <p className="text-[#9ca3af]">
            Traditional publishers take half. Melodio takes almost nothing.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Traditional */}
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-8">
            <div className="text-sm font-bold text-[#9ca3af] uppercase tracking-wider mb-4">
              Traditional Publisher
            </div>
            <ul className="space-y-3">
              {[
                "Publisher keeps 50% of your royalties",
                "Life of copyright — no exit",
                "No transparency on deals",
                "You wait years to see money",
                "They own your publishing forever",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-[#9ca3af]">
                  <span className="text-[#ef4444] shrink-0 mt-0.5">✗</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Melodio */}
          <div
            className="bg-[#13131a] border border-[#8b5cf6]/50 rounded-xl p-8"
            style={{ boxShadow: "0 0 30px rgba(139,92,246,0.1)" }}
          >
            <div className="text-sm font-bold text-[#8b5cf6] uppercase tracking-wider mb-4">
              Melodio
            </div>
            <ul className="space-y-3">
              {[
                "You keep 95% — 8–12% admin fee only",
                "Cancel anytime, zero lock-in",
                "Full transparency dashboard",
                "Paid quarterly, track every penny",
                "Sell points to fans for upfront cash",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-[#f9fafb]">
                  <span className="text-[#10b981] shrink-0 mt-0.5">✓</span>
                  {item}
                </li>
              ))}
            </ul>
            <div className="mt-6 pt-6 border-t border-[#2a2a3a]">
              <p className="text-sm text-[#9ca3af] mb-4">Start with one song. Free.</p>
              <Link
                href="/songwriters/register"
                className="block text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-3 rounded-lg transition-colors"
              >
                Register a Song
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Active Co-write Opportunities */}
      <section className="py-20 px-4 bg-[#13131a] border-y border-[#2a2a3a]">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-10">
            <div>
              <h2 className="text-3xl font-black text-[#f9fafb] mb-2">
                Active Co-write Opportunities
              </h2>
              <p className="text-[#9ca3af] text-sm">
                Artists looking for songwriting collaborators right now.
              </p>
            </div>
            <Link
              href="/dealroom?type=seek_cowriter"
              className="text-sm text-[#8b5cf6] hover:text-[#a78bfa] font-medium transition-colors whitespace-nowrap"
            >
              View All →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {COWRITE_OPPS.map((opp) => (
              <div
                key={opp.seeker}
                className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-6 hover:border-[#8b5cf6]/40 transition-colors"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-[#13131a] border border-[#2a2a3a] rounded-full flex items-center justify-center text-xl">
                    {opp.avatar}
                  </div>
                  <div>
                    <div className="font-semibold text-[#f9fafb] text-sm">{opp.seeker}</div>
                    <div className="text-xs text-[#9ca3af]">{opp.genre}</div>
                  </div>
                </div>
                <p className="text-sm text-[#9ca3af] mb-4 leading-relaxed">{opp.need}</p>
                <div className="flex items-center justify-between">
                  <span
                    className="text-xs font-semibold px-2.5 py-1 rounded-full"
                    style={{
                      background: `${opp.color}20`,
                      color: opp.color,
                      border: `1px solid ${opp.color}30`,
                    }}
                  >
                    {opp.offer}
                  </span>
                  <span className="text-xs text-[#9ca3af]">Due: {opp.deadline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Songwriter Tiers */}
      <section className="py-20 px-4 max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-black text-[#f9fafb] mb-3">
            Songwriter Plans
          </h2>
          <p className="text-[#9ca3af]">Start free. Upgrade as your catalog grows.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`bg-[#13131a] rounded-xl p-8 flex flex-col relative ${
                tier.popular ? "border-2 border-[#8b5cf6]" : "border border-[#2a2a3a]"
              }`}
              style={tier.popular ? { boxShadow: "0 0 30px rgba(139,92,246,0.15)" } : {}}
            >
              {tier.popular && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-[#8b5cf6] text-white text-xs font-bold px-4 py-1 rounded-full">
                  MOST POPULAR
                </div>
              )}
              <div className="font-black text-xl text-[#f9fafb] mb-1">{tier.name}</div>
              <div className="text-3xl font-black mb-6" style={{ color: tier.color }}>
                {tier.price}
              </div>
              <ul className="space-y-3 flex-1 mb-8">
                {tier.features.map((feat) => (
                  <li key={feat} className="flex items-start gap-2 text-sm text-[#9ca3af]">
                    <span className="text-[#10b981] shrink-0">✓</span>
                    {feat}
                  </li>
                ))}
              </ul>
              <Link
                href="/songwriters/register"
                className={`block text-center font-semibold text-sm px-5 py-3 rounded-lg transition-colors ${
                  tier.popular
                    ? "bg-[#8b5cf6] hover:bg-[#7c3aed] text-white"
                    : "border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb]"
                }`}
              >
                {tier.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-4 bg-[#13131a] border-y border-[#2a2a3a]">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black text-[#f9fafb] mb-3">FAQ</h2>
          </div>
          <div className="space-y-4">
            {FAQS.map((faq) => (
              <div
                key={faq.q}
                className="bg-[#0a0a0f] border border-[#2a2a3a] rounded-xl p-6"
              >
                <div className="font-semibold text-[#f9fafb] mb-2">{faq.q}</div>
                <p className="text-sm text-[#9ca3af] leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="py-24 px-4 text-center max-w-3xl mx-auto">
        <h2 className="text-3xl md:text-4xl font-black text-[#f9fafb] mb-4">
          Start protecting your songs today.{" "}
          <span
            style={{
              background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Free for your first 5.
          </span>
        </h2>
        <p className="text-[#9ca3af] mb-8">
          Register now and we handle ASCAP/BMI/MLC registration automatically.
        </p>
        <Link
          href="/songwriters/register"
          className="inline-block bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-lg px-12 py-5 rounded-xl transition-colors"
          style={{ boxShadow: "0 0 30px rgba(139,92,246,0.4)" }}
        >
          Register My Songs
        </Link>
      </section>
    </main>
  );
}
