"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { SkeletonCard, Skeleton } from "@/components/Skeleton";
import { fetchPointDrop, fetchPoints, formatNumber, tierBadge, createCheckoutSession } from "@/lib/api";

const ARTIST_COLORS = ["#8b5cf6", "#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#14b8a6"];

export default function PointDropPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id as string;

  const [qty, setQty] = useState(1);
  const [checkingOut, setCheckingOut] = useState(false);

  const { data: drop, isLoading } = useQuery({
    queryKey: ["point-drop", id],
    queryFn: () => fetchPointDrop(id),
  });

  const { data: allArtists = [] } = useQuery({
    queryKey: ["points"],
    queryFn: fetchPoints,
  });

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#0a0a0f]">
        <Navbar />
        <div className="max-w-6xl mx-auto px-4 pt-24 pb-20">
          <Skeleton className="h-6 w-40 mb-8" />
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3 space-y-6">
              <Skeleton className="h-72 rounded-2xl" />
              <div className="grid grid-cols-3 gap-4">{[1,2,3].map(i => <SkeletonCard key={i} />)}</div>
              <SkeletonCard />
            </div>
            <div className="lg:col-span-2"><SkeletonCard /></div>
          </div>
        </div>
      </main>
    );
  }

  if (!drop) return null;

  const artist = drop.artist;
  const colorIndex = allArtists.findIndex((a) => a.id === artist.id);
  const color = ARTIST_COLORS[Math.max(0, colorIndex) % ARTIST_COLORS.length];
  const aiConfidence = drop.aiConfidence;
  const pctSold = Math.round(((drop.pointsTotal - drop.pointsAvailable) / drop.pointsTotal) * 100);

  const estimates = [
    { scenario: "Conservative", perPoint: drop.conservativeEst, color: "#9ca3af", label: "Conservative estimate" },
    { scenario: "Expected", perPoint: drop.expectedEst, color: "#10b981", label: "Expected estimate" },
    { scenario: "Optimistic", perPoint: drop.optimisticEst, color: "#f59e0b", label: "Optimistic estimate" },
  ];

  const similar = allArtists.filter((a) => a.id !== artist.id).slice(0, 3);

  async function handleBuy() {
    setCheckingOut(true);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "";
      const result = await createCheckoutSession(drop!.id, qty);
      if (result.url) {
        window.location.href = result.url;
      } else {
        // No Stripe URL yet — show demo success
        window.location.href = `${origin}/payments/success`;
      }
    } catch {
      setCheckingOut(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 pt-24 pb-20">
        <Link href="/points" className="inline-flex items-center gap-2 text-sm text-[#9ca3af] hover:text-[#f9fafb] transition-colors mb-8">
          <svg width="16" height="16" fill="none" viewBox="0 0 16 16"><path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back to Points Store
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Left — Artist Info */}
          <div className="lg:col-span-3 space-y-6">
            {/* Hero artwork */}
            <div className="rounded-2xl overflow-hidden h-72 relative flex items-end p-8" style={{ background: `linear-gradient(135deg, ${color}40 0%, #0a0a0f 100%)`, border: `1px solid ${color}40` }}>
              <div className="absolute inset-0 flex items-center justify-center text-9xl opacity-15 select-none pointer-events-none">🎵</div>
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{tierBadge(artist.tier)}</span>
                  <span className="text-sm font-bold px-3 py-1 rounded-full" style={{ background: `${color}30`, color }}>{artist.genre}</span>
                </div>
                <h1 className="text-4xl font-black text-[#f9fafb]">{artist.name}</h1>
              </div>
              <div className="absolute top-5 right-5 bg-[#0a0a0f]/80 backdrop-blur text-[#f9fafb] font-bold px-3 py-1.5 rounded-lg border border-[#2a2a3a] text-sm">
                ⚡ {aiConfidence} Melodio Score
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Monthly Listeners", value: formatNumber(artist.monthlyListeners) },
                { label: "Total Streams", value: formatNumber(artist.totalStreams) },
                { label: "Monthly Growth", value: `+${artist.growthPct}%` },
              ].map((s) => (
                <div key={s.label} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-4 text-center">
                  <div className="text-white font-bold text-xl">{s.value}</div>
                  <div className="text-[#9ca3af] text-xs mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            {/* AI Confidence Score */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-[#f9fafb]">AI Confidence Score</h3>
                <span className="text-2xl font-black" style={{ color }}>{aiConfidence}/100</span>
              </div>
              <div className="w-full h-3 bg-[#2a2a3a] rounded-full overflow-hidden mb-3">
                <div className="h-full rounded-full transition-all duration-700" style={{ width: `${aiConfidence}%`, background: `linear-gradient(90deg, ${color}, #10b981)` }} />
              </div>
              <p className="text-sm text-[#9ca3af]">Based on streaming trajectory, social growth, genre momentum, and playlist algorithmic fit.</p>
            </div>

            {/* Points availability */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-[#f9fafb]">Points Remaining</h3>
                <span className="text-[#f9fafb] font-bold">{drop.pointsAvailable} of {drop.pointsTotal}</span>
              </div>
              <div className="w-full h-3 bg-[#2a2a3a] rounded-full overflow-hidden mb-2">
                <div className="h-full rounded-full" style={{ width: `${pctSold}%`, background: color }} />
              </div>
              <div className="flex justify-between text-xs text-[#9ca3af]">
                <span>{pctSold}% sold</span>
                <span>{drop.pointsAvailable} remaining</span>
              </div>
            </div>

            {/* Earnings Estimate */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h3 className="font-bold text-[#f9fafb] mb-4">Earnings Estimate — Per Point / Year</h3>
              <div className="space-y-3">
                {estimates.map((e) => (
                  <div key={e.scenario} className="flex items-center justify-between p-3 bg-[#0a0a0f] rounded-lg border border-[#2a2a3a]">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full" style={{ background: e.color }} />
                      <span className="text-sm font-medium text-[#f9fafb]">{e.scenario}</span>
                      <span className="text-xs text-[#9ca3af]">({e.label})</span>
                    </div>
                    <span className="font-bold" style={{ color: e.color }}>${e.perPoint}/pt</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[#9ca3af] mt-4">
                Estimates are projections based on current streaming data and growth trends. Not financial advice.
              </p>
            </div>

            {/* How it works */}
            <div className="bg-[#13131a] rounded-xl border border-[#2a2a3a] p-6">
              <h3 className="font-bold text-[#f9fafb] mb-5">How It Works</h3>
              <div className="space-y-5">
                {[
                  { step: "1", title: "Buy Points", desc: "Each point represents fractional royalty ownership in the artist's current and future releases on Melodio." },
                  { step: "2", title: "Earn Monthly", desc: "Streaming royalties are calculated monthly and distributed directly to point holders based on ownership percentage." },
                  { step: "3", title: "Hold or Trade", desc: "Points are locked for 12 months from purchase. After that, they're freely tradeable on the Melodio marketplace." },
                ].map((item) => (
                  <div key={item.step} className="flex items-start gap-4">
                    <div className="w-7 h-7 rounded-full bg-[#8b5cf6]/20 text-[#8b5cf6] text-sm font-bold flex items-center justify-center shrink-0">{item.step}</div>
                    <div>
                      <div className="font-semibold text-[#f9fafb] text-sm">{item.title}</div>
                      <div className="text-xs text-[#9ca3af] mt-0.5 leading-relaxed">{item.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right — Buy form */}
          <div className="lg:col-span-2">
            <div className="sticky top-24">
              <div className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-[#f9fafb] text-lg">Buy Points</h3>
                  <span className="text-xs text-[#9ca3af]">{drop.pointsAvailable} left</span>
                </div>
                <div className="text-[#9ca3af] text-sm mb-6">${artist.pricePerPoint} per point</div>

                {/* Quantity slider */}
                <div className="mb-6">
                  <div className="flex justify-between text-sm mb-2">
                    <label className="text-[#9ca3af]">Quantity</label>
                    <span className="font-bold text-[#f9fafb]">{qty}</span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={Math.min(drop.pointsAvailable, 10)}
                    value={qty}
                    onChange={(e) => setQty(Number(e.target.value))}
                    className="w-full accent-[#8b5cf6]"
                  />
                  <div className="flex justify-between text-xs text-[#9ca3af] mt-1">
                    <span>1</span>
                    <span>{Math.min(drop.pointsAvailable, 10)}</span>
                  </div>
                </div>

                {/* Price summary */}
                <div className="bg-[#0a0a0f] rounded-xl border border-[#2a2a3a] p-4 mb-5 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#9ca3af]">{qty} × ${artist.pricePerPoint}</span>
                    <span className="text-[#f9fafb] font-semibold">${qty * artist.pricePerPoint}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#9ca3af]">Est. annual yield</span>
                    <span className="text-[#10b981] font-semibold">${qty * drop.expectedEst}/yr</span>
                  </div>
                  <div className="border-t border-[#2a2a3a] pt-2 flex justify-between font-bold">
                    <span className="text-[#9ca3af]">Total</span>
                    <span className="text-[#f9fafb] text-lg">${qty * artist.pricePerPoint}</span>
                  </div>
                </div>

                <button
                  onClick={handleBuy}
                  disabled={checkingOut}
                  className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-70 disabled:cursor-not-allowed text-white font-bold text-base px-4 py-3.5 rounded-xl transition-colors duration-200 flex items-center justify-center gap-2"
                  style={{ boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
                >
                  {checkingOut ? (
                    <>
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Redirecting to checkout…
                    </>
                  ) : (
                    `Buy ${qty} ${qty === 1 ? "Point" : "Points"} — $${qty * artist.pricePerPoint}`
                  )}
                </button>

                <p className="text-xs text-[#9ca3af] text-center mt-4 leading-relaxed">
                  Secured by Stripe. By purchasing you agree to Melodio&apos;s point holder terms.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Similar Drops */}
        <section className="mt-20">
          <h2 className="text-2xl font-black text-[#f9fafb] mb-6">Similar Drops</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {similar.map((a, i) => (
              <Link key={a.id} href={`/points/${a.id}`} className="bg-[#13131a] rounded-xl border border-[#2a2a3a] hover:border-[#8b5cf6] transition-colors p-5 flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0" style={{ background: `${ARTIST_COLORS[i % ARTIST_COLORS.length]}20` }}>🎵</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-semibold text-[#f9fafb] truncate">{a.name}</span>
                    <span>{tierBadge(a.tier)}</span>
                  </div>
                  <div className="text-xs text-[#9ca3af]">{a.genre} · ${a.pricePerPoint}/pt</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-bold text-[#f9fafb]">⚡ {a.echoScore}</div>
                  <div className="text-xs text-[#10b981]">+{a.growthPct}%</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
