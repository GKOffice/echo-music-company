"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface Campaign {
  id: string;
  artist_name: string;
  title: string;
  goal_amount: number;
  total_pledged: number;
  pledge_count: number;
  release_date: string | null;
  description: string;
  status: string;
}

export default function StudioFundPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/fan-economy/studio-fund")
      .then((r) => r.json())
      .then((d) => { setCampaigns(d.campaigns || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🎵</span>
            <h1 className="text-3xl font-bold text-white">Melodio Studio Fund</h1>
          </div>
          <p className="text-[#9ca3af] text-lg max-w-2xl">
            Support artists making their best music yet. Pledge now — no charge until Release Day.
            <span className="text-[#8b5cf6] font-semibold"> $500+ supporters get First In access</span> to royalty purchases.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-2 text-sm text-[#9ca3af]">
              <span className="text-[#10b981] font-bold">✓</span> No charge until Release Day
            </div>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-2 text-sm text-[#9ca3af]">
              <span className="text-[#10b981] font-bold">✓</span> Withdraw anytime before release
            </div>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-2 text-sm text-[#9ca3af]">
              <span className="text-[#8b5cf6] font-bold">★</span> $500+ gets First In royalty access
            </div>
          </div>
        </div>

        {/* Artist CTA */}
        <div className="bg-gradient-to-r from-[#1a1a2e] to-[#16213e] border border-[#8b5cf6]/30 rounded-xl p-6 mb-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-white font-bold text-lg">Are you an artist?</h2>
              <p className="text-[#9ca3af] text-sm mt-1">Launch a Studio Fund and show your fans how you'll use their support.</p>
            </div>
            <Link
              href="/studio-fund/create"
              className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-6 py-3 rounded-lg transition-colors whitespace-nowrap"
            >
              Create Campaign →
            </Link>
          </div>
        </div>

        {/* Campaigns */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1,2,3].map(i => (
              <div key={i} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 animate-pulse">
                <div className="h-4 bg-[#2a2a3a] rounded mb-3 w-2/3" />
                <div className="h-3 bg-[#2a2a3a] rounded mb-6 w-full" />
                <div className="h-2 bg-[#2a2a3a] rounded-full w-full" />
              </div>
            ))}
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-20 text-[#9ca3af]">
            <div className="text-5xl mb-4">🎸</div>
            <p className="text-lg font-semibold text-white mb-2">No active campaigns yet</p>
            <p>Be the first artist to launch a Studio Fund.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((c) => {
              const pct = Math.min(100, Math.round((c.total_pledged / c.goal_amount) * 100));
              return (
                <Link key={c.id} href={`/studio-fund/${c.id}`} className="block group">
                  <div className="bg-[#13131a] border border-[#2a2a3a] hover:border-[#8b5cf6]/50 rounded-xl p-6 transition-all duration-200 h-full">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs text-[#8b5cf6] font-semibold uppercase tracking-wide">
                        {c.artist_name}
                      </span>
                      {c.release_date && (
                        <span className="text-xs text-[#9ca3af]">
                          Release: {new Date(c.release_date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                        </span>
                      )}
                    </div>
                    <h3 className="text-white font-bold text-lg mb-2 group-hover:text-[#8b5cf6] transition-colors">
                      {c.title}
                    </h3>
                    <p className="text-[#9ca3af] text-sm mb-5 line-clamp-2">{c.description}</p>

                    {/* Progress bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-[#10b981] font-bold">${c.total_pledged.toLocaleString()} pledged</span>
                        <span className="text-[#9ca3af]">{pct}% of goal</span>
                      </div>
                      <div className="w-full bg-[#1e1e2e] rounded-full h-2">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-[#8b5cf6] to-[#10b981] transition-all"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <div className="text-xs text-[#9ca3af] mt-1">
                        Goal: ${c.goal_amount.toLocaleString()} · {c.pledge_count} supporter{c.pledge_count !== 1 ? "s" : ""}
                      </div>
                    </div>

                    <div className="text-xs text-[#6b7280] mt-3 border-t border-[#2a2a3a] pt-3">
                      No charge until Release Day · Withdraw anytime
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
