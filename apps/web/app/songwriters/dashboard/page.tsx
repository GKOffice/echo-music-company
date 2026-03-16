"use client";

import Link from "next/link";
import Navbar from "../../../components/Navbar";

const STATS = [
  { label: "Songs Registered", value: "12", icon: "🎵" },
  { label: "Total Collected", value: "$4,280", icon: "💰" },
  { label: "This Quarter", value: "$820", icon: "📈", change: "+15%" },
  { label: "Active Sync Pitches", value: "3", icon: "🎬" },
];

const SONGS = [
  {
    title: "Midnight Protocol",
    coWriters: ["Aria Khan"],
    ascap: true,
    bmi: true,
    mlc: true,
    streams: "142K",
    earnings: "$310",
    dealRoom: true,
  },
  {
    title: "Golden Hours",
    coWriters: [],
    ascap: true,
    bmi: true,
    mlc: true,
    streams: "89K",
    earnings: "$190",
    dealRoom: false,
  },
  {
    title: "Signal Lost",
    coWriters: ["Marcus Reid", "Neon Flux"],
    ascap: true,
    bmi: false,
    mlc: true,
    streams: "210K",
    earnings: "$450",
    dealRoom: true,
  },
  {
    title: "Wavelength",
    coWriters: [],
    ascap: false,
    bmi: false,
    mlc: false,
    streams: "—",
    earnings: "—",
    dealRoom: false,
  },
];

const REVENUE_BARS = [
  { label: "Performance Royalties", pct: 45, color: "#8b5cf6" },
  { label: "Mechanical", pct: 25, color: "#10b981" },
  { label: "Sync", pct: 20, color: "#f59e0b" },
  { label: "YouTube / Other", pct: 10, color: "#60a5fa" },
];

const COLLECTION_STATUS = [
  { org: "ASCAP/BMI", status: "registered", label: "Registered" },
  { org: "MLC", status: "registered", label: "Registered" },
  { org: "SoundExchange", status: "registered", label: "Registered" },
  { org: "Songtrust (international)", status: "progress", label: "In Progress" },
  { org: "YouTube Content ID", status: "registered", label: "Active" },
];

const SYNC_PIPELINE = [
  {
    song: "Midnight Protocol",
    project: "Netflix — Thriller Drama Pilot",
    status: "Under Review",
    fee: "$5,000–$12,000",
    color: "#f59e0b",
  },
  {
    song: "Golden Hours",
    project: "Toyota — Global Campaign 2026",
    status: "Shortlisted",
    fee: "$18,000–$35,000",
    color: "#10b981",
  },
  {
    song: "Signal Lost",
    project: "HBO — Season Trailer",
    status: "Pitched",
    fee: "$8,000–$20,000",
    color: "#8b5cf6",
  },
];

const COWRITE_LISTINGS = [
  {
    title: "Looking for R&B Co-writer — EP Project",
    offers: 4,
    views: 128,
    status: "Active",
  },
  {
    title: "Topline needed for Pop single",
    offers: 7,
    views: 203,
    status: "Active",
  },
];

export default function SongwriterDashboardPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 pt-28 pb-20">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-black text-[#f9fafb]">Songwriter Dashboard</h1>
            <p className="text-[#9ca3af] text-sm mt-1">
              Manage your catalog, track collections, and grow your income.
            </p>
          </div>
          <Link
            href="/songwriters/register"
            className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-4 py-2.5 rounded-lg transition-colors"
          >
            + Register Song
          </Link>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5"
            >
              <div className="text-xl mb-1">{stat.icon}</div>
              <div className="text-xl font-black text-[#f9fafb]">
                {stat.value}
                {stat.change && (
                  <span className="text-sm font-semibold text-[#10b981] ml-2">
                    {stat.change}
                  </span>
                )}
              </div>
              <div className="text-xs text-[#9ca3af] mt-1">{stat.label}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column (2/3) */}
          <div className="lg:col-span-2 space-y-6">

            {/* Songs Table */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-[#2a2a3a]">
                <h2 className="font-bold text-[#f9fafb]">My Songs</h2>
                <Link
                  href="/songwriters/register"
                  className="text-xs text-[#8b5cf6] hover:text-[#a78bfa] transition-colors"
                >
                  + Register New Song
                </Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-[#9ca3af] border-b border-[#2a2a3a]">
                      <th className="text-left px-5 py-3">Song</th>
                      <th className="text-left px-4 py-3">Registration</th>
                      <th className="text-right px-4 py-3">Streams</th>
                      <th className="text-right px-4 py-3">Quarterly</th>
                      <th className="text-center px-4 py-3">Deal Room</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SONGS.map((song) => (
                      <tr
                        key={song.title}
                        className="border-b border-[#2a2a3a] last:border-0 hover:bg-[#1a1a24] transition-colors"
                      >
                        <td className="px-5 py-4">
                          <div className="font-medium text-[#f9fafb]">{song.title}</div>
                          {song.coWriters.length > 0 && (
                            <div className="text-xs text-[#9ca3af] mt-0.5">
                              w/ {song.coWriters.join(", ")}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-1.5">
                            {[
                              { label: "ASCAP", active: song.ascap },
                              { label: "BMI", active: song.bmi },
                              { label: "MLC", active: song.mlc },
                            ].map((reg) => (
                              <span
                                key={reg.label}
                                className={`text-xs px-1.5 py-0.5 rounded ${
                                  reg.active
                                    ? "bg-[#10b981]/10 text-[#10b981]"
                                    : "bg-[#2a2a3a] text-[#9ca3af]"
                                }`}
                              >
                                {reg.label}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-4 text-right text-[#9ca3af]">{song.streams}</td>
                        <td className="px-4 py-4 text-right font-medium text-[#f9fafb]">
                          {song.earnings}
                        </td>
                        <td className="px-4 py-4 text-center">
                          {song.dealRoom ? (
                            <span className="text-xs bg-[#8b5cf6]/10 text-[#8b5cf6] border border-[#8b5cf6]/20 px-2 py-0.5 rounded-full">
                              Listed
                            </span>
                          ) : (
                            <span className="text-xs text-[#9ca3af]">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Revenue Breakdown */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <h2 className="font-bold text-[#f9fafb] mb-5">Revenue Breakdown</h2>
              <div className="space-y-4">
                {REVENUE_BARS.map((item) => (
                  <div key={item.label}>
                    <div className="flex items-center justify-between text-sm mb-1.5">
                      <span className="text-[#9ca3af]">{item.label}</span>
                      <span className="font-semibold text-[#f9fafb]">{item.pct}%</span>
                    </div>
                    <div className="h-2 bg-[#2a2a3a] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${item.pct}%`,
                          backgroundColor: item.color,
                          boxShadow: `0 0 8px ${item.color}60`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Sync Pipeline */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-[#2a2a3a]">
                <h2 className="font-bold text-[#f9fafb]">Sync Pipeline</h2>
                <p className="text-xs text-[#9ca3af] mt-1">
                  Our Sync Agent pitched your songs to 3 projects this week
                </p>
              </div>
              <div className="divide-y divide-[#2a2a3a]">
                {SYNC_PIPELINE.map((pitch) => (
                  <div
                    key={pitch.song}
                    className="px-5 py-4 flex items-center justify-between gap-4"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[#f9fafb]">{pitch.song}</div>
                      <div className="text-xs text-[#9ca3af] mt-0.5 truncate">{pitch.project}</div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span
                        className="text-xs px-2.5 py-1 rounded-full font-medium"
                        style={{
                          background: `${pitch.color}15`,
                          color: pitch.color,
                          border: `1px solid ${pitch.color}30`,
                        }}
                      >
                        {pitch.status}
                      </span>
                      <span className="text-xs font-semibold text-[#f9fafb]">{pitch.fee}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right column (1/3) */}
          <div className="space-y-5">
            {/* Collection Status */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-[#2a2a3a]">
                <h2 className="font-bold text-[#f9fafb]">Collection Status</h2>
              </div>
              <div className="divide-y divide-[#2a2a3a]">
                {COLLECTION_STATUS.map((item) => (
                  <div key={item.org} className="px-5 py-3 flex items-center justify-between">
                    <span className="text-sm text-[#9ca3af]">{item.org}</span>
                    <span
                      className={`text-xs font-semibold flex items-center gap-1 ${
                        item.status === "registered" ? "text-[#10b981]" : "text-[#f59e0b]"
                      }`}
                    >
                      {item.status === "registered" ? "✅" : "🔄"} {item.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Co-write Listings */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-[#2a2a3a]">
                <h2 className="font-bold text-[#f9fafb] text-sm">Co-write Listings</h2>
                <Link
                  href="/dealroom/create?type=seek_cowriter"
                  className="text-xs text-[#8b5cf6] hover:text-[#a78bfa] transition-colors"
                >
                  + New
                </Link>
              </div>
              <div className="divide-y divide-[#2a2a3a]">
                {COWRITE_LISTINGS.map((listing) => (
                  <div key={listing.title} className="px-5 py-4">
                    <div className="text-sm text-[#f9fafb] mb-2 leading-tight">
                      {listing.title}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-[#9ca3af]">
                      <span>{listing.offers} offers</span>
                      <span>{listing.views} views</span>
                      <span className="text-[#10b981]">{listing.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Publishing Points */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <h2 className="font-bold text-[#f9fafb] mb-4">Publishing Points</h2>
              <div className="space-y-3">
                {[
                  { label: "Points sold", value: "28" },
                  { label: "Point holders", value: "14" },
                  { label: "Next payout", value: "Apr 1, 2026" },
                  { label: "Payout est.", value: "$205" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between text-sm">
                    <span className="text-[#9ca3af]">{item.label}</span>
                    <span className="font-semibold text-[#f9fafb]">{item.value}</span>
                  </div>
                ))}
              </div>
              <Link
                href="/dealroom"
                className="block text-center mt-5 border border-[#2a2a3a] hover:border-[#8b5cf6] text-[#9ca3af] hover:text-[#8b5cf6] font-semibold text-xs py-2.5 rounded-lg transition-colors"
              >
                View in Deal Room
              </Link>
            </div>

            {/* Quick links */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <h2 className="font-bold text-[#f9fafb] text-sm mb-4">Quick Actions</h2>
              <div className="space-y-2">
                {[
                  { label: "Register new song", href: "/songwriters/register" },
                  { label: "Browse co-write opps", href: "/songwriters/cowrite" },
                  { label: "List in Deal Room", href: "/dealroom" },
                  { label: "View sync pitches", href: "/dealroom?type=sync" },
                ].map((link) => (
                  <Link
                    key={link.label}
                    href={link.href}
                    className="flex items-center justify-between text-sm text-[#9ca3af] hover:text-[#f9fafb] py-1.5 transition-colors"
                  >
                    {link.label}
                    <span className="text-[#2a2a3a]">→</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
