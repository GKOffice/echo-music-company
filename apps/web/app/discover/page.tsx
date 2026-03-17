"use client";

import { Suspense, useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { SkeletonGrid } from "@/components/Skeleton";
import { fetchArtists } from "@/lib/api";
import type { Artist } from "@/lib/api";

const TIMEFRAMES = ["7 Days", "30 Days", "90 Days"] as const;
const GENRES = ["All Genres", "Afrobeats", "Hip-Hop", "R&B", "Pop", "Indie", "Electronic", "Trap Soul", "Alt R&B"];

const SIGNALS = [
  { icon: "🎵", label: "Stream Growth", pct: "35%", desc: "Monthly listener trajectory" },
  { icon: "📱", label: "Social Velocity", pct: "25%", desc: "Cross-platform follower momentum" },
  { icon: "🎬", label: "Sync Heat", pct: "20%", desc: "Film, TV & ad placements" },
  { icon: "📰", label: "Press Momentum", pct: "10%", desc: "Reviews, features, interviews" },
  { icon: "🎯", label: "A&R Score", pct: "10%", desc: "Melodio internal talent assessment" },
];

function getTierInfo(score: number) {
  if (score >= 88) return { label: "🔥 Breaking", color: "#ef4444" };
  if (score >= 78) return { label: "⚡ Rising", color: "#8b5cf6" };
  if (score >= 65) return { label: "📈 Growing", color: "#10b981" };
  return { label: "👀 Watch List", color: "#f59e0b" };
}

function SignalBars({ score }: { score: number }) {
  const bars = [
    { val: score * 0.95, color: "#8b5cf6" },
    { val: score * 0.92, color: "#8b5cf6" },
    { val: score * 0.88, color: "#10b981" },
    { val: score * 0.82, color: "#10b981" },
    { val: score * 0.9, color: "#f59e0b" },
  ];
  return (
    <div className="flex gap-1 items-end h-6">
      {bars.map((b, i) => (
        <div key={i} className="flex flex-col justify-end w-3 h-6 rounded-sm overflow-hidden bg-[#1e1e2e]">
          <div style={{ height: `${b.val}%`, backgroundColor: b.color }} className="w-full rounded-sm transition-all" />
        </div>
      ))}
    </div>
  );
}

interface MappedArtist {
  id: string;
  name: string;
  genre: string;
  momentum_score: number;
  pointsAvailable: number;
  pricePerPoint: number;
}

function mapArtist(a: Artist): MappedArtist {
  return {
    id: a.id,
    name: a.name,
    genre: a.genre,
    momentum_score: a.echoScore,
    pointsAvailable: a.pointsAvailable,
    pricePerPoint: a.pricePerPoint,
  };
}

function ArtistCard({ artist }: { artist: MappedArtist }) {
  const tier = getTierInfo(artist.momentum_score);
  return (
    <div className="relative bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 hover:border-[#8b5cf6]/50 transition-all duration-200 group">
      <div className="absolute top-3 right-3 text-xs font-bold px-2 py-1 rounded-full" style={{ color: tier.color, backgroundColor: `${tier.color}20` }}>
        {tier.label}
      </div>
      <div className="mb-3">
        <div className="text-[#f9fafb] font-bold text-lg leading-tight pr-20">{artist.name}</div>
        <div className="text-[#9ca3af] text-xs mt-0.5">{artist.genre}</div>
      </div>
      <div className="flex items-baseline gap-1 mb-3">
        <span className="font-black text-3xl" style={{ color: tier.color }}>{artist.momentum_score}</span>
        <span className="text-[#6b7280] text-xs">/ 100 momentum</span>
      </div>
      <div className="mb-4">
        <SignalBars score={artist.momentum_score} />
        <div className="text-[#6b7280] text-[10px] mt-1">stream · social · sync · press · A&R</div>
      </div>
      <div className="flex items-center justify-between text-xs text-[#9ca3af] mb-4">
        <span>{artist.pointsAvailable.toLocaleString()} pts available</span>
        <span className="text-[#f9fafb] font-semibold">${artist.pricePerPoint}/pt</span>
      </div>
      <div className="flex gap-2">
        <Link href={`/points/${artist.id}`} className="flex-1 text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-xs font-semibold py-2 px-3 rounded-lg transition-colors">
          Buy Points
        </Link>
        <button className="flex-1 text-center border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#f9fafb] text-xs font-semibold py-2 px-3 rounded-lg transition-colors">
          Watch
        </button>
      </div>
    </div>
  );
}

function DiscoverContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState("7 Days");
  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [genre, setGenre] = useState(searchParams.get("genre") || "All Genres");

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("q", search);
    if (genre !== "All Genres") params.set("genre", genre);
    const qs = params.toString();
    router.replace(qs ? `/discover?${qs}` : "/discover", { scroll: false });
  }, [search, genre]);

  const { data: rawArtists = [], isLoading } = useQuery({
    queryKey: ["artists"],
    queryFn: fetchArtists,
  });

  const artists = rawArtists
    .map(mapArtist)
    .filter((a) => {
      if (search && !a.name.toLowerCase().includes(search.toLowerCase())) return false;
      if (genre !== "All Genres" && !a.genre.toLowerCase().includes(genre.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => b.momentum_score - a.momentum_score);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      {/* Hero */}
      <section className="pt-28 pb-12 px-6 md:px-10 max-w-6xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 rounded-full px-4 py-1.5 text-[#8b5cf6] text-xs font-semibold mb-6">
          Artist discovery only — not financial advice
        </div>
        <h1 className="text-4xl md:text-6xl font-black tracking-tight mb-4">
          Discover Who&apos;s <span className="text-[#ef4444]">Breaking</span>
        </h1>
        <p className="text-[#9ca3af] text-lg max-w-2xl mx-auto">
          Our AI tracks streams, sync placements, press momentum, and social growth to surface artists before they blow up.
        </p>
      </section>

      {/* Search + Filter */}
      <div className="sticky top-16 z-40 bg-[#0a0a0f]/95 backdrop-blur-lg border-b border-[#2a2a3a]">
        <div className="max-w-6xl mx-auto px-6 py-3 flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7280]" width="16" height="16" fill="none" viewBox="0 0 16 16">
              <path d="M7 13A6 6 0 1 0 7 1a6 6 0 0 0 0 12zM13 13l-2.5-2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search artists…"
              className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg pl-9 pr-4 py-2 text-sm text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] transition-all"
            />
          </div>
          <select
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#9ca3af] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] appearance-none"
          >
            {GENRES.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
      </div>

      {/* Trending Section */}
      <section className="px-6 md:px-10 max-w-6xl mx-auto py-12 mb-10">
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <h2 className="text-xl font-bold">Trending Now</h2>
          <div className="flex gap-1 bg-[#13131a] border border-[#2a2a3a] rounded-lg p-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setActiveTab(tf)}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all ${activeTab === tf ? "bg-[#8b5cf6] text-white" : "text-[#9ca3af] hover:text-[#f9fafb]"}`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <SkeletonGrid count={8} />
        ) : artists.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-4xl mb-4">🔍</div>
            <div className="text-[#9ca3af] text-lg mb-2">No artists match your search.</div>
            <button onClick={() => { setSearch(""); setGenre("All Genres"); }} className="text-sm text-[#8b5cf6] hover:underline">Clear filters</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {artists.map((artist) => <ArtistCard key={artist.id} artist={artist} />)}
          </div>
        )}
      </section>

      {/* How We Score section */}
      <section className="px-6 md:px-10 max-w-6xl mx-auto mb-20">
        <h2 className="text-xl font-bold mb-2">How We Score Artists</h2>
        <p className="text-[#6b7280] text-sm mb-8">The Melodio Momentum Score combines 5 signals, updated continuously.</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {SIGNALS.map((s) => (
            <div key={s.label} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4 hover:border-[#8b5cf6]/40 transition-colors">
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
          <h2 className="text-xl font-bold mb-2">Your Picks</h2>
          <p className="text-[#9ca3af] text-sm mb-6 max-w-md mx-auto">
            Sign in to get personalized artist recommendations based on your taste and backing history.
          </p>
          <Link href="/auth/login" className="inline-block bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-6 py-2.5 rounded-lg transition-colors">
            Sign In for Personalized Picks
          </Link>
        </div>
      </section>

      {/* Footer disclaimer */}
      <footer className="px-6 md:px-10 max-w-6xl mx-auto pb-16">
        <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 text-center">
          <p className="text-[#6b7280] text-xs max-w-2xl mx-auto">
            Melodio artist discovery is for informational purposes only. Buying Melodio Points is not a securities offering.
            Past royalty performance of any artist does not guarantee future earnings. Melodio Points are not securities.
          </p>
        </div>
      </footer>
    </div>
  );
}

const LoadingFallback = () => (
  <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
    <div className="w-8 h-8 rounded-full border-2 border-[#8b5cf6] border-t-transparent animate-spin" />
  </div>
);

export default function DiscoverPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <DiscoverContent />
    </Suspense>
  );
}
