"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";

const API_URL = typeof window !== "undefined" && window.location.hostname !== "localhost" ? "https://api-production-14b6.up.railway.app" : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

// ─── Types ────────────────────────────────────────────────────────────────────

type LeaderboardTab = "artists" | "supporters" | "rising";

interface TopArtist {
  rank: number;
  name: string;
  genre: string;
  monthlyStreams: number;
  melodioScore: number;
  pointsSold: number;
  badge: string;
}

interface TopSupporter {
  rank: number;
  username: string;
  pointsOwned: number;
  totalSpent: number;
  artistsSupported: number;
  badge: string;
}

interface RisingStar {
  rank: number;
  name: string;
  genre: string;
  growthPct: number;
  weeksOnPlatform: number;
  badge: string;
}

interface LeaderboardData {
  topArtists: TopArtist[];
  topSupporters: TopSupporter[];
  risingStars: RisingStar[];
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_DATA: LeaderboardData = {
  topArtists: [
    { rank: 1, name: "Nova Vex", genre: "Afrobeats", monthlyStreams: 284000, melodioScore: 94, pointsSold: 12, badge: "🔥" },
    { rank: 2, name: "Melo Cipher", genre: "Hip-Hop", monthlyStreams: 210000, melodioScore: 89, pointsSold: 13, badge: "🚀" },
    { rank: 3, name: "Lyra Bloom", genre: "Alt R&B", monthlyStreams: 142000, melodioScore: 87, pointsSold: 12, badge: "💎" },
    { rank: 4, name: "Khai Dusk", genre: "Trap Soul", monthlyStreams: 98000, melodioScore: 82, pointsSold: 13, badge: "⚡" },
    { rank: 5, name: "Zara Sol", genre: "Pop", monthlyStreams: 67000, melodioScore: 76, pointsSold: 10, badge: "🎯" },
    { rank: 6, name: "Indie Haze", genre: "Indie Pop", monthlyStreams: 41000, melodioScore: 71, pointsSold: 10, badge: "🔥" },
  ],
  topSupporters: [
    { rank: 1, username: "m***r", pointsOwned: 47, totalSpent: 4250, artistsSupported: 4, badge: "💎" },
    { rank: 2, username: "b***x", pointsOwned: 38, totalSpent: 3800, artistsSupported: 6, badge: "🔥" },
    { rank: 3, username: "s***k", pointsOwned: 31, totalSpent: 2900, artistsSupported: 3, badge: "🚀" },
    { rank: 4, username: "t***o", pointsOwned: 25, totalSpent: 2100, artistsSupported: 5, badge: "🎯" },
    { rank: 5, username: "j***n", pointsOwned: 22, totalSpent: 1650, artistsSupported: 4, badge: "⚡" },
  ],
  risingStars: [
    { rank: 1, name: "Indie Haze", genre: "Indie Pop", growthPct: 89, weeksOnPlatform: 6, badge: "🚀" },
    { rank: 2, name: "Khai Dusk", genre: "Trap Soul", growthPct: 67, weeksOnPlatform: 12, badge: "⚡" },
    { rank: 3, name: "Zara Sol", genre: "Pop", growthPct: 54, weeksOnPlatform: 18, badge: "🎯" },
    { rank: 4, name: "Lyra Bloom", genre: "Alt R&B", growthPct: 41, weeksOnPlatform: 32, badge: "🔥" },
    { rank: 5, name: "Nova Vex", genre: "Afrobeats", growthPct: 34, weeksOnPlatform: 38, badge: "💎" },
  ],
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(0) + "K";
  return String(n);
}

function formatCurrency(n: number): string {
  return "$" + n.toLocaleString("en-US");
}

function rankBadge(rank: number): string {
  if (rank === 1) return "🥇";
  if (rank === 2) return "🥈";
  if (rank === 3) return "🥉";
  return `#${rank}`;
}

function rankRowStyle(rank: number): string {
  if (rank === 1) return "border-l-2 border-l-[#f59e0b] bg-[#f59e0b]/5";
  if (rank === 2) return "border-l-2 border-l-[#d1d5db] bg-[#d1d5db]/5";
  if (rank === 3) return "border-l-2 border-l-[#cd7f32] bg-[#cd7f32]/5";
  return "";
}

function GenreBadge({ genre }: { genre: string }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[#8b5cf6]/15 text-[#a78bfa]">
      {genre}
    </span>
  );
}

// ─── Score Bar ────────────────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 sm:w-20 h-1.5 bg-[#2a2a38] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[#8b5cf6] to-[#10b981]"
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-sm font-bold text-[#f9fafb]">{score}</span>
    </div>
  );
}

// ─── Skeleton Rows ────────────────────────────────────────────────────────────

function SkeletonRows({ cols }: { cols: number }) {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: cols }).map((__, j) => (
            <td key={j} className="px-4 py-4">
              <Skeleton className="h-4 w-full" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// ─── Top Artists Table ────────────────────────────────────────────────────────

function TopArtistsTable({
  artists,
  isLoading,
}: {
  artists: TopArtist[];
  isLoading: boolean;
}) {
  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0">
      <table className="w-full min-w-[560px]">
        <thead>
          <tr className="text-xs text-[#6b7280] border-b border-[#2a2a38]">
            <th className="text-left px-4 pb-3 font-medium">Rank</th>
            <th className="text-left px-4 pb-3 font-medium">Artist</th>
            <th className="text-right px-4 pb-3 font-medium">Monthly Streams</th>
            <th className="text-right px-4 pb-3 font-medium hidden sm:table-cell">Melodio Score</th>
            <th className="text-right px-4 pb-3 font-medium">Points Sold</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#2a2a38]">
          {isLoading ? (
            <SkeletonRows cols={5} />
          ) : (
            artists.map((artist) => (
              <tr
                key={artist.rank}
                className={`hover:bg-[#1a1a24] transition-colors ${rankRowStyle(artist.rank)}`}
              >
                <td className="px-4 py-4">
                  <span
                    className={`text-lg font-black ${
                      artist.rank <= 3
                        ? ""
                        : "text-sm text-[#6b7280]"
                    }`}
                  >
                    {rankBadge(artist.rank)}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{artist.badge}</span>
                    <div>
                      <div className="font-semibold text-[#f9fafb] text-sm leading-tight">
                        {artist.name}
                      </div>
                      <div className="mt-0.5">
                        <GenreBadge genre={artist.genre} />
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="text-sm font-semibold text-[#f9fafb]">
                    {formatNumber(artist.monthlyStreams)}
                  </span>
                </td>
                <td className="px-4 py-4 text-right hidden sm:table-cell">
                  <ScoreBar score={artist.melodioScore} />
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="text-sm font-bold text-[#10b981]">
                    {artist.pointsSold}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ─── Top Supporters Table ─────────────────────────────────────────────────────

function TopSupportersTable({
  supporters,
  isLoading,
}: {
  supporters: TopSupporter[];
  isLoading: boolean;
}) {
  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0">
      <table className="w-full min-w-[500px]">
        <thead>
          <tr className="text-xs text-[#6b7280] border-b border-[#2a2a38]">
            <th className="text-left px-4 pb-3 font-medium">Rank</th>
            <th className="text-left px-4 pb-3 font-medium">Username</th>
            <th className="text-right px-4 pb-3 font-medium">Points Owned</th>
            <th className="text-right px-4 pb-3 font-medium hidden sm:table-cell">Total Earned for Artists</th>
            <th className="text-right px-4 pb-3 font-medium">Artists</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#2a2a38]">
          {isLoading ? (
            <SkeletonRows cols={5} />
          ) : (
            supporters.map((s) => (
              <tr
                key={s.rank}
                className={`hover:bg-[#1a1a24] transition-colors ${rankRowStyle(s.rank)}`}
              >
                <td className="px-4 py-4">
                  <span
                    className={`text-lg font-black ${
                      s.rank <= 3 ? "" : "text-sm text-[#6b7280]"
                    }`}
                  >
                    {rankBadge(s.rank)}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{s.badge}</span>
                    <span className="font-semibold text-[#f9fafb] text-sm font-mono">
                      {s.username}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="text-sm font-bold text-[#8b5cf6]">{s.pointsOwned}</span>
                </td>
                <td className="px-4 py-4 text-right hidden sm:table-cell">
                  <span className="text-sm font-semibold text-[#10b981]">
                    {formatCurrency(s.totalSpent)}
                  </span>
                </td>
                <td className="px-4 py-4 text-right">
                  <span className="text-sm text-[#d1d5db]">{s.artistsSupported}</span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ─── Rising Stars Table ───────────────────────────────────────────────────────

function RisingStarsTable({
  stars,
  isLoading,
}: {
  stars: RisingStar[];
  isLoading: boolean;
}) {
  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0">
      <table className="w-full min-w-[480px]">
        <thead>
          <tr className="text-xs text-[#6b7280] border-b border-[#2a2a38]">
            <th className="text-left px-4 pb-3 font-medium">Rank</th>
            <th className="text-left px-4 pb-3 font-medium">Artist</th>
            <th className="text-right px-4 pb-3 font-medium">Stream Growth</th>
            <th className="text-right px-4 pb-3 font-medium hidden sm:table-cell">Weeks on Platform</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[#2a2a38]">
          {isLoading ? (
            <SkeletonRows cols={4} />
          ) : (
            stars.map((star) => (
              <tr
                key={star.rank}
                className={`hover:bg-[#1a1a24] transition-colors ${rankRowStyle(star.rank)}`}
              >
                <td className="px-4 py-4">
                  <span
                    className={`text-lg font-black ${
                      star.rank <= 3 ? "" : "text-sm text-[#6b7280]"
                    }`}
                  >
                    {rankBadge(star.rank)}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-2">
                    <span className="text-base">{star.badge}</span>
                    <div>
                      <div className="font-semibold text-[#f9fafb] text-sm leading-tight">
                        {star.name}
                      </div>
                      <div className="mt-0.5">
                        <GenreBadge genre={star.genre} />
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 sm:w-20 h-1.5 bg-[#2a2a38] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.min(star.growthPct, 100)}%`,
                          background:
                            star.growthPct >= 70
                              ? "#10b981"
                              : star.growthPct >= 40
                              ? "#f59e0b"
                              : "#8b5cf6",
                        }}
                      />
                    </div>
                    <span
                      className="text-sm font-bold"
                      style={{
                        color:
                          star.growthPct >= 70
                            ? "#10b981"
                            : star.growthPct >= 40
                            ? "#f59e0b"
                            : "#8b5cf6",
                      }}
                    >
                      +{star.growthPct}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-4 text-right hidden sm:table-cell">
                  <span className="text-sm text-[#9ca3af]">
                    {star.weeksOnPlatform}w
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function LeaderboardsPage() {
  const [activeTab, setActiveTab] = useState<LeaderboardTab>("artists");

  const { data: artistsData, isLoading: artistsLoading } = useQuery<{ artists: TopArtist[] }>({
    queryKey: ["leaderboards-artists"],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/leaderboards/artists`);
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return { artists: MOCK_DATA.topArtists };
      }
    },
  });

  const { data: supportersData, isLoading: supportersLoading } = useQuery<{ supporters: TopSupporter[] }>({
    queryKey: ["leaderboards-supporters"],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/leaderboards/supporters`);
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return { supporters: MOCK_DATA.topSupporters };
      }
    },
  });

  const { data: risingData, isLoading: risingLoading } = useQuery<{ rising: RisingStar[] }>({
    queryKey: ["leaderboards-rising"],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/leaderboards/rising-stars`);
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return { rising: MOCK_DATA.risingStars };
      }
    },
  });

  const topArtists = artistsData?.artists ?? MOCK_DATA.topArtists;
  const topSupporters = supportersData?.supporters ?? MOCK_DATA.topSupporters;
  const risingStars = risingData?.rising ?? MOCK_DATA.risingStars;

  const TABS: { key: LeaderboardTab; label: string; icon: string; desc: string }[] = [
    { key: "artists", label: "Top Artists", icon: "🎤", desc: "Ranked by monthly streams and Melodio Score" },
    { key: "supporters", label: "Top Supporters", icon: "💎", desc: "Fans who've backed the most artists" },
    { key: "rising", label: "Rising Stars", icon: "🚀", desc: "Fastest-growing artists week-over-week" },
  ];

  const activeTabDef = TABS.find((t) => t.key === activeTab)!;

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-5xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <section className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/10 border border-[#8b5cf6]/30 text-[#a78bfa] text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
            🏆 Updated weekly
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#f9fafb] mb-3">
            Melodio Leaderboards
          </h1>
          <p className="text-[#9ca3af] text-base max-w-lg mx-auto">
            The top artists, supporters, and rising talents on the Melodio platform — updated every week.
          </p>
        </section>

        {/* Tabs */}
        <div className="flex flex-col sm:flex-row gap-3 mb-8">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 flex flex-col items-center gap-1.5 px-4 py-4 rounded-2xl border transition-all duration-200 text-center ${
                activeTab === tab.key
                  ? "bg-[#8b5cf6]/10 border-[#8b5cf6]/40 text-[#f9fafb]"
                  : "bg-[#13131a] border-[#2a2a38] text-[#9ca3af] hover:text-[#f9fafb] hover:border-[#2a2a38]"
              }`}
            >
              <span className="text-2xl">{tab.icon}</span>
              <span className="font-semibold text-sm">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab description */}
        <p className="text-sm text-[#6b7280] mb-4 px-1">{activeTabDef.desc}</p>

        {/* Rank legend */}
        <div className="flex flex-wrap items-center gap-4 mb-4 px-1">
          {[
            { color: "#f59e0b", label: "1st Place" },
            { color: "#d1d5db", label: "2nd Place" },
            { color: "#cd7f32", label: "3rd Place" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div
                className="w-2.5 h-2.5 rounded-sm"
                style={{ background: item.color }}
              />
              <span className="text-xs text-[#6b7280]">{item.label}</span>
            </div>
          ))}
        </div>

        {/* Table Card */}
        <section className="bg-[#13131a] border border-[#2a2a38] rounded-2xl overflow-hidden">
          <div className="p-4 sm:p-6">
            {activeTab === "artists" && (
              <TopArtistsTable
                artists={topArtists}
                isLoading={artistsLoading}
              />
            )}
            {activeTab === "supporters" && (
              <TopSupportersTable
                supporters={topSupporters}
                isLoading={supportersLoading}
              />
            )}
            {activeTab === "rising" && (
              <RisingStarsTable
                stars={risingStars}
                isLoading={risingLoading}
              />
            )}
          </div>

          {/* Footer note */}
          <div className="border-t border-[#2a2a38] px-4 sm:px-6 py-4">
            <p className="text-xs text-[#6b7280]">
              {activeTab === "supporters"
                ? "Supporter usernames are partially masked to protect privacy. \"Total earned for artists\" reflects the amount paid into the artist ecosystem."
                : activeTab === "rising"
                ? "Growth % calculated week-over-week based on streaming data. Artists must have been on Melodio for at least 4 weeks to qualify."
                : "Rankings updated weekly based on streaming data, Melodio Score, and point activity."}
            </p>
          </div>
        </section>

        {/* Badge Legend */}
        <section className="mt-8 bg-[#13131a] border border-[#2a2a38] rounded-2xl p-5">
          <h3 className="text-sm font-bold text-[#f9fafb] mb-3">Badge Guide</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              { badge: "🔥", name: "Hot Streak", desc: "Consistent growth" },
              { badge: "💎", name: "Diamond Hands", desc: "Long-term holder" },
              { badge: "🚀", name: "Rocket", desc: "Rapid rise" },
              { badge: "🎯", name: "Tastemaker", desc: "Early supporter" },
              { badge: "⚡", name: "Lightning", desc: "Breakout velocity" },
            ].map((item) => (
              <div
                key={item.badge}
                className="flex items-start gap-2 p-3 bg-[#0a0a0f] rounded-xl border border-[#2a2a38]"
              >
                <span className="text-lg shrink-0">{item.badge}</span>
                <div>
                  <div className="text-xs font-semibold text-[#f9fafb]">{item.name}</div>
                  <div className="text-xs text-[#6b7280]">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
