"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Navbar from "../../../components/Navbar";
import { formatNumber, tierBadge } from "../../../lib/api";
import type { Artist } from "../../../lib/api";

const MOCK_ARTISTS: Artist[] = [
  {
    id: "1",
    name: "Nova Vex",
    genre: "Afrobeats",
    tier: "diamond",
    echoScore: 94,
    monthlyListeners: 284000,
    totalStreams: 4200000,
    pointsAvailable: 3,
    pointsTotal: 15,
    pricePerPoint: 250,
    growthPct: 34,
  },
  {
    id: "2",
    name: "Lyra Bloom",
    genre: "Alt R&B",
    tier: "fire",
    echoScore: 87,
    monthlyListeners: 142000,
    totalStreams: 1800000,
    pointsAvailable: 8,
    pointsTotal: 20,
    pricePerPoint: 150,
    growthPct: 22,
  },
  {
    id: "3",
    name: "Khai Dusk",
    genre: "Trap Soul",
    tier: "fire",
    echoScore: 82,
    monthlyListeners: 98000,
    totalStreams: 950000,
    pointsAvailable: 12,
    pointsTotal: 25,
    pricePerPoint: 100,
    growthPct: 18,
  },
  {
    id: "4",
    name: "Zara Sol",
    genre: "Pop",
    tier: "star",
    echoScore: 76,
    monthlyListeners: 67000,
    totalStreams: 620000,
    pointsAvailable: 20,
    pointsTotal: 30,
    pricePerPoint: 75,
    growthPct: 11,
  },
  {
    id: "5",
    name: "Melo Cipher",
    genre: "Hip-Hop",
    tier: "fire",
    echoScore: 89,
    monthlyListeners: 210000,
    totalStreams: 3100000,
    pointsAvailable: 5,
    pointsTotal: 18,
    pricePerPoint: 200,
    growthPct: 28,
  },
  {
    id: "6",
    name: "Indie Haze",
    genre: "Indie Pop",
    tier: "star",
    echoScore: 71,
    monthlyListeners: 41000,
    totalStreams: 380000,
    pointsAvailable: 25,
    pointsTotal: 35,
    pricePerPoint: 50,
    growthPct: 9,
  },
];

const ARTIST_COLORS = ["#8b5cf6", "#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#14b8a6"];

export default function PointDropPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const artist = MOCK_ARTISTS.find((a) => a.id === id) ?? MOCK_ARTISTS[0];
  const colorIndex = MOCK_ARTISTS.findIndex((a) => a.id === id);
  const color = ARTIST_COLORS[colorIndex % ARTIST_COLORS.length];

  const [qty, setQty] = useState(1);
  const [purchased, setPurchased] = useState(false);

  const aiConfidence = artist.echoScore;
  const pctSold = Math.round(((artist.pointsTotal - artist.pointsAvailable) / artist.pointsTotal) * 100);

  const estimates = [
    { scenario: "Conservative", perPoint: Math.round(artist.pricePerPoint * 0.08), color: "#9ca3af", pct: "8%" },
    { scenario: "Expected", perPoint: Math.round(artist.pricePerPoint * 0.18), color: "#10b981", pct: "18%" },
    { scenario: "Optimistic", perPoint: Math.round(artist.pricePerPoint * 0.34), color: "#f59e0b", pct: "34%" },
  ];

  const similar = MOCK_ARTISTS.filter((a) => a.id !== artist.id).slice(0, 3);

  function handleBuy() {
    setPurchased(true);
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 pt-24 pb-20">
        {/* Back */}
        <Link href="/points" className="inline-flex items-center gap-2 text-sm text-[#9ca3af] hover:text-[#f9fafb] transition-colors mb-8">
          <svg width="16" height="16" fill="none" viewBox="0 0 16 16">
            <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          Back to Points Store
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left — Artist Info */}
          <div className="lg:col-span-3 space-y-6">

            {/* Hero artwork */}
            <div
              className="rounded-2xl overflow-hidden h-72 relative flex items-end p-8"
              style={{
                background: `linear-gradient(135deg, ${color}40 0%, #0a0a0f 100%)`,
                border: `1px solid ${color}40`,
              }}
            >
              <div className="absolute inset-0 flex items-center justify-center text-9xl opacity-15 select-none pointer-events-none">
                🎵
              </div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{tierBadge(artist.tier)}</span>
                  <span
                    className="text-sm font-bold px-3 py-1 rounded-full"
                    style={{ background: `${color}30`, color }}
                  >
                    {artist.genre}
                  </span>
                </div>
                <h1 className="text-4xl font-black text-[#f9fafb]">{artist.name}</h1>
              </div>
              <div className="absolute top-5 right-5 bg-[#0a0a0f]/80 backdrop-blur text-[#f9fafb] font-bold px-3 py-1.5 rounded-lg border border-[#2a2a3a] text-sm">
                ⚡ {aiConfidence} ECHO Score
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Monthly Listeners", value: formatNumber(artist.monthlyListeners) },
                { label: "Total Streams", value: formatNumber(artist.totalStreams) },
                { label: "Monthly Growth", value: `+${artist.growthPct}%` },
              ].map((s) => (
                <div key={s.label} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-4 text-center">
                  <div className="text-white font-bold text-xl">{s.value}</div>
                  <div className="text-[#9ca3af] text-xs mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            {/* AI Confidence Score */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-[#f9fafb]">AI Confidence Score</h3>
                <span className="text-2xl font-black" style={{ color }}>{aiConfidence}/100</span>
              </div>
              <div className="w-full h-3 bg-[#2a2a3a] rounded-full overflow-hidden mb-3">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${aiConfidence}%`, background: `linear-gradient(90deg, ${color}, #10b981)` }}
                />
              </div>
              <p className="text-sm text-[#9ca3af]">
                Based on streaming trajectory, social growth, genre momentum, and playlist algorithmic fit. {aiConfidence}+ indicates strong breakout potential.
              </p>
            </div>

            {/* Points availability */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-[#f9fafb]">Points Remaining</h3>
                <span className="text-[#f9fafb] font-bold">{artist.pointsAvailable} of {artist.pointsTotal}</span>
              </div>
              <div className="w-full h-3 bg-[#2a2a3a] rounded-full overflow-hidden mb-2">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${pctSold}%`, background: color }}
                />
              </div>
              <div className="flex justify-between text-xs text-[#9ca3af]">
                <span>{pctSold}% sold</span>
                <span>{artist.pointsAvailable} remaining</span>
              </div>
            </div>

            {/* Earnings Estimate */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h3 className="font-bold text-[#f9fafb] mb-4">Earnings Estimate — Per Point / Year</h3>
              <div className="space-y-3">
                {estimates.map((e) => (
                  <div key={e.scenario} className="flex items-center justify-between p-3 bg-[#0a0a0f] rounded-lg border border-[#2a2a3a]">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full" style={{ background: e.color }} />
                      <span className="text-sm font-medium text-[#f9fafb]">{e.scenario}</span>
                      <span className="text-xs text-[#9ca3af]">({e.pct} ROI)</span>
                    </div>
                    <span className="font-bold" style={{ color: e.color }}>${e.perPoint}/pt</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[#9ca3af] mt-4">
                Estimates are projections based on current streaming data and growth trends. Not financial advice. Royalties depend on actual performance.
              </p>
            </div>

            {/* How it works */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h3 className="font-bold text-[#f9fafb] mb-5">How It Works</h3>
              <div className="space-y-5">
                {[
                  { step: "1", title: "Buy Points", desc: "Each point represents fractional royalty ownership in the artist's current and future releases on ECHO." },
                  { step: "2", title: "Earn Monthly", desc: "Streaming royalties are calculated monthly and distributed directly to point holders based on ownership percentage." },
                  { step: "3", title: "Hold or Trade", desc: "Points are locked for 12 months from purchase. After that, they're freely tradeable on the ECHO marketplace." },
                ].map((item) => (
                  <div key={item.step} className="flex items-start gap-4">
                    <div className="w-7 h-7 rounded-full bg-[#8b5cf6]/20 text-[#8b5cf6] text-sm font-bold flex items-center justify-center shrink-0">
                      {item.step}
                    </div>
                    <div>
                      <div className="font-semibold text-[#f9fafb] text-sm">{item.title}</div>
                      <div className="text-xs text-[#9ca3af] mt-0.5 leading-relaxed">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right — Buy form */}
          <div className="lg:col-span-2">
            <div className="sticky top-24">
              {purchased ? (
                <div className="bg-[#13131a] rounded-2xl border border-[#10b981]/50 p-8 text-center" style={{ boxShadow: "0 0 30px rgba(16,185,129,0.2)" }}>
                  <div className="text-5xl mb-4">🎉</div>
                  <h3 className="text-xl font-black text-[#f9fafb] mb-2">Points Secured!</h3>
                  <p className="text-[#9ca3af] text-sm mb-6">
                    You now own {qty} ECHO {qty === 1 ? "Point" : "Points"} in {artist.name}. Royalties will flow monthly.
                  </p>
                  <div className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-4 mb-6">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-[#9ca3af]">Points purchased</span>
                      <span className="font-bold text-[#f9fafb]">{qty}</span>
                    </div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-[#9ca3af]">Total invested</span>
                      <span className="font-bold text-[#10b981]">${qty * artist.pricePerPoint}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[#9ca3af]">Expected first payout</span>
                      <span className="font-bold text-[#f9fafb]">Apr 1, 2026</span>
                    </div>
                  </div>
                  <Link href="/points" className="block w-full text-center border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] font-semibold text-sm px-4 py-2.5 rounded-lg transition-colors">
                    Browse More Drops
                  </Link>
                </div>
              ) : (
                <div className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-6">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold text-[#f9fafb] text-lg">Buy Points</h3>
                    <span className="text-xs text-[#9ca3af]">{artist.pointsAvailable} left</span>
                  </div>
                  <div className="text-[#9ca3af] text-sm mb-6">${artist.pricePerPoint} per point</div>

                  {/* Quantity slider */}
                  <div className="mb-6">
                    <div className="flex justify-between text-sm mb-2">
                      <label className="text-[#9ca3af]">Quantity</label>
                      <span className="font-bold text-[#f9fafb]">{qty}</span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={Math.min(artist.pointsAvailable, 10)}
                      value={qty}
                      onChange={(e) => setQty(Number(e.target.value))}
                      className="w-full accent-[#8b5cf6]"
                    />
                    <div className="flex justify-between text-xs text-[#9ca3af] mt-1">
                      <span>1</span>
                      <span>{Math.min(artist.pointsAvailable, 10)}</span>
                    </div>
                  </div>

                  {/* Price summary */}
                  <div className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-4 mb-5 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-[#9ca3af]">{qty} × ${artist.pricePerPoint}</span>
                      <span className="text-[#f9fafb] font-semibold">${qty * artist.pricePerPoint}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[#9ca3af]">Expected annual yield</span>
                      <span className="text-[#10b981] font-semibold">
                        ${qty * Math.round(artist.pricePerPoint * 0.18)}/yr
                      </span>
                    </div>
                    <div className="border-t border-[#2a2a3a] pt-2 flex justify-between font-bold">
                      <span className="text-[#9ca3af]">Total</span>
                      <span className="text-[#f9fafb] text-lg">${qty * artist.pricePerPoint}</span>
                    </div>
                  </div>

                  <button
                    onClick={handleBuy}
                    className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-base px-4 py-3.5 rounded-xl transition-colors duration-200"
                    style={{ boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
                  >
                    Buy {qty} {qty === 1 ? "Point" : "Points"} — ${qty * artist.pricePerPoint}
                  </button>

                  <p className="text-xs text-[#9ca3af] text-center mt-4 leading-relaxed">
                    By purchasing you agree to ECHO&apos;s point holder terms. 12-month holding period applies.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Similar Drops */}
        <section className="mt-20">
          <h2 className="text-2xl font-black text-[#f9fafb] mb-6">Similar Drops</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {similar.map((a, i) => (
              <Link
                key={a.id}
                href={`/points/${a.id}`}
                className="bg-[#13131a] rounded-xl border border-[#2a2a3a] hover:border-[#8b5cf6] transition-colors p-5 flex items-center gap-4"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                  style={{ background: `${ARTIST_COLORS[i % ARTIST_COLORS.length]}20` }}
                >
                  🎵
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-semibold text-[#f9fafb] truncate">{a.name}</span>
                    <span>{tierBadge(a.tier)}</span>
                  </div>
                  <div className="text-xs text-[#9ca3af]">{a.genre} · ${a.pricePerPoint}/pt</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-bold text-[#f9fafb]">⚡ {a.echoScore}</div>
                  <div className="text-xs text-[#10b981]">+{a.growthPct}%</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
