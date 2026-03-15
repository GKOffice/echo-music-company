"use client";

import Link from "next/link";
import Navbar from "../../components/Navbar";
import { formatNumber, formatCurrency } from "../../lib/api";

const stats = [
  { label: "Monthly Listeners", value: "284K", change: "+12%", up: true },
  { label: "Total Streams", value: "4.2M", change: "+8%", up: true },
  { label: "Revenue MTD", value: "$8,412", change: "+23%", up: true },
  {
    label: "ECHO Score",
    value: "94",
    change: "💎 Diamond",
    tier: true,
  },
];

const releases = [
  {
    id: "r1",
    title: "Midnight Drive",
    status: "live",
    streams: 1240000,
    revenue: 4960,
    pointsSold: 12,
    releaseDate: "Feb 14, 2026",
  },
  {
    id: "r2",
    title: "Neon Fever",
    status: "live",
    streams: 860000,
    revenue: 3440,
    pointsSold: 8,
    releaseDate: "Jan 20, 2026",
  },
  {
    id: "r3",
    title: "Dark Matter EP",
    status: "processing",
    streams: 0,
    revenue: 0,
    pointsSold: 0,
    releaseDate: "Mar 22, 2026",
  },
];

const activity = [
  { icon: "📀", text: "Midnight Drive added to 3 editorial playlists", time: "2h ago", accent: "#8b5cf6" },
  { icon: "💰", text: "2 ECHO Points sold · $500 earned", time: "5h ago", accent: "#10b981" },
  { icon: "🏆", text: "Milestone: 1M streams on Midnight Drive", time: "1d ago", accent: "#f59e0b" },
  { icon: "📈", text: "Monthly listeners up 12% — ECHO Score raised to 94", time: "2d ago", accent: "#8b5cf6" },
  { icon: "💰", text: "Royalty payout: $4,960 distributed to 12 holders", time: "3d ago", accent: "#10b981" },
  { icon: "🎤", text: "Distribution Agent deployed Neon Fever to 47 DSPs", time: "1w ago", accent: "#9ca3af" },
];

const quickActions = [
  { label: "Upload Song", icon: "⬆️", href: "/dashboard/upload", color: "#8b5cf6" },
  { label: "Drop Points", icon: "💎", href: "/points", color: "#10b981" },
  { label: "Browse Beats", icon: "🎛️", href: "/dashboard/beats", color: "#f59e0b" },
  { label: "View Analytics", icon: "📊", href: "/dashboard/analytics", color: "#3b82f6" },
];

function statusBadge(status: string) {
  if (status === "live") return { label: "Live", bg: "#10b981/20", text: "#34d399" };
  if (status === "processing") return { label: "Processing", bg: "#f59e0b/20", text: "#fbbf24" };
  return { label: "Draft", bg: "#2a2a3a", text: "#9ca3af" };
}

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 pt-24 pb-16">

        {/* Header */}
        <div className="flex items-start justify-between mb-10 flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-black text-[#f9fafb]">Artist Dashboard</h1>
            <p className="text-[#9ca3af] mt-1">Welcome back, Nova Vex</p>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 bg-[#10b981] rounded-full animate-pulse" />
            <span className="text-[#9ca3af]">All agents online</span>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {stats.map((s) => (
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
              <div className="space-y-3">
                {releases.map((r) => {
                  const badge = statusBadge(r.status);
                  return (
                    <div key={r.id} className="flex items-center gap-4 p-4 bg-[#0a0a0f] rounded-lg border border-[#2a2a3a] hover:border-[#8b5cf6] transition-colors group cursor-pointer">
                      {/* Artwork placeholder */}
                      <div className="w-12 h-12 bg-[#2a2a3a] rounded-lg shrink-0 flex items-center justify-center text-xl">
                        🎵
                      </div>
                      {/* Info */}
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
                      {/* Stats */}
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
            </section>

            {/* Recent Activity */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-5">Recent Activity</h2>
              <div className="space-y-4">
                {activity.map((a, i) => (
                  <div key={i} className="flex items-start gap-3">
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

            {/* ECHO Points */}
            <section className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h2 className="text-lg font-bold text-[#f9fafb] mb-5">ECHO Points</h2>

              {/* Progress */}
              <div className="mb-5">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-[#9ca3af]">Points Sold</span>
                  <span className="font-semibold text-[#f9fafb]">12 / 15</span>
                </div>
                <div className="w-full h-2 bg-[#2a2a3a] rounded-full overflow-hidden">
                  <div className="h-full bg-[#8b5cf6] rounded-full" style={{ width: "80%" }} />
                </div>
                <div className="text-xs text-[#9ca3af] mt-2">3 points remaining · $250/pt</div>
              </div>

              <div className="space-y-3 mb-5">
                <div className="flex justify-between items-center py-2 border-b border-[#2a2a3a]">
                  <span className="text-sm text-[#9ca3af]">Total Raised</span>
                  <span className="font-semibold text-[#f9fafb]">$3,000</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-[#2a2a3a]">
                  <span className="text-sm text-[#9ca3af]">Paid to Holders</span>
                  <span className="font-semibold text-[#10b981]">$4,960</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-[#9ca3af]">Next Payout</span>
                  <span className="font-semibold text-[#f9fafb]">Apr 1, 2026</span>
                </div>
              </div>

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
                    className="flex flex-col items-center justify-center gap-2 p-4 bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] hover:border-[#8b5cf6] transition-colors group cursor-pointer"
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
