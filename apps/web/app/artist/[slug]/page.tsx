"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";

const API_URL = typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://api-production-14b6.up.railway.app" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

// ─── Types ───────────────────────────────────────────────────────────────────

interface ScoreBreakdown {
  streaming: number;
  engagement: number;
  playlistPotential: number;
  growthTrajectory: number;
}

interface Release {
  id: string;
  title: string;
  releaseDate: string;
  streams: number;
  status: "live" | "upcoming" | "processing";
}

interface Artist {
  id: string;
  slug: string;
  name: string;
  genre: string;
  bio: string;
  monthlyListeners: number;
  totalStreams: number;
  pointsAvailable: number;
  pointsTotal: number;
  pricePerPoint: number;
  holderCount?: number;
  recentBuyers?: number;
  melodioScore: number;
  scoreBreakdown: ScoreBreakdown;
  social: {
    spotify?: string;
    instagram?: string;
    tiktok?: string;
    twitter?: string;
  };
  releases: Release[];
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_ARTIST: Artist = {
  id: "1",
  slug: "nova-vex",
  name: "Nova Vex",
  genre: "Afrobeats",
  bio: "Nova Vex is a London-based Afrobeats artist blending West African rhythms with UK club culture. Signed to Melodio's inaugural artist roster in 2025, she's amassed 284K monthly listeners in just 8 months.",
  monthlyListeners: 284000,
  totalStreams: 4200000,
  pointsAvailable: 3,
  pointsTotal: 15,
  pricePerPoint: 250,
  holderCount: 12,
  recentBuyers: 3,
  melodioScore: 94,
  scoreBreakdown: {
    streaming: 24,
    engagement: 23,
    playlistPotential: 24,
    growthTrajectory: 23,
  },
  social: {
    spotify: "#",
    instagram: "#",
    tiktok: "#",
    twitter: "#",
  },
  releases: [
    {
      id: "r1",
      title: "Midnight Drive",
      releaseDate: "2026-02-14",
      streams: 1240000,
      status: "live",
    },
    {
      id: "r2",
      title: "Neon Fever",
      releaseDate: "2026-01-20",
      streams: 860000,
      status: "live",
    },
    {
      id: "r3",
      title: "Dark Matter EP",
      releaseDate: "2026-03-22",
      streams: 0,
      status: "upcoming",
    },
  ],
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

function scoreColor(score: number): string {
  if (score >= 81) return "#8b5cf6";
  if (score >= 61) return "#10b981";
  if (score >= 31) return "#f59e0b";
  return "#ef4444";
}

function scoreLabel(score: number): string {
  if (score >= 81) return "Elite";
  if (score >= 61) return "Strong";
  if (score >= 31) return "Growing";
  return "Emerging";
}

function releaseStatusBadge(status: string) {
  if (status === "live") return { label: "Live", bg: "#10b98120", color: "#10b981" };
  if (status === "upcoming") return { label: "Upcoming", bg: "#f59e0b20", color: "#f59e0b" };
  return { label: "Processing", bg: "#8b5cf620", color: "#8b5cf6" };
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

// ─── Circular Score Ring ──────────────────────────────────────────────────────

function ScoreRing({ score }: { score: number }) {
  const R = 50;
  const CIRCUMFERENCE = 2 * Math.PI * R; // 314.159...
  const offset = CIRCUMFERENCE * (1 - score / 100);
  const color = scoreColor(score);
  const label = scoreLabel(score);

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox="0 0 120 120"
        width={120}
        height={120}
        aria-label={`Melodio Score: ${score} out of 100`}
      >
        {/* Background ring */}
        <circle
          cx={60}
          cy={60}
          r={R}
          stroke="#2a2a38"
          strokeWidth={10}
          fill="none"
        />
        {/* Progress ring */}
        <circle
          cx={60}
          cy={60}
          r={R}
          stroke={color}
          strokeWidth={10}
          fill="none"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        {/* Center score */}
        <text
          x={60}
          y={54}
          textAnchor="middle"
          fontSize="24"
          fontWeight="900"
          fill={color}
        >
          {score}
        </text>
        <text
          x={60}
          y={68}
          textAnchor="middle"
          fontSize="11"
          fill="#9ca3af"
        >
          /100
        </text>
      </svg>
      <span
        className="mt-1 text-xs font-bold px-3 py-1 rounded-full"
        style={{ background: `${color}20`, color }}
      >
        {label}
      </span>
    </div>
  );
}

// ─── Social Icon Buttons ──────────────────────────────────────────────────────

function SpotifyIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.516 17.318c-.213.33-.666.435-.996.222-2.727-1.666-6.16-2.042-10.21-1.118-.39.09-.779-.152-.869-.541-.09-.39.152-.779.541-.869 4.424-1.01 8.22-.576 11.29 1.293.33.213.435.666.244.013zm1.47-3.27c-.267.41-.829.54-1.239.273-3.12-1.919-7.876-2.474-11.56-1.353-.477.144-.98-.125-1.124-.602-.144-.477.125-.98.602-1.124 4.214-1.28 9.444-.656 13.03 1.567.41.267.54.829.273 1.239zm.127-3.404C15.37 8.612 9.507 8.41 6.228 9.387c-.572.174-1.175-.153-1.349-.725-.174-.572.153-1.175.725-1.349 3.778-1.147 10.063-.926 14.023 1.574.509.306.673.966.367 1.475-.306.509-.966.673-1.475.367l-.402-.415z" />
    </svg>
  );
}

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
    </svg>
  );
}

function TikTokIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
      <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.22 8.22 0 004.84 1.55V6.82a4.85 4.85 0 01-1.07-.13z" />
    </svg>
  );
}

function TwitterIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ArtistProfilePage() {
  const params = useParams();
  const slug = typeof params.slug === "string" ? params.slug : "nova-vex";

  const [toast, setToast] = useState(false);
  const [scoreTooltip, setScoreTooltip] = useState(false);

  const { data: artist, isLoading } = useQuery<Artist>({
    queryKey: ["artist", slug],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/artists/${slug}`, {
          headers: { "Content-Type": "application/json" },
        });
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return MOCK_ARTIST;
      }
    },
  });

  const handleShare = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
    } catch {
      // fallback
    }
    setToast(true);
    setTimeout(() => setToast(false), 2000);
  }, []);

  const score = artist?.melodioScore ?? 0;
  const breakdown = artist?.scoreBreakdown ?? {
    streaming: 0,
    engagement: 0,
    playlistPotential: 0,
    growthTrajectory: 0,
  };

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      {/* Toast */}
      <div
        className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
          toast ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4 pointer-events-none"
        }`}
      >
        <div className="bg-[#10b981] text-white text-sm font-semibold px-5 py-3 rounded-xl shadow-xl">
          Link copied!
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 pt-24 pb-16">
        {/* Hero Section */}
        <div className="bg-[#13131a] rounded-2xl border border-[#2a2a38] p-6 sm:p-8 mb-6">
          <div className="flex flex-col sm:flex-row items-start gap-6">
            {/* Avatar */}
            {isLoading ? (
              <Skeleton className="w-24 h-24 sm:w-32 sm:h-32 rounded-full shrink-0" />
            ) : (
              <div
                className="w-24 h-24 sm:w-32 sm:h-32 rounded-full shrink-0"
                style={{
                  background:
                    "linear-gradient(135deg, #8b5cf6 0%, #10b981 100%)",
                  boxShadow: "0 0 32px #8b5cf640",
                }}
              />
            )}

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-start gap-3 mb-3">
                {isLoading ? (
                  <Skeleton className="h-9 w-48" />
                ) : (
                  <h1 className="text-3xl sm:text-4xl font-black text-[#f9fafb]">
                    {artist?.name}
                  </h1>
                )}
                <button
                  onClick={handleShare}
                  className="mt-1 flex items-center gap-1.5 text-xs bg-[#1a1a24] hover:bg-[#2a2a38] border border-[#2a2a38] text-[#9ca3af] hover:text-[#f9fafb] px-3 py-1.5 rounded-lg transition-colors"
                >
                  <svg viewBox="0 0 20 20" width="14" height="14" fill="currentColor">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v1h8v-1zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-1a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v1h-3zM4.75 12.094A5.973 5.973 0 004 15v1H1v-1a3 3 0 013.75-2.906z" />
                  </svg>
                  Share
                </button>
              </div>

              {/* Genre tag */}
              {isLoading ? (
                <Skeleton className="h-6 w-24 rounded-full mb-3" />
              ) : (
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="text-xs font-semibold bg-[#8b5cf6]/20 text-[#a78bfa] px-3 py-1 rounded-full">
                    {artist?.genre}
                  </span>
                </div>
              )}

              {/* Bio */}
              {isLoading ? (
                <div className="space-y-2 mb-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <Skeleton className="h-4 w-4/5" />
                </div>
              ) : (
                <p className="text-[#9ca3af] text-sm leading-relaxed mb-4 max-w-2xl">
                  {artist?.bio}
                </p>
              )}

              {/* Social links */}
              {!isLoading && artist?.social && (
                <div className="flex items-center gap-2">
                  {artist.social.spotify && (
                    <a
                      href={artist.social.spotify}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-9 h-9 flex items-center justify-center rounded-lg bg-[#1a1a24] hover:bg-[#2a2a38] text-[#1db954] hover:text-[#1db954] border border-[#2a2a38] transition-colors"
                      aria-label="Spotify"
                    >
                      <SpotifyIcon />
                    </a>
                  )}
                  {artist.social.instagram && (
                    <a
                      href={artist.social.instagram}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-9 h-9 flex items-center justify-center rounded-lg bg-[#1a1a24] hover:bg-[#2a2a38] text-[#e1306c] border border-[#2a2a38] transition-colors"
                      aria-label="Instagram"
                    >
                      <InstagramIcon />
                    </a>
                  )}
                  {artist.social.tiktok && (
                    <a
                      href={artist.social.tiktok}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-9 h-9 flex items-center justify-center rounded-lg bg-[#1a1a24] hover:bg-[#2a2a38] text-[#f9fafb] border border-[#2a2a38] transition-colors"
                      aria-label="TikTok"
                    >
                      <TikTokIcon />
                    </a>
                  )}
                  {artist.social.twitter && (
                    <a
                      href={artist.social.twitter}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-9 h-9 flex items-center justify-center rounded-lg bg-[#1a1a24] hover:bg-[#2a2a38] text-[#1d9bf0] border border-[#2a2a38] transition-colors"
                      aria-label="X / Twitter"
                    >
                      <TwitterIcon />
                    </a>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-4">
                  <Skeleton className="h-3 w-3/4 mb-2" />
                  <Skeleton className="h-6 w-1/2" />
                </div>
              ))
            : [
                {
                  label: "Monthly Listeners",
                  value: formatNumber(artist?.monthlyListeners ?? 0),
                  icon: "👂",
                  color: "#8b5cf6",
                },
                {
                  label: "Total Streams",
                  value: formatNumber(artist?.totalStreams ?? 0),
                  icon: "▶️",
                  color: "#10b981",
                },
                {
                  label: "Melodio Score",
                  value: `${artist?.melodioScore ?? 0}/100`,
                  icon: "⚡",
                  color: scoreColor(artist?.melodioScore ?? 0),
                },
                {
                  label: "Points Available",
                  value: `${artist?.pointsAvailable ?? 0} / ${artist?.pointsTotal ?? 0}`,
                  icon: "💎",
                  color: "#f59e0b",
                },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-4 hover:border-[#8b5cf6]/40 transition-colors"
                >
                  <div className="text-xs text-[#6b7280] mb-1">{stat.label}</div>
                  <div
                    className="text-xl font-black"
                    style={{ color: stat.color }}
                  >
                    {stat.value}
                  </div>
                </div>
              ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left — Discography + Points Drops */}
          <div className="lg:col-span-2 space-y-6">
            {/* Discography */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-5">Discography</h2>
              <div className="space-y-3">
                {isLoading
                  ? Array.from({ length: 3 }).map((_, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-4 p-4 bg-[#0a0a0f] rounded-xl border border-[#2a2a38]"
                      >
                        <Skeleton className="w-14 h-14 rounded-xl shrink-0" />
                        <div className="flex-1 space-y-2">
                          <Skeleton className="h-4 w-1/2" />
                          <Skeleton className="h-3 w-1/3" />
                        </div>
                        <Skeleton className="h-6 w-16 shrink-0" />
                      </div>
                    ))
                  : artist?.releases.map((release) => {
                      const badge = releaseStatusBadge(release.status);
                      return (
                        <div
                          key={release.id}
                          className="flex items-center gap-4 p-4 bg-[#0a0a0f] rounded-xl border border-[#2a2a38] hover:border-[#8b5cf6]/50 transition-colors"
                        >
                          {/* Cover art gradient placeholder */}
                          <div
                            className="w-14 h-14 rounded-xl shrink-0"
                            style={{
                              background: `linear-gradient(135deg, #${Math.floor(
                                Math.random() * 0x555555 + 0x444444
                              )
                                .toString(16)
                                .padStart(6, "0")} 0%, #${Math.floor(
                                Math.random() * 0x555555 + 0x444444
                              )
                                .toString(16)
                                .padStart(6, "0")} 100%)`,
                            }}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-[#f9fafb] text-sm truncate">
                              {release.title}
                            </div>
                            <div className="text-xs text-[#6b7280] mt-0.5">
                              {formatDate(release.releaseDate)}
                            </div>
                          </div>
                          <div className="text-right shrink-0">
                            {release.streams > 0 && (
                              <div className="text-sm font-bold text-[#f9fafb]">
                                {formatNumber(release.streams)}
                              </div>
                            )}
                            <span
                              className="text-xs px-2 py-0.5 rounded-full font-medium"
                              style={{ background: badge.bg, color: badge.color }}
                            >
                              {badge.label}
                            </span>
                          </div>
                        </div>
                      );
                    })}
              </div>
            </section>

            {/* Available Points */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-bold text-[#f9fafb]">Available Points</h2>
                <span className="text-xs text-[#9ca3af] bg-[#1a1a24] px-3 py-1 rounded-full">
                  {artist?.pointsAvailable ?? 0} remaining
                </span>
              </div>
              {/* FOMO — holder count */}
              {(artist?.holderCount ?? 0) > 0 && (
                <div className="flex items-center gap-3 mb-5 p-3 bg-[#0a0a0f] rounded-xl border border-[#2a2a38]">
                  <div className="flex -space-x-1.5">
                    {Array.from({ length: Math.min(artist?.holderCount ?? 0, 5) }).map((_, i) => (
                      <div key={i} className="w-6 h-6 rounded-full bg-gradient-to-br from-[#8b5cf6] to-[#10b981] border-2 border-[#0a0a0f] flex items-center justify-center text-[9px] font-bold text-white">
                        {String.fromCharCode(65 + i)}
                      </div>
                    ))}
                  </div>
                  <div className="flex-1 text-sm text-[#9ca3af]">
                    <span className="text-[#f9fafb] font-bold">{artist?.holderCount}</span> fans already holding
                    {(artist?.holderCount ?? 0) >= 8 && (
                      <span className="ml-2 text-[#ef4444] text-xs font-bold animate-pulse">· Almost sold out</span>
                    )}
                  </div>
                  {(artist?.recentBuyers ?? 0) > 0 && (
                    <span className="text-xs bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30 px-2 py-1 rounded-full font-bold">
                      🔥 {artist?.recentBuyers} bought today
                    </span>
                  )}
                </div>
              )}

              {isLoading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Array.from({ length: 2 }).map((_, i) => (
                    <div key={i} className="bg-[#0a0a0f] rounded-xl border border-[#2a2a38] p-5">
                      <Skeleton className="h-4 w-1/2 mb-3" />
                      <Skeleton className="h-8 w-1/3 mb-2" />
                      <Skeleton className="h-3 w-2/3 mb-4" />
                      <Skeleton className="h-10 w-full" />
                    </div>
                  ))}
                </div>
              ) : (artist?.pointsAvailable ?? 0) > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {Array.from({ length: Math.min(artist?.pointsAvailable ?? 0, 2) }).map(
                    (_, i) => (
                      <div
                        key={i}
                        className="bg-[#0a0a0f] rounded-xl border border-[#2a2a38] hover:border-[#8b5cf6]/50 p-5 transition-colors"
                      >
                        <div className="text-xs text-[#9ca3af] mb-1">Point Drop #{i + 1}</div>
                        <div className="text-2xl font-black text-[#f9fafb] mb-1">
                          ${artist?.pricePerPoint?.toLocaleString()}
                        </div>
                        <div className="text-xs text-[#6b7280] mb-4">
                          per point &middot; {1} of {artist?.pointsTotal} total
                        </div>
                        <div className="w-full h-1.5 bg-[#2a2a38] rounded-full overflow-hidden mb-4">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${
                                100 -
                                ((artist?.pointsAvailable ?? 0) / (artist?.pointsTotal ?? 1)) * 100
                              }%`,
                              background: "linear-gradient(90deg, #8b5cf6, #10b981)",
                            }}
                          />
                        </div>
                        <Link
                          href={`/points/${artist?.id}`}
                          className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2.5 rounded-xl transition-colors"
                        >
                          Buy Points
                        </Link>
                      </div>
                    )
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-3xl mb-3">🔒</div>
                  <div className="text-[#9ca3af] text-sm">All points have been purchased.</div>
                  <Link
                    href="/discover"
                    className="inline-block mt-3 text-sm text-[#8b5cf6] hover:underline"
                  >
                    Discover other artists
                  </Link>
                </div>
              )}
            </section>
          </div>

          {/* Right — Melodio Score */}
          <aside>
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6 sticky top-24">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-bold text-[#f9fafb]">Melodio Score</h2>
                <button
                  onClick={() => setScoreTooltip((v) => !v)}
                  className="w-6 h-6 rounded-full bg-[#1a1a24] border border-[#2a2a38] text-[#9ca3af] hover:text-[#f9fafb] text-xs flex items-center justify-center transition-colors"
                  aria-label="What is Melodio Score?"
                >
                  ?
                </button>
              </div>

              {scoreTooltip && (
                <div className="mb-4 text-xs text-[#9ca3af] bg-[#1a1a24] border border-[#2a2a38] rounded-xl p-3 leading-relaxed">
                  Melodio Score measures an artist&apos;s streaming momentum, fan engagement, playlist placement potential, and growth trajectory. Scored 0-100.
                </div>
              )}

              {isLoading ? (
                <div className="flex flex-col items-center gap-4">
                  <Skeleton className="w-[120px] h-[120px] rounded-full" />
                  <div className="w-full space-y-3">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <Skeleton key={i} className="h-8 w-full" />
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  {/* Ring */}
                  <div className="flex justify-center mb-6">
                    <ScoreRing score={score} />
                  </div>

                  {/* Sub-scores */}
                  <div className="space-y-4">
                    {[
                      { label: "Streaming", max: 25, value: breakdown.streaming },
                      { label: "Engagement", max: 25, value: breakdown.engagement },
                      {
                        label: "Playlist Potential",
                        max: 25,
                        value: breakdown.playlistPotential,
                      },
                      {
                        label: "Growth Trajectory",
                        max: 25,
                        value: breakdown.growthTrajectory,
                      },
                    ].map((sub) => {
                      const pct = (sub.value / sub.max) * 100;
                      const c = scoreColor(pct);
                      return (
                        <div key={sub.label}>
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-xs text-[#9ca3af]">{sub.label}</span>
                            <span
                              className="text-xs font-bold"
                              style={{ color: c }}
                            >
                              {sub.value}/{sub.max}
                            </span>
                          </div>
                          <div className="w-full h-2 bg-[#2a2a38] rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-700"
                              style={{
                                width: `${pct}%`,
                                background: c,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Color legend */}
                  <div className="mt-5 pt-4 border-t border-[#2a2a38] grid grid-cols-2 gap-2">
                    {[
                      { label: "0–30 Emerging", color: "#ef4444" },
                      { label: "31–60 Growing", color: "#f59e0b" },
                      { label: "61–80 Strong", color: "#10b981" },
                      { label: "81–100 Elite", color: "#8b5cf6" },
                    ].map((leg) => (
                      <div key={leg.label} className="flex items-center gap-1.5">
                        <div
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ background: leg.color }}
                        />
                        <span className="text-[10px] text-[#6b7280]">{leg.label}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </section>
          </aside>
        </div>
      </div>
    </main>
  );
}
