"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../components/Navbar";

const MOCK_TRENDING = [
  {
    id: "nova-vex",
    name: "Nova Vex",
    genre: "Dark R&B",
    momentum_score: 91,
    tier: "🔥",
    tier_label: "🔥 Breaking",
    tier_color: "#ef4444",
    points_available: 500,
    price_per_point: 250,
    dimension_scores: { stream_growth: 88, social_velocity: 92, sync_heat: 95, press_momentum: 85, ar_score: 90 },
  },
  {
    id: "lyra-bloom",
    name: "Lyra Bloom",
    genre: "Indie Pop",
    momentum_score: 84,
    tier: "⚡",
    tier_label: "⚡ Rising",
    tier_color: "#8b5cf6",
    points_available: 1200,
    price_per_point: 180,
    dimension_scores: { stream_growth: 82, social_velocity: 87, sync_heat: 80, press_momentum: 78, ar_score: 85 },
  },
  {
    id: "melo-cipher",
    name: "Melo Cipher",
    genre: "Hip-Hop",
    momentum_score: 78,
    tier: "⚡",
    tier_label: "⚡ Rising",
    tier_color: "#8b5cf6",
    points_available: 800,
    price_per_point: 150,
    dimension_scores: { stream_growth: 75, social_velocity: 80, sync_heat: 72, press_momentum: 70, ar_score: 82 },
  },
  {
    id: "khai-dusk",
    name: "Khai Dusk",
    genre: "Alt Soul",
    momentum_score: 73,
    tier: "⚡",
    tier_label: "⚡ Rising",
    tier_color: "#8b5cf6",
    points_available: 600,
    price_per_point: 120,
    dimension_scores: { stream_growth: 70, social_velocity: 75, sync_heat: 68, press_momentum: 65, ar_score: 78 },
  },
  {
    id: "zara-sol",
    name: "Zara Sol",
    genre: "Afrobeats",
    momentum_score: 69,
    tier: "📈",
    tier_label: "📈 Growing",
    tier_color: "#10b981",
    points_available: 2000,
    price_per_point: 80,
    dimension_scores: { stream_growth: 65, social_velocity: 72, sync_heat: 60, press_momentum: 58, ar_score: 75 },
  },
  {
    id: "echo-static",
    name: "Echo Static",
    genre: "Electronic",
    momentum_score: 65,
    tier: "📈",
    tier_label: "📈 Growing",
    tier_color: "#10b981",
    points_available: 1500,
    price_per_point: 60,
    dimension_scores: { stream_growth: 62, social_velocity: 68, sync_heat: 55, press_momentum: 52, ar_score: 70 },
  },
  {
    id: "river-kane",
    name: "River Kane",
    genre: "Folk Pop",
    momentum_score: 58,
    tier: "📈",
    tier_label: "📈 Growing",
    tier_color: "#10b981",
    points_available: 3000,
    price_per_point: 40,
    dimension_scores: { stream_growth: 55, social_velocity: 60, sync_heat: 48, press_momentum: 45, ar_score: 65 },
  },
  {
    id: "jade-vortex",
    name: "Jade Vortex",
    genre: "Neo Soul",
    momentum_score: 52,
    tier: "👀",
    tier_label: "👀 Watch List",
    tier_color: "#f59e0b",
    points_available: 5000,
    price_per_point: 25,
    dimension_scores: { stream_growth: 48, social_velocity: 55, sync_heat: 40, press_momentum: 38, ar_score: 60 },
  },
];

const TIMEFRAMES = ["7 Days", "30 Days", "90 Days"] as const;

const SIGNALS = [
  { icon: "🎵", label: "Stream Growth", pct: "35%", desc: "Monthly listener trajectory" },
  { icon: "📱", label: "Social Velocity", pct: "25%", desc: "Cross-platform follower momentum" },
  { icon: "🎬", label: "Sync Heat", pct: "20%", desc: "Film, TV & ad placements" },
  { icon: "📰", label: "Press Momentum", pct: "10%", desc: "Reviews, features, interviews" },
  { icon: "🎯", label: "A&R Score", pct: "10%", desc: "Melodio internal talent assessment" },
];

function SignalBars({ scores }: { scores: Record<string, number> }) {
  const bars = [
    { key: "stream_growth", color: "#8b5cf6" },
    { key: "social_velocity", color: "#8b5cf6" },
    { key: "sync_heat", color: "#10b981" },
    { key: "press_momentum", color: "#10b981" },
    { key: "ar_score", color: "#f59e0b" },
  ];
  return (
    <div className="flex gap-1 items-end h-6">
      {bars.map((b) => (
        <div key={b.key} className="flex flex-col justify-end w-3 h-6 rounded-sm overflow-hidden bg-[#1e1e2e]">
          <div
            style={{ height: `${scores[b.key] || 0}%`, backgroundColor: b.color }}
            className="w-full rounded-sm transition-all"
          />
        </div>
      ))}
    </div>
  );
}

function ArtistCard({ artist }: { artist: typeof MOCK_TRENDING[0] }) {
  return (
    <div className="relative bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 hover:border-[#8b5cf6]/50 transition-all duration-200 group">
      {/* Tier badge */}
      <div
        className="absolute top-3 right-3 text-xs font-bold px-2 py-1 rounded-full"
        style={{ color: artist.tier_color, backgroundColor: `${artist.tier_color}20` }}
      >
        {artist.tier_label}
      </div>

      {/* Artist info */}
      <div className="mb-3">
        <div className="text-[#f9fafb] font-bold text-lg leading-tight pr-20">{artist.name}</div>
        <div className="text-[#9ca3af] text-xs mt-0.5">{artist.genre}</div>
      </div>

      {/* Momentum score */}
      <div className="flex items-baseline gap-1 mb-3">
        <span className="font-black text-3xl" style={{ color: artist.tier_color }}>
          {artist.momentum_score}
        </span>
        <span className="text-[#6b7280] text-xs">/ 100 momentum</span>
      </div>

      {/* Signal bars */}
      <div className="mb-4">
        <SignalBars scores={artist.dimension_scores} />
        <div className="text-[#6b7280] text-[10px] mt-1">stream · social · sync · press · A&R</div>
      </div>

      {/* Points info */}
      <div className="flex items-center justify-between text-xs text-[#9ca3af] mb-4">
        <span>{artist.points_available.toLocaleString()} pts available</span>
        <span className="text-[#f9fafb] font-semibold">${artist.price_per_point}/pt</span>
      </div>

      {/* CTAs */}
      <div className="flex gap-2">
        <Link
          href="/points"
          className="flex-1 text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-xs font-semibold py-2 px-3 rounded-lg transition-colors"
        >
          Buy Points
        </Link>
        <button className="flex-1 text-center border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb] text-xs font-semibold py-2 px-3 rounded-lg transition-colors">
          Watch
        </button>
      </div>
    </div>
  );
}

export default function DiscoverPage() {
  const [activeTab, setActiveTab] = useState<string>("7 Days");

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-16 px-6 md:px-10 max-w-6xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 rounded-full px-4 py-1.5 text-[#8b5cf6] text-xs font-semibold mb-6">
          Artist discovery only — not financial advice
        </div>
        <h1 className="text-4xl md:text-6xl font-black tracking-tight mb-4">
          Discover Who&apos;s{" "}
          <span className="text-[#ef4444]">Breaking</span>
        </h1>
        <p className="text-[#9ca3af] text-lg md:text-xl max-w-2xl mx-auto mb-2">
          Our AI tracks streams, sync placements, press momentum, and social growth to surface artists
          before they blow up. Back them early. Earn royalties as they grow.
        </p>
      </section>

      {/* Trending Section */}
      <section className="px-6 md:px-10 max-w-6xl mx-auto mb-20">
        {/* Timeframe tabs */}
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-[#f9fafb]">Trending Now</h2>
          <div className="flex gap-1 bg-[#13131a] border border-[#2a2a3a] rounded-lg p-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setActiveTab(tf)}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${
                  activeTab === tf
                    ? "bg-[#8b5cf6] text-white"
                    : "text-[#9ca3af] hover:text-[#f9fafb]"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Artist cards grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {MOCK_TRENDING.map((artist) => (
            <ArtistCard key={artist.id} artist={artist} />
          ))}
        </div>
      </section>

      {/* How We Score section */}
      <section className="px-6 md:px-10 max-w-6xl mx-auto mb-20">
        <h2 className="text-xl font-bold text-[#f9fafb] mb-2">How We Score Artists</h2>
        <p className="text-[#6b7280] text-sm mb-8">
          The Melodio Momentum Score combines 5 signals, updated continuously.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {SIGNALS.map((s) => (
            <div
              key={s.label}
              className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4 hover:border-[#8b5cf6]/40 transition-colors"
            >
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="text-[#f9fafb] font-semibold text-sm mb-1">{s.label}</div>
              <div className="text-[#8b5cf6] font-black text-lg mb-1">{s.pct}</div>
              <div className="text-[#6b7280] text-xs">{s.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Personalized section */}
      <section className="px-6 md:px-10 max-w-6xl mx-auto mb-20">
        <div className="bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-8 text-center">
          <div className="text-3xl mb-3">🎧</div>
          <h2 className="text-xl font-bold text-[#f9fafb] mb-2">Your Picks</h2>
          <p className="text-[#9ca3af] text-sm mb-6 max-w-md mx-auto">
            Sign in to get personalized artist recommendations based on your taste and backing history.
          </p>
          <Link
            href="/dashboard"
            className="inline-block bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-2.5 rounded-lg transition-colors"
          >
            Sign In for Personalized Picks
          </Link>
        </div>
      </section>

      {/* Footer disclaimer */}
      <footer className="px-6 md:px-10 max-w-6xl mx-auto pb-16">
        <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 text-center">
          <p className="text-[#6b7280] text-xs leading-relaxed max-w-2xl mx-auto">
            Melodio artist discovery is for informational purposes only. Buying Melodio Points is not an
            investment. Past royalty performance of any artist does not guarantee future earnings.
            Melodio Points are not securities.
          </p>
        </div>
      </footer>
    </div>
  );
}
