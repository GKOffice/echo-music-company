import type { Metadata } from "next";
import Link from "next/link";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "How Melodio Works — AI-Powered Music Career Growth",
  description:
    "Submit your demo, get AI-scored in 60 seconds, and let 23 autonomous agents build your career. 60% revenue, 100% ownership, masters revert in 5 years.",
};

const SECTIONS = [
  {
    num: "01",
    icon: "📤",
    title: "Submit Your Demo",
    lines: [
      "Upload a track or paste a SoundCloud/YouTube link. Our A&R Agent scores your music in under 60 seconds — analyzing production quality, vocal performance, commercial potential, and genre fit.",
      "No gatekeepers. No waiting months for a response. Every submission gets a transparent score and honest feedback, whether you're signed or not.",
    ],
    stat: "60s",
    statLabel: "Average AI review time",
    color: "#8b5cf6",
  },
  {
    num: "02",
    icon: "🤖",
    title: "We Build Your Career",
    lines: [
      "Once signed, 23 AI agents activate simultaneously — handling distribution to 150+ DSPs, playlist pitching, social media strategy, sync licensing, PR outreach, and royalty collection from 60+ PROs worldwide.",
      "Your team never sleeps. Marketing campaigns launch at optimal times. Analytics track every stream. Legal reviews every contract. All running 24/7.",
    ],
    stat: "23",
    statLabel: "AI agents working around the clock",
    color: "#10b981",
  },
  {
    num: "03",
    icon: "💰",
    title: "You Get Paid",
    lines: [
      "Artists keep 60% of all revenue. Melodio takes 40% to fund operations — but you keep 100% of your publishing and your masters revert after 5 years. Quarterly payouts via Stripe with full transparency.",
      "No hidden recoupment. No 360 deals. No surprise deductions. Every dollar is tracked and visible on your dashboard in real time.",
    ],
    stat: "60%",
    statLabel: "Artist revenue share",
    color: "#f59e0b",
  },
  {
    num: "04",
    icon: "💎",
    title: "Melodio Points",
    lines: [
      "Let fans invest in your music through Melodio Points — fractional royalty ownership. Fans buy points, earn a share of your streaming royalties quarterly, and can trade them after a 12-month holding period.",
      "Artists raise capital from their community while building a superfan base with real financial alignment. Everyone wins when the music does.",
    ],
    stat: "12mo",
    statLabel: "Hold period, then freely tradeable",
    color: "#3b82f6",
  },
];

export default function HowItWorksPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-20 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-[#8b5cf6]/8 rounded-full blur-3xl" />
          <div className="absolute top-0 right-1/4 w-96 h-96 bg-[#10b981]/8 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            The future of music
          </div>
          <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-6">
            How{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Melodio
            </span>{" "}
            Works
          </h1>
          <p className="text-[#9ca3af] text-xl leading-relaxed max-w-2xl mx-auto">
            An autonomous AI music company. Submit your music, let 23 agents
            build your career, keep your masters, and get paid — all without a
            single middleman.
          </p>
        </div>
      </section>

      {/* Sections */}
      <section className="max-w-5xl mx-auto px-4 pb-20 space-y-16">
        {SECTIONS.map((s) => (
          <div
            key={s.num}
            className="relative bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-8 md:p-12 hover:border-opacity-60 transition-all"
            style={{ borderColor: `${s.color}30` }}
          >
            {/* Number watermark */}
            <div
              className="absolute top-6 right-8 text-7xl md:text-8xl font-black opacity-[0.06] select-none"
              style={{ color: s.color }}
            >
              {s.num}
            </div>

            <div className="flex flex-col md:flex-row gap-8 items-start">
              {/* Icon + Stat */}
              <div className="shrink-0 flex flex-col items-center gap-4">
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl"
                  style={{ background: `${s.color}15` }}
                >
                  {s.icon}
                </div>
                <div
                  className="text-center rounded-xl px-4 py-3 min-w-[100px]"
                  style={{ background: `${s.color}10`, border: `1px solid ${s.color}25` }}
                >
                  <div className="text-2xl font-black" style={{ color: s.color }}>
                    {s.stat}
                  </div>
                  <div className="text-xs text-[#9ca3af] mt-0.5 leading-tight">
                    {s.statLabel}
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 relative z-10">
                <h2 className="text-2xl md:text-3xl font-black mb-4">{s.title}</h2>
                {s.lines.map((line, i) => (
                  <p
                    key={i}
                    className="text-[#9ca3af] leading-relaxed mb-3 last:mb-0"
                  >
                    {line}
                  </p>
                ))}
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* CTA */}
      <section className="px-4 pb-24">
        <div
          className="max-w-4xl mx-auto rounded-3xl border border-[#2a2a3a] p-12 text-center"
          style={{
            background: "linear-gradient(135deg, #13131a 0%, #1a1128 100%)",
          }}
        >
          <h2 className="text-4xl font-black mb-4">Ready to Get Started?</h2>
          <p className="text-[#9ca3af] text-xl mb-10 max-w-xl mx-auto">
            Submit your demo today. If the music is there, our agents will handle
            the rest.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/submit"
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-8 py-4 rounded-xl transition-colors text-lg"
              style={{ boxShadow: "0 0 30px rgba(139,92,246,0.4)" }}
            >
              Submit Your Demo
            </Link>
            <Link
              href="/points"
              className="border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb] font-bold px-8 py-4 rounded-xl transition-colors text-lg"
            >
              Join the Waitlist
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
