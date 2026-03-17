"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

const SECTIONS = [
  {
    id: "artists",
    title: "For Artists",
    emoji: "🎤",
    color: "#8b5cf6",
    tagline: "Submit your music. Keep 100% ownership.",
    steps: [
      { icon: "📤", title: "Submit Your Demo", desc: "Upload your music and our A&R Agent reviews it within 48 hours. No gatekeepers, no politics." },
      { icon: "✅", title: "Get Signed (per song)", desc: "If selected, you get a per-song deal. No long-term contracts. You keep all publishing — we take 10% admin fee only." },
      { icon: "💎", title: "Drop Melodio Points", desc: "Offer fans fractional royalty ownership in your releases. Raise capital while building your superfan base." },
      { icon: "💰", title: "Earn Every Month", desc: "Royalties flow to you and your point holders monthly. Full transparency — every stream, every dollar tracked." },
    ],
    cta: { label: "Submit Your Demo", href: "/submit" },
  },
  {
    id: "fans",
    title: "For Fans",
    emoji: "🎧",
    color: "#10b981",
    tagline: "Own a piece of the music. Earn as it streams.",
    steps: [
      { icon: "🔍", title: "Discover Rising Artists", desc: "Our AI tracks stream growth, sync placements, social velocity, and press momentum to surface artists before they blow up." },
      { icon: "💎", title: "Buy Melodio Points", desc: "Purchase fractional royalty ownership in an artist's release catalog. Each point earns a share of streaming royalties." },
      { icon: "📈", title: "Earn Monthly Royalties", desc: "As streams flow in, royalties are distributed proportionally to all point holders on the 1st of each month." },
      { icon: "🔄", title: "Trade or Hold", desc: "After a 12-month holding period, your points are freely tradeable on the Melodio marketplace." },
    ],
    cta: { label: "Browse Points Store", href: "/points" },
  },
  {
    id: "producers",
    title: "For Producers",
    emoji: "🎛️",
    color: "#f59e0b",
    tagline: "Upload beats. Get discovered. Earn fair.",
    steps: [
      { icon: "⬆️", title: "Upload Your Beats", desc: "List beats with genre tags, BPM, key, and license type. Our system surfaces them to matched artists automatically." },
      { icon: "🤝", title: "Get Matched with Artists", desc: "Our AI matches your beats to compatible signed artists. Direct introductions — no cold outreach needed." },
      { icon: "📄", title: "Transparent Licensing", desc: "Set your own license terms: exclusive, non-exclusive, lease. Smart contracts handle everything automatically." },
      { icon: "💸", title: "Earn on Every Use", desc: "Get paid on placement and earn ongoing royalties when tracks using your beats are streamed." },
    ],
    cta: { label: "List Your Beats", href: "/dealroom" },
  },
  {
    id: "songwriters",
    title: "For Songwriters",
    emoji: "✍️",
    color: "#3b82f6",
    tagline: "Register songs. Collect worldwide. Find co-writers.",
    steps: [
      { icon: "📋", title: "Register Your Songs", desc: "Register your compositions and collect performance, mechanical, sync, and digital royalties from 60+ PROs worldwide." },
      { icon: "💎", title: "Offer Publishing Points", desc: "Monetize your catalog now by offering fans fractional ownership of your publishing royalties. You keep 100% — fans earn alongside you." },
      { icon: "🤝", title: "Find Co-Writers", desc: "Browse the co-write marketplace to find artists and songwriters who match your style. Transparent 50/50 splits, no haggling." },
      { icon: "💰", title: "Collect Globally", desc: "We handle collection from 60+ PROs. Monthly payouts in your local currency, full audit trail." },
    ],
    cta: { label: "Start for Free", href: "/songwriters" },
  },
];

const FAQS = [
  {
    q: "What are Melodio Points?",
    a: "Melodio Points represent fractional royalty ownership in an artist's release catalog. When you buy points, you own a percentage of streaming royalties from their music. As the artist streams more, you earn more — paid monthly.",
  },
  {
    q: "Is there any lock-in period?",
    a: "Points are held for 12 months from purchase date. After that, they are freely tradeable on the Melodio marketplace. We believe in transparency — there are no hidden lock-up extensions.",
  },
  {
    q: "How does Melodio make money?",
    a: "We charge artists a 10% admin fee on royalties collected, and a 5% marketplace fee on point trades. That's it. No hidden fees, no per-song fees, no long-term contract premiums.",
  },
  {
    q: "What rights do artists give up?",
    a: "None of the important ones. Artists keep 100% of their publishing rights and masters. Point holders get a revenue share only — they don't gain any creative control or catalog ownership.",
  },
  {
    q: "How are royalties calculated?",
    a: "Royalties are calculated from streaming platform payouts distributed to Melodio. The revenue share is split proportionally: if you hold 2% of an artist's points and they earn $10,000 in a month, you receive $200. Simple math, transparent ledger.",
  },
  {
    q: "What happens if an artist leaves Melodio?",
    a: "All existing point agreements honor their terms regardless of whether the artist continues with Melodio. Your royalty rights are protected by contract.",
  },
  {
    q: "Can producers and songwriters use Melodio?",
    a: "Yes. Producers can list beats on the Deal Room and get matched with artists. Songwriters can register songs, collect global royalties, and offer publishing points — all through one platform.",
  },
  {
    q: "What genres does Melodio support?",
    a: "All genres. Our A&R Agent is trained on Afrobeats, Hip-Hop, R&B, Pop, Indie, Electronic, Latin, and more. If the music is good and there's momentum, we can work with it.",
  },
  {
    q: "Is Melodio available globally?",
    a: "Yes. Artists, fans, producers, and songwriters can join from anywhere. Royalty collection covers 60+ PROs across 150+ countries.",
  },
  {
    q: "How do I get started?",
    a: "It takes 3 minutes. Sign up for a free account, choose your role (Artist, Fan, Producer, or Songwriter), and you'll be directed to the right tools immediately.",
  },
];

export default function HowItWorksPage() {
  const [activeSection, setActiveSection] = useState("artists");
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const section = SECTIONS.find((s) => s.id === activeSection)!;

  return (
    <main className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-16 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#8b5cf6]/8 rounded-full blur-3xl" />
          <div className="absolute top-0 right-1/4 w-96 h-96 bg-[#10b981]/8 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            Built different
          </div>
          <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-6">
            How{" "}
            <span style={{ background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Melodio
            </span>{" "}
            Works
          </h1>
          <p className="text-[#9ca3af] text-xl leading-relaxed max-w-2xl mx-auto">
            An autonomous AI music company where artists keep everything, fans earn royalties, and the music business finally makes sense.
          </p>
        </div>
      </section>

      {/* Section tabs */}
      <div className="sticky top-16 z-40 bg-[#0a0a0f]/95 backdrop-blur-lg border-b border-[#2a2a3a]">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-2 overflow-x-auto no-scrollbar">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`shrink-0 flex items-center gap-2 text-sm font-semibold px-5 py-2 rounded-full transition-all ${
                activeSection === s.id
                  ? "text-white"
                  : "bg-[#13131a] border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb]"
              }`}
              style={activeSection === s.id ? { background: s.color } : {}}
            >
              <span>{s.emoji}</span>
              {s.title}
            </button>
          ))}
        </div>
      </div>

      {/* Active section walkthrough */}
      <section className="max-w-6xl mx-auto px-4 py-20">
        <div className="text-center mb-14">
          <div className="text-5xl mb-4">{section.emoji}</div>
          <h2 className="text-4xl font-black mb-3">{section.title}</h2>
          <p className="text-[#9ca3af] text-xl">{section.tagline}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {section.steps.map((step, i) => (
            <div
              key={i}
              className="relative bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-6 hover:border-[#8b5cf6]/50 transition-all group"
            >
              <div
                className="absolute top-4 right-4 text-5xl font-black opacity-10 select-none"
                style={{ color: section.color }}
              >
                {String(i + 1).padStart(2, "0")}
              </div>
              <div className="text-3xl mb-4">{step.icon}</div>
              <h3 className="font-bold text-[#f9fafb] mb-2">{step.title}</h3>
              <p className="text-sm text-[#9ca3af] leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>

        <div className="text-center mt-10">
          <Link
            href={section.cta.href}
            className="inline-flex items-center gap-2 font-bold px-8 py-4 rounded-xl text-white transition-all"
            style={{ background: section.color, boxShadow: `0 0 24px ${section.color}40` }}
          >
            {section.cta.label} →
          </Link>
        </div>
      </section>

      {/* Revenue types */}
      <section className="bg-[#13131a] border-y border-[#2a2a3a] py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-black mb-3">Every Revenue Stream Collected</h2>
            <p className="text-[#9ca3af]">Melodio collects from all major sources automatically.</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: "📻", label: "Performance Royalties", desc: "Radio, TV, live performance" },
              { icon: "💿", label: "Mechanical Royalties", desc: "Physical and digital sales" },
              { icon: "🎬", label: "Sync Licensing", desc: "Film, TV, ads, games" },
              { icon: "▶️", label: "YouTube Content ID", desc: "Video monetization worldwide" },
              { icon: "🌊", label: "Streaming Royalties", desc: "Spotify, Apple Music, Tidal+" },
              { icon: "🌍", label: "International PROs", desc: "60+ societies, 150+ countries" },
              { icon: "🎵", label: "Cover Song Licensing", desc: "When others record your songs" },
              { icon: "🖨️", label: "Print Licensing", desc: "Sheet music and transcriptions" },
            ].map((item) => (
              <div key={item.label} className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-5 hover:border-[#8b5cf6]/40 transition-colors">
                <div className="text-2xl mb-2">{item.icon}</div>
                <div className="text-sm font-semibold text-[#f9fafb] mb-1">{item.label}</div>
                <div className="text-xs text-[#9ca3af]">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-black mb-3">Frequently Asked Questions</h2>
          <p className="text-[#9ca3af]">Straight answers to real questions.</p>
        </div>
        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div key={i} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] overflow-hidden">
              <button
                onClick={() => setOpenFaq(openFaq === i ? null : i)}
                className="w-full flex items-center justify-between px-6 py-5 text-left hover:bg-[#1a1a24] transition-colors"
              >
                <span className="font-semibold text-[#f9fafb] text-sm pr-4">{faq.q}</span>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  className={`shrink-0 text-[#9ca3af] transition-transform duration-200 ${openFaq === i ? "rotate-180" : ""}`}
                >
                  <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
              {openFaq === i && (
                <div className="px-6 pb-5 text-sm text-[#9ca3af] leading-relaxed border-t border-[#2a2a3a] pt-4">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 pb-20">
        <div className="max-w-4xl mx-auto bg-[#13131a] rounded-3xl border border-[#2a2a3a] p-12 text-center" style={{ background: "linear-gradient(135deg, #13131a 0%, #1a1128 100%)" }}>
          <h2 className="text-4xl font-black mb-4">Ready to Own the Sound?</h2>
          <p className="text-[#9ca3af] text-xl mb-10 max-w-xl mx-auto">
            Join thousands of artists, fans, producers, and songwriters building the future of music together.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/signup" className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-8 py-4 rounded-xl transition-colors text-lg" style={{ boxShadow: "0 0 30px rgba(139,92,246,0.4)" }}>
              Get Started Free
            </Link>
            <Link href="/points" className="border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb] font-bold px-8 py-4 rounded-xl transition-colors text-lg">
              Browse Points Store
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
