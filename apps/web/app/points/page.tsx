"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../components/Navbar";
import { formatNumber, tierBadge } from "../../lib/api";
import type { Artist } from "../../lib/api";

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

const FILTERS = ["All", "Trending", "New Drops", "Afrobeats", "Hip-Hop", "R&B", "Pop", "Indie"];

const ARTIST_COLORS = [
  "#8b5cf6", "#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#14b8a6",
];

function ArtistCard({ artist, colorIndex }: { artist: Artist; colorIndex: number }) {
  const color = ARTIST_COLORS[colorIndex % ARTIST_COLORS.length];
  const pctSold = Math.round(((artist.pointsTotal - artist.pointsAvailable) / artist.pointsTotal) * 100);

  return (
    <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] hover:border-[#8b5cf6] transition-all duration-200 overflow-hidden flex flex-col group">
      {/* Artwork placeholder */}
      <div
        className="h-40 relative flex items-end p-4"
        style={{
          background: `linear-gradient(135deg, ${color}30 0%, #0a0a0f 100%)`,
        }}
      >
        <div
          className="absolute inset-0 flex items-center justify-center text-6xl opacity-20 select-none"
          aria-hidden
        >
          🎵
        </div>
        <div className="relative z-10 flex items-center gap-2">
          <span className="text-lg">{tierBadge(artist.tier)}</span>
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full"
            style={{ background: `${color}30`, color }}
          >
            {artist.genre}
          </span>
        </div>
        {/* ECHO Score chip */}
        <div className="absolute top-3 right-3 bg-[#0a0a0f]/80 backdrop-blur-sm text-[#f9fafb] text-xs font-bold px-2 py-1 rounded-lg border border-[#2a2a3a]">
          ⚡ {artist.echoScore}
        </div>
      </div>

      {/* Body */}
      <div className="p-5 flex flex-col flex-1">
        <h3 className="font-bold text-[#f9fafb] text-lg mb-1">{artist.name}</h3>
        <div className="text-sm text-[#9ca3af] mb-4">
          {formatNumber(artist.monthlyListeners)} monthly listeners
          <span className="ml-2 text-[#10b981] font-medium">+{artist.growthPct}%</span>
        </div>

        {/* Points progress */}
        <div className="mb-4">
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-[#9ca3af]">Points Available</span>
            <span className="text-[#f9fafb] font-semibold">{artist.pointsAvailable} / {artist.pointsTotal}</span>
          </div>
          <div className="w-full h-1.5 bg-[#2a2a3a] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${pctSold}%`, background: color }}
            />
          </div>
          <div className="text-xs text-[#9ca3af] mt-1">{pctSold}% sold</div>
        </div>

        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="text-[#9ca3af] text-xs">Price per point</div>
            <div className="text-[#f9fafb] font-bold text-lg">${artist.pricePerPoint}</div>
          </div>
          <div className="text-right">
            <div className="text-[#9ca3af] text-xs">ECHO Score</div>
            <div className="text-[#f9fafb] font-bold text-lg">{artist.echoScore}</div>
          </div>
        </div>

        <Link
          href={`/points/${artist.id}`}
          className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2.5 rounded-lg transition-colors duration-200 mt-auto"
        >
          Buy Points
        </Link>
      </div>
    </div>
  );
}

export default function PointsStorePage() {
  const [activeFilter, setActiveFilter] = useState("All");

  const filtered = MOCK_ARTISTS.filter((a) => {
    if (activeFilter === "All" || activeFilter === "New Drops") return true;
    if (activeFilter === "Trending") return a.growthPct > 20;
    return a.genre.toLowerCase().includes(activeFilter.toLowerCase());
  });

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-16 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/3 w-96 h-96 bg-[#8b5cf6]/10 rounded-full blur-3xl" />
          <div className="absolute top-0 right-1/3 w-96 h-96 bg-[#10b981]/10 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            {MOCK_ARTISTS.length} active drops
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-[#f9fafb] mb-4">
            Own the Sound.{" "}
            <span
              style={{
                background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Earn Every Stream.
            </span>
          </h1>
          <p className="text-[#9ca3af] text-lg">
            Buy ECHO Points and earn royalties every time your artist streams. Back the music you believe in.
          </p>
        </div>
      </section>

      {/* Filter Bar */}
      <div className="sticky top-16 z-40 bg-[#0a0a0f]/95 backdrop-blur-lg border-b border-[#2a2a3a]">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-2 overflow-x-auto no-scrollbar">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setActiveFilter(f)}
              className={`shrink-0 text-sm font-medium px-4 py-2 rounded-full transition-colors duration-200 ${
                activeFilter === f
                  ? "bg-[#8b5cf6] text-white"
                  : "bg-[#13131a] border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] hover:border-[#8b5cf6]"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Artist Grid */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {filtered.length === 0 ? (
          <div className="text-center py-20 text-[#9ca3af]">No drops match this filter.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((artist, i) => (
              <ArtistCard key={artist.id} artist={artist} colorIndex={i} />
            ))}
          </div>
        )}
      </div>

      {/* How points work banner */}
      <section className="border-t border-[#2a2a3a] bg-[#13131a] py-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-2xl font-black text-[#f9fafb] mb-10">How ECHO Points Work</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Buy Points", desc: "Purchase fractional royalty ownership in an artist's release catalog. No lock-in, transparent pricing." },
              { step: "02", title: "Earn Royalties", desc: "As streams flow in, royalties are distributed proportionally to all point holders each month." },
              { step: "03", title: "Trade or Hold", desc: "After the 12-month holding period, points can be traded freely on the ECHO marketplace." },
            ].map((item) => (
              <div key={item.step} className="text-left">
                <div className="text-4xl font-black text-[#8b5cf6]/30 mb-3">{item.step}</div>
                <div className="font-bold text-[#f9fafb] mb-2">{item.title}</div>
                <div className="text-sm text-[#9ca3af] leading-relaxed">{item.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
