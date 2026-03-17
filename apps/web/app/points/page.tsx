"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { SkeletonGrid } from "@/components/Skeleton";
import { fetchPoints, formatNumber, tierBadge } from "@/lib/api";
import type { Artist } from "@/lib/api";

const FILTERS = ["All", "Trending", "New Drops", "Afrobeats", "Hip-Hop", "R&B", "Pop", "Indie"];
const SORT_OPTIONS = [
  { value: "score", label: "Melodio Score" },
  { value: "price_asc", label: "Price: Low → High" },
  { value: "price_desc", label: "Price: High → Low" },
  { value: "growth", label: "Growth %" },
];
const ARTIST_COLORS = ["#8b5cf6", "#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#14b8a6"];

function ArtistCard({ artist, colorIndex }: { artist: Artist; colorIndex: number }) {
  const color = ARTIST_COLORS[colorIndex % ARTIST_COLORS.length];
  const pctSold = Math.round(((artist.pointsTotal - artist.pointsAvailable) / artist.pointsTotal) * 100);

  return (
    <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] hover:border-[#8b5cf6] transition-all duration-200 overflow-hidden flex flex-col group">
      <div className="h-40 relative flex items-end p-4" style={{ background: `linear-gradient(135deg, ${color}30 0%, #0a0a0f 100%)` }}>
        <div className="absolute inset-0 flex items-center justify-center text-6xl opacity-20 select-none" aria-hidden>🎵</div>
        <div className="relative z-10 flex items-center gap-2">
          <span className="text-lg">{tierBadge(artist.tier)}</span>
          <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ background: `${color}30`, color }}>{artist.genre}</span>
        </div>
        <div className="absolute top-3 right-3 bg-[#0a0a0f]/80 backdrop-blur-sm text-[#f9fafb] text-xs font-bold px-2 py-1 rounded-lg border border-[#2a2a3a]">⚡ {artist.echoScore}</div>
      </div>
      <div className="p-5 flex flex-col flex-1">
        <h3 className="font-bold text-[#f9fafb] text-lg mb-1">{artist.name}</h3>
        <div className="text-sm text-[#9ca3af] mb-4">
          {formatNumber(artist.monthlyListeners)} monthly listeners
          <span className="ml-2 text-[#10b981] font-medium">+{artist.growthPct}%</span>
        </div>
        <div className="mb-4">
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-[#9ca3af]">Points Available</span>
            <span className="text-[#f9fafb] font-semibold">{artist.pointsAvailable} / {artist.pointsTotal}</span>
          </div>
          <div className="w-full h-1.5 bg-[#2a2a3a] rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{ width: `${pctSold}%`, background: color }} />
          </div>
          <div className="text-xs text-[#9ca3af] mt-1">{pctSold}% sold</div>
        </div>
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="text-[#9ca3af] text-xs">Price per point</div>
            <div className="text-[#f9fafb] font-bold text-lg">${artist.pricePerPoint}</div>
          </div>
          <div className="text-right">
            <div className="text-[#9ca3af] text-xs">Melodio Score</div>
            <div className="text-[#f9fafb] font-bold text-lg">{artist.echoScore}</div>
          </div>
        </div>
        <Link href={`/points/${artist.id}`} className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2.5 rounded-lg transition-colors duration-200 mt-auto">
          Buy Points
        </Link>
      </div>
    </div>
  );
}

export default function PointsStorePage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [activeFilter, setActiveFilter] = useState(searchParams.get("filter") || "All");
  const [sort, setSort] = useState(searchParams.get("sort") || "score");

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("q", search);
    if (activeFilter !== "All") params.set("filter", activeFilter);
    if (sort !== "score") params.set("sort", sort);
    const qs = params.toString();
    router.replace(qs ? `?${qs}` : "/points", { scroll: false });
  }, [search, activeFilter, sort]);

  const { data: artists = [], isLoading } = useQuery({
    queryKey: ["points"],
    queryFn: fetchPoints,
  });

  const filtered = artists
    .filter((a) => {
      if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && !a.genre.toLowerCase().includes(search.toLowerCase())) return false;
      if (activeFilter === "All" || activeFilter === "New Drops") return true;
      if (activeFilter === "Trending") return a.growthPct > 20;
      return a.genre.toLowerCase().includes(activeFilter.toLowerCase());
    })
    .sort((a, b) => {
      if (sort === "price_asc") return a.pricePerPoint - b.pricePerPoint;
      if (sort === "price_desc") return b.pricePerPoint - a.pricePerPoint;
      if (sort === "growth") return b.growthPct - a.growthPct;
      return b.echoScore - a.echoScore;
    });

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-12 px-4 text-center relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/3 w-96 h-96 bg-[#8b5cf6]/10 rounded-full blur-3xl" />
          <div className="absolute top-0 right-1/3 w-96 h-96 bg-[#10b981]/10 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-[#13131a] border border-[#2a2a3a] rounded-full px-4 py-2 text-sm text-[#9ca3af] mb-6">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            {isLoading ? "Loading…" : `${artists.length} active drops`}
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-[#f9fafb] mb-4">
            Own the Sound.{" "}
            <span style={{ background: "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Earn Every Stream.
            </span>
          </h1>
          <p className="text-[#9ca3af] text-lg">Buy Melodio Points and earn royalties every time your artist streams.</p>
        </div>
      </section>

      {/* Search + Filter Bar */}
      <div className="sticky top-16 z-40 bg-[#0a0a0f]/95 backdrop-blur-lg border-b border-[#2a2a3a]">
        <div className="max-w-7xl mx-auto px-4 py-3 space-y-2">
          {/* Search row */}
          <div className="flex gap-3 items-center">
            <div className="relative flex-1 max-w-sm">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7280]" width="16" height="16" fill="none" viewBox="0 0 16 16">
                <path d="M7 13A6 6 0 1 0 7 1a6 6 0 0 0 0 12zM13 13l-2.5-2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search artists or genres…"
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg pl-9 pr-4 py-2 text-sm text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:border-transparent transition-all"
              />
            </div>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] appearance-none cursor-pointer"
            >
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          {/* Filter chips row */}
          <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`shrink-0 text-sm font-medium px-4 py-1.5 rounded-full transition-colors duration-200 ${
                  activeFilter === f ? "bg-[#8b5cf6] text-white" : "bg-[#13131a] border border-[#2a2a3a] text-[#9ca3af] hover:text-[#f9fafb] hover:border-[#8b5cf6]"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Artist Grid */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {isLoading ? (
          <SkeletonGrid count={6} />
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-4xl mb-4">🎵</div>
            <div className="text-[#9ca3af] text-lg mb-2">No drops match your search.</div>
            <button onClick={() => { setSearch(""); setActiveFilter("All"); }} className="text-sm text-[#8b5cf6] hover:underline">Clear filters</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((artist, i) => (
              <ArtistCard key={artist.id} artist={artist} colorIndex={i} />
            ))}
          </div>
        )}
      </div>

      {/* How points work */}
      <section className="border-t border-[#2a2a3a] bg-[#13131a] py-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-2xl font-black text-[#f9fafb] mb-10">How Melodio Points Work</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Buy Points", desc: "Purchase fractional royalty ownership in an artist's release catalog. No lock-in, transparent pricing." },
              { step: "02", title: "Earn Royalties", desc: "As streams flow in, royalties are distributed proportionally to all point holders each month." },
              { step: "03", title: "Trade or Hold", desc: "After the 12-month holding period, points can be traded freely on the Melodio marketplace." },
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
