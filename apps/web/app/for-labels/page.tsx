import type { Metadata } from "next";
import Link from "next/link";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Melodio for Labels — White-Label AI Music Infrastructure",
  description:
    "White-label Melodio Points infrastructure for external labels. AI-powered analytics, automated royalty collection, and a Points Store for your roster.",
};

const FEATURES = [
  {
    icon: "💎",
    title: "Points Store for Your Roster",
    desc: "Give your artists their own Melodio Points marketplace. Fans buy fractional royalty ownership — artists raise capital while deepening fan engagement.",
  },
  {
    icon: "📊",
    title: "AI-Powered Analytics",
    desc: "Real-time dashboards tracking streams, revenue, social velocity, playlist placements, and growth trajectories across your entire roster — powered by 23 specialized AI agents.",
  },
  {
    icon: "💰",
    title: "Automated Royalty Collection",
    desc: "We collect from 60+ PROs across 150+ countries automatically. Performance, mechanical, sync, YouTube Content ID, and international royalties — all flowing into one transparent ledger.",
  },
  {
    icon: "🤖",
    title: "AI Agent Suite",
    desc: "Access Melodio's full 23-agent system: marketing, distribution, PR, legal, analytics, sync licensing, and more. Each agent is purpose-built for music industry operations.",
  },
  {
    icon: "🔗",
    title: "API-First Integration",
    desc: "Plug Melodio infrastructure into your existing systems via our REST API. Catalog management, royalty reporting, and fan analytics — all programmatically accessible.",
  },
  {
    icon: "🛡️",
    title: "White-Label Branding",
    desc: "Your label, your brand. The Points Store, analytics dashboards, and artist portals are fully white-labelable with your logo, colors, and domain.",
  },
];

const STATS = [
  { value: "23", label: "AI Agents", sub: "Purpose-built for music" },
  { value: "60+", label: "PROs", sub: "Worldwide collection" },
  { value: "150+", label: "DSPs", sub: "Global distribution" },
  { value: "24/7", label: "Operations", sub: "Never sleeps" },
];

export default function ForLabelsPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-20 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-[#8b5cf6]/6 rounded-full blur-3xl" />
          <div className="absolute top-20 right-1/4 w-[400px] h-[400px] bg-[#10b981]/5 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#8b5cf6] rounded-full animate-pulse" />
            B2B Partnerships
          </div>
          <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-6">
            Melodio{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              for Labels
            </span>
          </h1>
          <p className="text-[#9ca3af] text-xl leading-relaxed max-w-2xl mx-auto">
            White-label AI music infrastructure for forward-thinking labels.
            Give your roster autonomous career management, fan-powered funding,
            and global royalty collection — under your brand.
          </p>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-5xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map((s) => (
            <div
              key={s.label}
              className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-6 text-center"
            >
              <div className="text-3xl md:text-4xl font-black text-[#8b5cf6] mb-1">
                {s.value}
              </div>
              <div className="text-sm font-semibold text-[#f9fafb]">
                {s.label}
              </div>
              <div className="text-xs text-[#6b7280] mt-0.5">{s.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 pb-20">
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-black mb-3">
            Everything Your Label Needs
          </h2>
          <p className="text-[#9ca3af] text-lg max-w-xl mx-auto">
            Plug into Melodio&apos;s autonomous infrastructure and give your
            artists an unfair advantage.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-7 hover:border-[#8b5cf6]/30 transition-colors"
            >
              <div className="text-3xl mb-4">{f.icon}</div>
              <h3 className="text-lg font-bold text-[#f9fafb] mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-[#9ca3af] leading-relaxed">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works (brief) */}
      <section className="bg-[#13131a] border-y border-[#2a2a3a] py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-black mb-12">How the Partnership Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                num: "01",
                title: "Discovery Call",
                desc: "We learn about your roster, catalog size, and goals. We tailor the infrastructure to your workflow.",
              },
              {
                num: "02",
                title: "White-Label Setup",
                desc: "We deploy your branded Points Store, analytics dashboard, and artist portals within 2 weeks.",
              },
              {
                num: "03",
                title: "Go Live",
                desc: "Your artists get autonomous AI management. Your fans get investment access. You get full visibility.",
              },
            ].map((step) => (
              <div key={step.num} className="text-center">
                <div className="text-4xl font-black text-[#8b5cf6]/20 mb-3">
                  {step.num}
                </div>
                <h3 className="text-lg font-bold mb-2">{step.title}</h3>
                <p className="text-sm text-[#9ca3af] leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 py-24">
        <div
          className="max-w-4xl mx-auto rounded-3xl border border-[#2a2a3a] p-12 text-center"
          style={{
            background: "linear-gradient(135deg, #13131a 0%, #1a1128 100%)",
          }}
        >
          <h2 className="text-4xl font-black mb-4">
            Let&apos;s Build Together
          </h2>
          <p className="text-[#9ca3af] text-xl mb-10 max-w-xl mx-auto">
            Ready to give your roster the power of 23 AI agents? Reach out and
            let&apos;s explore what Melodio can do for your label.
          </p>
          <a
            href="mailto:partnerships@melodio.io"
            className="inline-flex items-center gap-2 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-8 py-4 rounded-xl transition-colors text-lg"
            style={{ boxShadow: "0 0 30px rgba(139,92,246,0.4)" }}
          >
            Contact Us →
          </a>
          <p className="text-sm text-[#6b7280] mt-4">
            partnerships@melodio.io
          </p>
        </div>
      </section>
    </main>
  );
}
