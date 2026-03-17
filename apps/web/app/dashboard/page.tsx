"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import Navbar from "../../components/Navbar";
import { Skeleton } from "../../components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import {
  fetchMyArtist,
  fetchMyReleases,
  fetchMyActivity,
  formatNumber,
  formatCurrency,
} from "../../lib/api";

const quickActions = [
  { label: "Upload Song", icon: "⬆️", href: "/dashboard/upload", color: "#8b5cf6" },
  { label: "Drop Points", icon: "💎", href: "/points", color: "#10b981" },
  { label: "Browse Beats", icon: "🎛️", href: "/dashboard/beats", color: "#f59e0b" },
  { label: "View Analytics", icon: "📊", href: "/dashboard/analytics", color: "#3b82f6" },
];

function statusBadge(status: string) {
  if (status === "live") return { label: "Live", text: "#34d399" };
  if (status === "processing") return { label: "Processing", text: "#fbbf24" };
  return { label: "Draft", text: "#9ca3af" };
}

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: artist, isLoading: artistLoading } = useQuery({
    queryKey: ["my-artist"],
    queryFn: fetchMyArtist,
  });

  const { data: releases = [], isLoading: releasesLoading } = useQuery({
    queryKey: ["my-releases"],
    queryFn: fetchMyReleases,
  });

  const { data: activity = [], isLoading: activityLoading } = useQuery({
    queryKey: ["my-activity"],
    queryFn: fetchMyActivity,
  });

  const stats = artist
    ? [
        { label: "Monthly Listeners", value: formatNumber(artist.monthly_listeners), change: "+12%", up: true },
        { label: "Total Streams", value: formatNumber(artist.total_streams), change: "+8%", up: true },
        { label: "Revenue MTD", value: formatCurrency(artist.revenue_mtd), change: "+23%", up: true },
        { label: "Melodio Score", value: String(artist.melodio_score), change: `💎 ${artist.tier}`, tier: true },
      ]
    : null;

  const pointsSoldPct = artist
    ? Math.round((artist.points_sold / artist.points_total) * 100)
    : 0;

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 pt-24 pb-16">

        {/* Header */}
        <div className="flex items-start justify-between mb-10 flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-black text-[#f9fafb]">Artist Dashboard</h1>
            <p className="text-[#9ca3af] mt-1">
              Welcome back,{" "}
              {artistLoading
                ? <span className="inline-block w-24 h-4 bg-[#1a1a24] rounded animate-pulse align-middle" />
                : user?.name ?? artist?.name ?? "Artist"}
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            <span className="text-[#9ca3af]">All agents online</span>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {artistLoading || !stats
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-5">
                  <Skeleton className="h-4 w-3/4 mb-3" />
                  <Skeleton className="h-8 w-1/2 mb-2" />
                  <Skeleton className="h-4 w-1/3" />
                </div>
              ))
            : stats.map((s) => (
                <div key={s.label} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-5 hover:border-[#8b5cf6] transition-colors">
                  <div className="text-[#9ca3af] text-sm mb-2">{s.label}</div>
                  <div className="text-white font-bold text-2xl mb-1">{s.value}</div>
                  {s.tier ? (
                    <span className="inline-flex items-center px-2 py-0.5 bg-[#8b5cf6]/20 text-[#a78bfa] text-xs rounded-full">
                      {s.change}
                    </span>
                  ) : (
                    <div className={`text-sm font-medium ${s.up ? "text-[#10b981]" : "text-[#ef4444]"}`}>
                      {s.change} this month
                    </div>
                  )}
                </div>
              ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column — Releases + Activity */}
          <div className="lg:col-span-2 space-y-6">

            {/* My Releases */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-bold text-[#f9fafb]">My Releases</h2>
                <Link href="/dashboard/upload" className="text-sm text-[#8b5cf6] hover:underline">+ Upload New</Link>
              </div>
              <div className="overflow-x-auto -mx-2 px-2">
                <div className="space-y-3 min-w-[320px]">
                  {releasesLoading
                    ? Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="flex items-center gap-4 p-4 bg-[#0a0a0f] rounded-lg border border-[#2a2a3a]">
                          <Skeleton className="w-12 h-12 rounded-lg shrink-0" />
                          <div className="flex-1 space-y-2">
                            <Skeleton className="h-4 w-1/2" />
                            <Skeleton className="h-3 w-1/3" />
                          </div>
                          <Skeleton className="h-8 w-20 shrink-0 hidden sm:block" />
                        </div>
                      ))
                    : releases.map((r) => {
                        const badge = statusBadge(r.status);
                        return (
                          <div key={r.id} className="flex items-center gap-4 p-4 bg-[#0a0a0f] rounded-lg border border-[#2a2a3a] hover:border-[#8b5cf6] transition-colors cursor-pointer">
                            <div className="w-12 h-12 bg-[#2a2a3a] rounded-lg shrink-0 flex items-center justify-center text-xl">
                              🎵
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-semibold text-[#f9fafb] truncate">{r.title}</span>
                                <span
                                  className="text-xs px-2 py-0.5 rounded-full shrink-0"
                                  style={{ background: `${badge.text}20`, color: badge.text }}
                                >
                                  {badge.label}
                                </span>
                              </div>
                              <div className="text-xs text-[#9ca3af]">{r.releaseDate}</div>
                            </div>
                            <div className="hidden sm:grid grid-cols-3 gap-6 text-right shrink-0">
                              <div>
                                <div className="text-sm font-semibold text-[#f9fafb]">{r.streams > 0 ? formatNumber(r.streams) : "—"}</div>
                                <div className="text-xs text-[#9ca3af]">Streams</div>
                              </div>
                              <div>
                                <div className="text-sm font-semibold text-[#f9fafb]">{r.revenue > 0 ? formatCurrency(r.revenue) : "—"}</div>
                                <div className="text-xs text-[#9ca3af]">Revenue</div>
                              </div>
                              <div>
                                <div className="text-sm font-semibold text-[#f9fafb]">{r.pointsSold > 0 ? r.pointsSold : "—"}</div>
                                <div className="text-xs text-[#9ca3af]">Pts Sold</div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                </div>
              </div>
            </section>

            {/* Recent Activity */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-5">Recent Activity</h2>
              <div className="space-y-4">
                {activityLoading
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
                        <div className="flex-1 space-y-1">
                          <Skeleton className="h-4 w-3/4" />
                        </div>
                        <Skeleton className="h-4 w-12 shrink-0" />
                      </div>
                    ))
                  : activity.map((a, i) => (
                      <div key={a.id ?? i} className="flex items-start gap-3">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0"
                          style={{ background: `${a.accent}20` }}
                        >
                          {a.icon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-[#e8e8f0]">{a.text}</div>
                        </div>
                        <div className="text-xs text-[#9ca3af] shrink-0">{a.time}</div>
                      </div>
                    ))}
              </div>
            </section>
          </div>

          {/* Right column — Points + Quick Actions */}
          <div className="space-y-6">

            {/* Melodio Points */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-5">Melodio Points</h2>

              {artistLoading || !artist ? (
                <div className="space-y-3 mb-5">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-2 w-full" />
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-4 w-full mt-3" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                </div>
              ) : (
                <>
                  <div className="mb-5">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-[#9ca3af]">Points Sold</span>
                      <span className="font-semibold text-[#f9fafb]">{artist.points_sold} / {artist.points_total}</span>
                    </div>
                    <div className="w-full h-2 bg-[#2a2a3a] rounded-full overflow-hidden">
                      <div className="h-full bg-[#8b5cf6] rounded-full" style={{ width: `${pointsSoldPct}%` }} />
                    </div>
                    <div className="text-xs text-[#9ca3af] mt-2">
                      {artist.points_total - artist.points_sold} remaining · ${artist.price_per_point}/pt
                    </div>
                  </div>

                  <div className="space-y-3 mb-5">
                    <div className="flex justify-between items-center py-2 border-b border-[#2a2a3a]">
                      <span className="text-sm text-[#9ca3af]">Total Raised</span>
                      <span className="font-semibold text-[#f9fafb]">{formatCurrency(artist.total_raised)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-[#2a2a3a]">
                      <span className="text-sm text-[#9ca3af]">Paid to Holders</span>
                      <span className="font-semibold text-[#10b981]">{formatCurrency(artist.paid_to_holders)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-sm text-[#9ca3af]">Next Payout</span>
                      <span className="font-semibold text-[#f9fafb]">{artist.next_payout}</span>
                    </div>
                  </div>
                </>
              )}

              <Link
                href="/points"
                className="block w-full text-center bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2.5 rounded-lg transition-colors"
              >
                Drop More Points
              </Link>
            </section>

            {/* Quick Actions */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 gap-3">
                {quickActions.map((action) => (
                  <Link
                    key={action.label}
                    href={action.href}
                    className="flex flex-col items-center justify-center gap-2 p-4 bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] hover:border-[#8b5cf6] transition-colors group"
                  >
                    <span className="text-2xl">{action.icon}</span>
                    <span className="text-xs font-medium text-[#9ca3af] group-hover:text-[#f9fafb] transition-colors text-center">
                      {action.label}
                    </span>
                  </Link>
                ))}
              </div>
            </section>

            {/* Agent Status */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-4">Agent Activity</h2>
              <div className="space-y-3">
                {[
                  { name: "A&R Agent", status: "Reviewing submissions", color: "#8b5cf6" },
                  { name: "Distribution", status: "DSPs synced", color: "#10b981" },
                  { name: "Marketing", status: "Running campaigns", color: "#f59e0b" },
                  { name: "Analytics", status: "Tracking streams", color: "#3b82f6" },
                ].map((agent) => (
                  <div key={agent.name} className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full animate-pulse shrink-0" style={{ background: agent.color }} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[#f9fafb]">{agent.name}</div>
                      <div className="text-xs text-[#9ca3af] truncate">{agent.status}</div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
