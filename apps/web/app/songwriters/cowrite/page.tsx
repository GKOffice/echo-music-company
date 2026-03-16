"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../../components/Navbar";

const GENRES = ["All Genres", "R&B", "Pop", "Hip-Hop", "Afrobeats", "Electronic", "Country", "Rock"];
const STYLES = ["All Styles", "Melodic", "Lyrical", "Topliner", "Producer-Writer"];
const BUDGETS = ["All Budgets", "Cash", "Points", "Cash + Points"];

const SEEKERS = [
  {
    avatar: "🎤",
    name: "Marcus Reid",
    genre: "R&B",
    need: "Looking for R&B co-writer for upcoming debut EP. Need someone who can write emotional hooks. Already have 3 instrumentals ready.",
    offer: "20% publishing points",
    offerType: "points",
    deadline: "Rolling",
    verified: true,
  },
  {
    avatar: "🎛️",
    name: "Neon Flux",
    genre: "Pop",
    need: "Producer seeking topline writer for Pop single. Radio-ready track. Must be available this month.",
    offer: "$500 + 15% publishing",
    offerType: "both",
    deadline: "Mar 30, 2026",
    verified: false,
  },
  {
    avatar: "🎵",
    name: "Aaliya J",
    genre: "Hip-Hop",
    need: "Female rapper seeking lyricist for Hip-Hop EP (4 tracks). Paying per track, open to publishing split.",
    offer: "25% publishing pts / track",
    offerType: "points",
    deadline: "Apr 15, 2026",
    verified: true,
  },
  {
    avatar: "🎸",
    name: "River Stone",
    genre: "Indie Pop",
    need: "Indie artist looking for melodic songwriter for debut album sessions. Mostly acoustic, some production.",
    offer: "$300 + 10% publishing",
    offerType: "both",
    deadline: "Apr 30, 2026",
    verified: false,
  },
];

const AVAILABLE_WRITERS = [
  {
    avatar: "✍️",
    name: "Zara Sol",
    genres: ["R&B", "Pop"],
    credits: "Co-wrote 3 charting songs including 'Midnight Protocol'",
    rate: "$400–$800 / song",
    rateType: "cash",
    availability: "Available now",
    verified: true,
  },
  {
    avatar: "🎹",
    name: "Leo Vance",
    genres: ["Hip-Hop", "Trap"],
    credits: "Songwriter for 2 major label artists",
    rate: "15–25% publishing points",
    rateType: "points",
    availability: "2 slots open",
    verified: true,
  },
  {
    avatar: "🎧",
    name: "Maya Drift",
    genres: ["Pop", "Electronic"],
    credits: "Topline writer — 12M+ streams on co-writes",
    rate: "$250–$600 + points",
    rateType: "both",
    availability: "Available Apr 1",
    verified: false,
  },
  {
    avatar: "🎙️",
    name: "Dax Morrow",
    genres: ["Afrobeats", "R&B"],
    credits: "Award-winning lyricist, 7 years experience",
    rate: "20% publishing points",
    rateType: "points",
    availability: "Available now",
    verified: true,
  },
];

const RATE_COLOR: Record<string, string> = {
  cash: "#10b981",
  points: "#f59e0b",
  both: "#8b5cf6",
};

export default function CowritePage() {
  const [genre, setGenre] = useState("All Genres");
  const [style, setStyle] = useState("All Styles");
  const [budget, setBudget] = useState("All Budgets");

  const filterSelect =
    "bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#e8e8f0] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] appearance-none cursor-pointer";

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-12 px-4 text-center border-b border-[#2a2a3a] bg-[#13131a]">
        <div className="inline-flex items-center gap-2 bg-[#0a0a0f] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
          <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
          {SEEKERS.length + AVAILABLE_WRITERS.length} active listings
        </div>
        <h1 className="text-3xl md:text-5xl font-black text-[#f9fafb] mb-3">
          Find Your Next{" "}
          <span
            style={{
              background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Co-writer.
          </span>
        </h1>
        <p className="text-[#9ca3af] max-w-xl mx-auto">
          Match with songwriters by genre, style, and availability. Pay with cash or publishing
          points.
        </p>
      </section>

      {/* Filter bar */}
      <section className="py-4 px-4 bg-[#13131a] border-b border-[#2a2a3a] sticky top-16 z-40">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center gap-3">
          <select
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            className={filterSelect}
          >
            {GENRES.map((g) => (
              <option key={g}>{g}</option>
            ))}
          </select>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            className={filterSelect}
          >
            {STYLES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
          <select
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            className={filterSelect}
          >
            {BUDGETS.map((b) => (
              <option key={b}>{b}</option>
            ))}
          </select>
          <Link
            href="/dealroom/create?type=seek_cowriter"
            className="ml-auto bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2 rounded-lg transition-colors"
          >
            + Post Opportunity
          </Link>
        </div>
      </section>

      {/* Two-column layout */}
      <section className="py-10 px-4 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

          {/* Left — Looking for co-writers */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-black text-[#f9fafb] text-lg">Looking for Co-writers</h2>
              <span className="text-xs text-[#9ca3af] bg-[#13131a] border border-[#2a2a3a] rounded-full px-3 py-1">
                {SEEKERS.length} listings
              </span>
            </div>
            <div className="space-y-4">
              {SEEKERS.map((s) => (
                <div
                  key={s.name}
                  className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 hover:border-[#8b5cf6]/40 transition-colors"
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 bg-[#0a0a0f] border border-[#2a2a3a] rounded-full flex items-center justify-center text-xl shrink-0">
                      {s.avatar}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-[#f9fafb] text-sm">{s.name}</span>
                        {s.verified && (
                          <span className="text-xs text-[#10b981]">✓ Verified</span>
                        )}
                      </div>
                      <span className="text-xs text-[#9ca3af]">{s.genre}</span>
                    </div>
                    <span className="text-xs text-[#9ca3af] shrink-0">{s.deadline}</span>
                  </div>
                  <p className="text-sm text-[#9ca3af] mb-4 leading-relaxed">{s.need}</p>
                  <div className="flex items-center justify-between">
                    <span
                      className="text-xs font-semibold px-3 py-1 rounded-full"
                      style={{
                        background: `${RATE_COLOR[s.offerType]}15`,
                        color: RATE_COLOR[s.offerType],
                        border: `1px solid ${RATE_COLOR[s.offerType]}30`,
                      }}
                    >
                      {s.offer}
                    </span>
                    <button className="text-xs text-[#8b5cf6] hover:text-[#a78bfa] font-medium transition-colors">
                      Apply →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — Available co-writers */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-black text-[#f9fafb] text-lg">Available Co-writers</h2>
              <span className="text-xs text-[#9ca3af] bg-[#13131a] border border-[#2a2a3a] rounded-full px-3 py-1">
                {AVAILABLE_WRITERS.length} writers
              </span>
            </div>
            <div className="space-y-4">
              {AVAILABLE_WRITERS.map((w) => (
                <div
                  key={w.name}
                  className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 hover:border-[#10b981]/40 transition-colors"
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 bg-[#0a0a0f] border border-[#2a2a3a] rounded-full flex items-center justify-center text-xl shrink-0">
                      {w.avatar}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-[#f9fafb] text-sm">{w.name}</span>
                        {w.verified && (
                          <span className="text-xs text-[#10b981]">✓ Verified</span>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {w.genres.map((g) => (
                          <span
                            key={g}
                            className="text-xs bg-[#2a2a3a] text-[#9ca3af] px-2 py-0.5 rounded"
                          >
                            {g}
                          </span>
                        ))}
                      </div>
                    </div>
                    <span
                      className={`text-xs shrink-0 ${
                        w.availability.includes("now") ? "text-[#10b981]" : "text-[#9ca3af]"
                      }`}
                    >
                      {w.availability}
                    </span>
                  </div>
                  <p className="text-xs text-[#9ca3af] italic mb-3">{w.credits}</p>
                  <div className="flex items-center justify-between">
                    <span
                      className="text-xs font-semibold px-3 py-1 rounded-full"
                      style={{
                        background: `${RATE_COLOR[w.rateType]}15`,
                        color: RATE_COLOR[w.rateType],
                        border: `1px solid ${RATE_COLOR[w.rateType]}30`,
                      }}
                    >
                      {w.rate}
                    </span>
                    <button className="text-xs text-[#8b5cf6] hover:text-[#a78bfa] font-medium transition-colors">
                      Book →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Post listing CTA */}
        <div className="mt-12 text-center bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-10">
          <div className="text-3xl mb-3">🤝</div>
          <h3 className="text-xl font-black text-[#f9fafb] mb-2">
            Looking for a co-writer? Post your opportunity.
          </h3>
          <p className="text-[#9ca3af] text-sm mb-6">
            Describe what you need. Writers apply. You choose. Pay with cash or publishing points.
          </p>
          <Link
            href="/dealroom/create?type=seek_cowriter"
            className="inline-block bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-sm"
            style={{ boxShadow: "0 0 20px rgba(139,92,246,0.3)" }}
          >
            Post a Co-write Opportunity
          </Link>
        </div>
      </section>
    </main>
  );
}
