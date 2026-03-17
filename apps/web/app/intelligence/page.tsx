"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { searchArtistIntelligence, type IntelligenceSearchResult } from "@/lib/api";

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

const TRENDING_SEARCHES = [
  "Kendrick Lamar", "Tyla", "Chappell Roan", "Sabrina Carpenter",
  "Doechii", "GloRilla", "Gracie Abrams", "Shaboozey",
];

export default function IntelligencePage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<IntelligenceSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, 350);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    setSearching(true);
    const data = await searchArtistIntelligence(q);
    setResults(data.results ?? []);
    setShowDropdown(true);
    setSearching(false);
  }, []);

  useEffect(() => {
    doSearch(debouncedQuery);
  }, [debouncedQuery, doSearch]);

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function handleSelect(name: string) {
    router.push(`/intelligence/${encodeURIComponent(name)}`);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) handleSelect(query.trim());
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f] pt-20 pb-16">
      {/* Hero */}
      <section className="max-w-3xl mx-auto px-4 pt-16 pb-12 text-center">
        <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 rounded-full px-4 py-1.5 mb-6">
          <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
          <span className="text-xs font-medium text-[#8b5cf6]">AI-Powered Artist Intelligence</span>
        </div>

        <h1 className="text-4xl md:text-5xl font-black text-white mb-4 leading-tight">
          Know Every Artist.<br />
          <span className="text-[#8b5cf6]">Before Everyone Else.</span>
        </h1>
        <p className="text-text-muted text-lg max-w-xl mx-auto mb-10">
          Search any artist and get a comprehensive AI analysis — Melodio Score, 10 predictive signals, platform stats, and a sign recommendation.
        </p>

        {/* Search bar */}
        <div className="relative" ref={dropdownRef}>
          <form onSubmit={handleSubmit} className="relative">
            <div className="relative flex items-center">
              <svg
                className="absolute left-4 text-text-muted pointer-events-none"
                width="20" height="20" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => query && setShowDropdown(true)}
                placeholder="Search any artist..."
                className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-2xl pl-12 pr-32 py-4 text-white placeholder-text-muted text-lg focus:outline-none focus:border-[#8b5cf6] focus:ring-2 focus:ring-[#8b5cf6]/20 transition-all"
                autoComplete="off"
              />
              <button
                type="submit"
                disabled={!query.trim()}
                className="absolute right-2 bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-5 py-2.5 rounded-xl transition-colors text-sm"
              >
                {searching ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                    Searching
                  </span>
                ) : "Analyze →"}
              </button>
            </div>
          </form>

          {/* Dropdown results */}
          {showDropdown && results.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden shadow-2xl z-50">
              {results.map((r, i) => (
                <button
                  key={i}
                  onClick={() => handleSelect(r.name)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#1a1a2e] transition-colors text-left border-b border-[#2a2a3a] last:border-0"
                >
                  {r.image ? (
                    <img src={r.image} alt={r.name} className="w-10 h-10 rounded-full object-cover shrink-0" />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-[#8b5cf6]/20 flex items-center justify-center shrink-0">
                      <span className="text-[#8b5cf6] font-bold text-sm">{r.name[0]}</span>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-medium text-sm truncate">{r.name}</div>
                    {r.genres?.length > 0 && (
                      <div className="text-text-muted text-xs truncate">{r.genres.slice(0, 3).join(", ")}</div>
                    )}
                  </div>
                  {r.followers > 0 && (
                    <div className="text-text-muted text-xs shrink-0">
                      {r.followers >= 1_000_000
                        ? `${(r.followers / 1_000_000).toFixed(1)}M`
                        : r.followers >= 1_000
                        ? `${(r.followers / 1_000).toFixed(0)}K`
                        : r.followers}{" "}
                      followers
                    </div>
                  )}
                  <svg className="text-text-muted shrink-0" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m9 18 6-6-6-6"/>
                  </svg>
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Trending searches */}
      <section className="max-w-3xl mx-auto px-4 mb-16">
        <p className="text-xs font-medium text-text-muted mb-3 text-center uppercase tracking-wider">Trending searches</p>
        <div className="flex flex-wrap gap-2 justify-center">
          {TRENDING_SEARCHES.map((name) => (
            <button
              key={name}
              onClick={() => handleSelect(name)}
              className="bg-[#13131a] hover:bg-[#1a1a2e] border border-[#2a2a3a] hover:border-[#8b5cf6]/40 text-text-muted hover:text-white text-sm px-4 py-2 rounded-full transition-all"
            >
              {name}
            </button>
          ))}
        </div>
      </section>

      {/* Feature cards */}
      <section className="max-w-5xl mx-auto px-4">
        <h2 className="text-xl font-bold text-white text-center mb-8">What You Get</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            {
              icon: "🎯",
              title: "Melodio Score",
              desc: "0–100 composite score across Music Quality, Social Momentum, Commercial Traction, Brand Strength, and Market Timing.",
            },
            {
              icon: "📈",
              title: "10 Predictive Signals",
              desc: "Platform Velocity, Breakout Probability, Sync Readiness, Fanbase Quality, Release Cadence, and more.",
            },
            {
              icon: "🤖",
              title: "AI Executive Summary",
              desc: "Claude-powered 4-paragraph deep-dive analysis with sign recommendation and confidence level.",
            },
            {
              icon: "🌐",
              title: "Cross-Platform Stats",
              desc: "Spotify followers, YouTube views, touring data, Genius pageviews — all in one place.",
            },
            {
              icon: "🤝",
              title: "Collaboration Network",
              desc: "Map who the artist has worked with. Collaborating with rising producers is a leading indicator.",
            },
            {
              icon: "⚡",
              title: "Side-by-Side Compare",
              desc: "Compare up to 4 artists with radar charts and AI-generated comparison summaries.",
            },
          ].map((card) => (
            <div
              key={card.title}
              className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 hover:border-[#8b5cf6]/30 transition-colors"
            >
              <div className="text-2xl mb-3">{card.icon}</div>
              <h3 className="text-white font-semibold text-sm mb-2">{card.title}</h3>
              <p className="text-text-muted text-xs leading-relaxed">{card.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
