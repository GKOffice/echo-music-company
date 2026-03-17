"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────────────────

interface OwnedPoint {
  artistId: string;
  artistName: string;
  genre: string;
  points: number;
  purchasePrice: number;
  currentValue: number;
  royaltiesEarned: number;
  badgeEmoji: string;
}

interface MonthlyBreakdown {
  month: string;
  royalties: number;
  streams: number;
}

interface Portfolio {
  totalPoints: number;
  totalSpent: number;
  totalEarned: number;
  portfolioValue: number;
}

interface FanPortfolioData {
  portfolio: Portfolio;
  earningsOverTime: number[];
  earningsMonths: string[];
  ownedPoints: OwnedPoint[];
  monthlyBreakdown: MonthlyBreakdown[];
  nextPayout: string;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_DATA: FanPortfolioData = {
  portfolio: {
    totalPoints: 47,
    totalSpent: 4250,
    totalEarned: 892,
    portfolioValue: 5140,
  },
  earningsOverTime: [120, 145, 198, 210, 98, 121],
  earningsMonths: ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
  ownedPoints: [
    {
      artistId: "1",
      artistName: "Nova Vex",
      genre: "Afrobeats",
      points: 12,
      purchasePrice: 250,
      currentValue: 320,
      royaltiesEarned: 412,
      badgeEmoji: "💎",
    },
    {
      artistId: "2",
      artistName: "Lyra Bloom",
      genre: "Alt R&B",
      points: 8,
      purchasePrice: 150,
      currentValue: 178,
      royaltiesEarned: 234,
      badgeEmoji: "🔥",
    },
    {
      artistId: "5",
      artistName: "Melo Cipher",
      genre: "Hip-Hop",
      points: 5,
      purchasePrice: 200,
      currentValue: 240,
      royaltiesEarned: 156,
      badgeEmoji: "🔥",
    },
    {
      artistId: "6",
      artistName: "Indie Haze",
      genre: "Indie Pop",
      points: 22,
      purchasePrice: 50,
      currentValue: 42,
      royaltiesEarned: 90,
      badgeEmoji: "⭐",
    },
  ],
  monthlyBreakdown: [
    { month: "Mar 2026", royalties: 121, streams: 48200 },
    { month: "Feb 2026", royalties: 98, streams: 39100 },
    { month: "Jan 2026", royalties: 210, streams: 84000 },
    { month: "Dec 2025", royalties: 198, streams: 79200 },
    { month: "Nov 2025", royalties: 145, streams: 58000 },
    { month: "Oct 2025", royalties: 120, streams: 48000 },
  ],
  nextPayout: "April 1, 2026",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

function pctEarned(spent: number, earned: number): string {
  if (spent === 0) return "0%";
  return ((earned / spent) * 100).toFixed(1) + "%";
}

function isPositiveEarned(spent: number, currentValue: number): boolean {
  return currentValue >= spent;
}

// ─── SVG Line Chart ───────────────────────────────────────────────────────────

function EarningsChart({
  data,
  months,
}: {
  data: number[];
  months: string[];
}) {
  const W = 600;
  const H = 160;
  const PADDING_LEFT = 40;
  const PADDING_RIGHT = 20;
  const PADDING_TOP = 16;
  const PADDING_BOTTOM = 32;

  const plotW = W - PADDING_LEFT - PADDING_RIGHT;
  const plotH = H - PADDING_TOP - PADDING_BOTTOM;

  const minVal = Math.min(...data);
  const maxVal = Math.max(...data);
  const range = maxVal - minVal || 1;

  const xs = data.map(
    (_, i) => PADDING_LEFT + (i / (data.length - 1)) * plotW
  );
  const ys = data.map(
    (v) => PADDING_TOP + plotH - ((v - minVal) / range) * plotH
  );

  // Build smooth path using cardinal spline-style cubic bezier
  let pathD = `M ${xs[0]} ${ys[0]}`;
  for (let i = 1; i < xs.length; i++) {
    const cpx = (xs[i - 1] + xs[i]) / 2;
    pathD += ` C ${cpx} ${ys[i - 1]}, ${cpx} ${ys[i]}, ${xs[i]} ${ys[i]}`;
  }

  // Fill path (close down to baseline)
  const fillD =
    pathD +
    ` L ${xs[xs.length - 1]} ${PADDING_TOP + plotH} L ${xs[0]} ${PADDING_TOP + plotH} Z`;

  const lastX = xs[xs.length - 1];
  const lastY = ys[ys.length - 1];
  const lastVal = data[data.length - 1];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      style={{ height: 200 }}
      aria-label="Earnings over time chart"
    >
      <defs>
        <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.04" />
        </linearGradient>
        <linearGradient id="chartLine" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#10b981" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
        const y = PADDING_TOP + frac * plotH;
        const val = Math.round(maxVal - frac * range);
        return (
          <g key={frac}>
            <line
              x1={PADDING_LEFT}
              y1={y}
              x2={W - PADDING_RIGHT}
              y2={y}
              stroke="#2a2a38"
              strokeWidth="1"
            />
            <text
              x={PADDING_LEFT - 6}
              y={y + 4}
              textAnchor="end"
              fontSize="9"
              fill="#6b7280"
            >
              ${val}
            </text>
          </g>
        );
      })}

      {/* Fill */}
      <path d={fillD} fill="url(#chartFill)" />

      {/* Line */}
      <path
        d={pathD}
        fill="none"
        stroke="url(#chartLine)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Dots */}
      {xs.map((x, i) => (
        <circle
          key={i}
          cx={x}
          cy={ys[i]}
          r="4"
          fill="#0a0a0f"
          stroke="#10b981"
          strokeWidth="2"
        />
      ))}

      {/* Month labels */}
      {months.map((m, i) => (
        <text
          key={m}
          x={xs[i]}
          y={H - 6}
          textAnchor="middle"
          fontSize="10"
          fill="#9ca3af"
        >
          {m}
        </text>
      ))}

      {/* Last value label */}
      <rect
        x={lastX - 28}
        y={lastY - 22}
        width={56}
        height={18}
        rx="4"
        fill="#10b981"
        opacity="0.15"
      />
      <text
        x={lastX}
        y={lastY - 9}
        textAnchor="middle"
        fontSize="10"
        fontWeight="700"
        fill="#10b981"
      >
        ${lastVal}
      </text>
    </svg>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FanDashboardPage() {
  const { user, loading: authLoading } = useAuth();

  const { data, isLoading } = useQuery<FanPortfolioData>({
    queryKey: ["fan-portfolio"],
    enabled: !!user,
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/fan/portfolio`, {
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return MOCK_DATA;
      }
    },
  });

  const portfolio = data?.portfolio ?? MOCK_DATA.portfolio;
  const earningsOverTime = data?.earningsOverTime ?? MOCK_DATA.earningsOverTime;
  const earningsMonths = data?.earningsMonths ?? MOCK_DATA.earningsMonths;
  const ownedPoints = data?.ownedPoints ?? MOCK_DATA.ownedPoints;
  const monthlyBreakdown = data?.monthlyBreakdown ?? MOCK_DATA.monthlyBreakdown;
  const nextPayout = data?.nextPayout ?? MOCK_DATA.nextPayout;

  // Days until next payout
  const daysUntilPayout = (() => {
    const now = new Date();
    const payout = new Date(nextPayout);
    const diff = Math.ceil((payout.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  })();

  const totalValueChange = portfolio.portfolioValue - portfolio.totalSpent;
  const totalValueChangePct =
    portfolio.totalSpent > 0
      ? ((totalValueChange / portfolio.totalSpent) * 100).toFixed(1)
      : "0";

  // ── Auth Gate ───────────────────────────────────────────────────────────────
  if (!authLoading && !user) {
    return (
      <main className="min-h-screen bg-[#0a0a0f]">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] px-4 text-center">
          <div className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-8 max-w-sm w-full">
            <div className="text-4xl mb-4">🔒</div>
            <h2 className="text-xl font-bold text-[#f9fafb] mb-2">Sign in to view your portfolio</h2>
            <p className="text-[#9ca3af] text-sm mb-6">
              Track your owned points, royalties earned, and upcoming payouts all in one place.
            </p>
            <Link
              href="/auth/login"
              className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/auth/signup"
              className="block mt-3 text-sm text-[#9ca3af] hover:text-[#f9fafb] transition-colors"
            >
              New to Melodio? Create an account
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 pt-24 pb-16">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-black text-[#f9fafb]">My Royalty Portfolio</h1>
          <p className="text-[#9ca3af] mt-1 text-sm">
            Track your owned points, royalties earned, and upcoming payouts.
          </p>
        </div>

        {/* Overview Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {isLoading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-5">
                  <Skeleton className="h-3 w-1/2 mb-3" />
                  <Skeleton className="h-7 w-3/4 mb-2" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              ))
            : [
                {
                  label: "Points Owned",
                  value: String(portfolio.totalPoints),
                  sub: "across all artists",
                  color: "#8b5cf6",
                  icon: "💎",
                },
                {
                  label: "Total Spent",
                  value: formatCurrency(portfolio.totalSpent),
                  sub: "purchase price",
                  color: "#9ca3af",
                  icon: "🛒",
                },
                {
                  label: "Total Earned",
                  value: formatCurrency(portfolio.totalEarned),
                  sub: "royalties received",
                  color: "#10b981",
                  icon: "💰",
                },
                {
                  label: "Portfolio Value",
                  value: formatCurrency(portfolio.portfolioValue),
                  sub:
                    totalValueChange >= 0
                      ? `+${formatCurrency(totalValueChange)} (+${totalValueChangePct}%)`
                      : `${formatCurrency(totalValueChange)} (${totalValueChangePct}%)`,
                  color: totalValueChange >= 0 ? "#10b981" : "#ef4444",
                  icon: "📈",
                },
              ].map((card) => (
                <div
                  key={card.label}
                  className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-5 hover:border-[#8b5cf6]/50 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-base">{card.icon}</span>
                    <span className="text-xs text-[#9ca3af] font-medium">{card.label}</span>
                  </div>
                  <div className="text-xl sm:text-2xl font-black text-[#f9fafb] mb-1">
                    {card.value}
                  </div>
                  <div className="text-xs font-medium" style={{ color: card.color }}>
                    {card.sub}
                  </div>
                </div>
              ))}
        </div>

        {/* Earnings Chart */}
        <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-[#f9fafb]">Earnings Over Time</h2>
            <span className="text-xs text-[#9ca3af] bg-[#1a1a24] px-3 py-1 rounded-full">
              Last 6 months
            </span>
          </div>
          {isLoading ? (
            <Skeleton className="w-full h-[200px]" />
          ) : (
            <EarningsChart data={earningsOverTime} months={earningsMonths} />
          )}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Owned Points Table */}
          <section className="lg:col-span-2 bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
            <h2 className="text-lg font-bold text-[#f9fafb] mb-5">Owned Points by Artist</h2>
            <div className="overflow-x-auto -mx-2 px-2">
              <table className="w-full min-w-[560px]">
                <thead>
                  <tr className="text-xs text-[#6b7280] border-b border-[#2a2a38]">
                    <th className="text-left pb-3 font-medium">Artist</th>
                    <th className="text-right pb-3 font-medium">Points</th>
                    <th className="text-right pb-3 font-medium">Buy Price</th>
                    <th className="text-right pb-3 font-medium">Current Value</th>
                    <th className="text-right pb-3 font-medium">Royalties Earned</th>
                    <th className="text-right pb-3 font-medium">% Earned</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2a2a38]">
                  {isLoading
                    ? Array.from({ length: 4 }).map((_, i) => (
                        <tr key={i}>
                          {Array.from({ length: 6 }).map((__, j) => (
                            <td key={j} className="py-4 pr-2">
                              <Skeleton className="h-4 w-full" />
                            </td>
                          ))}
                        </tr>
                      ))
                    : ownedPoints.map((op) => {
                        const pct = pctEarned(
                          op.purchasePrice * op.points,
                          op.royaltiesEarned
                        );
                        const positive = isPositiveEarned(
                          op.purchasePrice,
                          op.currentValue
                        );
                        return (
                          <tr key={op.artistId} className="group hover:bg-[#1a1a24] transition-colors">
                            <td className="py-4 pr-4">
                              <div className="flex items-center gap-2">
                                <span className="text-base">{op.badgeEmoji}</span>
                                <div>
                                  <div className="font-semibold text-[#f9fafb] text-sm">
                                    {op.artistName}
                                  </div>
                                  <div className="text-xs text-[#6b7280]">{op.genre}</div>
                                </div>
                              </div>
                            </td>
                            <td className="py-4 text-right text-sm font-semibold text-[#f9fafb]">
                              {op.points}
                            </td>
                            <td className="py-4 text-right text-sm text-[#9ca3af]">
                              {formatCurrency(op.purchasePrice)}
                            </td>
                            <td className="py-4 text-right text-sm font-semibold">
                              <span style={{ color: positive ? "#10b981" : "#ef4444" }}>
                                {formatCurrency(op.currentValue)}
                              </span>
                            </td>
                            <td className="py-4 text-right text-sm font-semibold text-[#10b981]">
                              {formatCurrency(op.royaltiesEarned)}
                            </td>
                            <td className="py-4 text-right">
                              <span
                                className="text-xs font-bold px-2 py-1 rounded-full"
                                style={{
                                  background: positive ? "#10b98120" : "#ef444420",
                                  color: positive ? "#10b981" : "#ef4444",
                                }}
                              >
                                {pct}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                </tbody>
              </table>
            </div>
          </section>

          {/* Next Payout */}
          <aside className="space-y-4">
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
              <h2 className="text-base font-bold text-[#f9fafb] mb-4">Your Next Payout</h2>
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-4 w-2/3" />
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-center gap-4 py-4">
                    <div className="text-center">
                      <div className="text-4xl font-black text-[#8b5cf6]">{daysUntilPayout}</div>
                      <div className="text-xs text-[#9ca3af] mt-1">days away</div>
                    </div>
                    <div className="w-px h-12 bg-[#2a2a38]" />
                    <div className="text-center">
                      <div className="text-sm font-bold text-[#f9fafb]">{nextPayout}</div>
                      <div className="text-xs text-[#9ca3af] mt-1">payout date</div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-[#2a2a38] text-xs text-[#6b7280] text-center">
                    Royalties are distributed on the 1st of each month based on streaming data from the prior month.
                  </div>
                </>
              )}
            </section>

            {/* Quick summary */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
              <h2 className="text-base font-bold text-[#f9fafb] mb-4">Quick Stats</h2>
              <div className="space-y-3">
                {[
                  {
                    label: "Artists supported",
                    value: String(ownedPoints.length),
                    color: "#8b5cf6",
                  },
                  {
                    label: "Avg. earned per point",
                    value:
                      portfolio.totalPoints > 0
                        ? formatCurrency(
                            Math.round(portfolio.totalEarned / portfolio.totalPoints)
                          )
                        : "$0",
                    color: "#10b981",
                  },
                  {
                    label: "Lifetime payouts",
                    value: formatCurrency(portfolio.totalEarned),
                    color: "#f59e0b",
                  },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm text-[#9ca3af]">{s.label}</span>
                    <span
                      className="text-sm font-bold"
                      style={{ color: s.color }}
                    >
                      {s.value}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>

        {/* Monthly Breakdown Table */}
        <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
          <h2 className="text-lg font-bold text-[#f9fafb] mb-5">Monthly Royalty Breakdown</h2>
          <div className="overflow-x-auto -mx-2 px-2">
            <table className="w-full min-w-[400px]">
              <thead>
                <tr className="text-xs text-[#6b7280] border-b border-[#2a2a38]">
                  <th className="text-left pb-3 font-medium">Month</th>
                  <th className="text-right pb-3 font-medium">Royalties</th>
                  <th className="text-right pb-3 font-medium">Streams Contributing</th>
                  <th className="text-right pb-3 font-medium">Per Stream</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a38]">
                {isLoading
                  ? Array.from({ length: 6 }).map((_, i) => (
                      <tr key={i}>
                        {Array.from({ length: 4 }).map((__, j) => (
                          <td key={j} className="py-4 pr-2">
                            <Skeleton className="h-4 w-full" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : monthlyBreakdown.map((row, idx) => (
                      <tr
                        key={row.month}
                        className={`hover:bg-[#1a1a24] transition-colors ${
                          idx === 0 ? "bg-[#10b981]/5" : ""
                        }`}
                      >
                        <td className="py-4 text-sm font-medium text-[#f9fafb]">
                          {row.month}
                          {idx === 0 && (
                            <span className="ml-2 text-xs bg-[#10b981]/20 text-[#10b981] px-2 py-0.5 rounded-full">
                              Latest
                            </span>
                          )}
                        </td>
                        <td className="py-4 text-right text-sm font-bold text-[#10b981]">
                          {formatCurrency(row.royalties)}
                        </td>
                        <td className="py-4 text-right text-sm text-[#9ca3af]">
                          {formatNumber(row.streams)}
                        </td>
                        <td className="py-4 text-right text-xs text-[#6b7280]">
                          ${((row.royalties / row.streams) * 1000).toFixed(3)}/K
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
