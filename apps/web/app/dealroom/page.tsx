"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { SkeletonListItem } from "@/components/Skeleton";
import { fetchDealRoom } from "@/lib/api";
import type { Listing } from "@/lib/api";

const LISTING_TYPES = [
  { key: "all", label: "All" },
  { key: "sell_master_points", label: "Sell Points" },
  { key: "seek_cowriter", label: "Co-write" },
  { key: "seek_producer", label: "Seek Producer" },
  { key: "offer_beat", label: "Beat Offers" },
  { key: "auction", label: "Auction" },
];

const TYPE_BADGE: Record<string, { label: string; color: string }> = {
  sell_master_points: { label: "Master Points", color: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
  sell_publishing_points: { label: "Publishing Points", color: "bg-violet-500/20 text-violet-300 border-violet-500/30" },
  seek_cowriter: { label: "Co-write", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
  seek_producer: { label: "Seek Producer", color: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  offer_beat: { label: "Beat Offer", color: "bg-orange-500/20 text-orange-300 border-orange-500/30" },
};

// Inline mock fallback for when API is offline
const MOCK_LISTINGS: Listing[] = [
  { id: "1", listing_type: "sell_master_points", listing_mode: "fixed", title: "2% Master Points — 'Golden Hour' (4.2M Streams)", creator_type: "artist", creator_name: "Nova Vex", genre: "Afrobeats", asking_price: 8400, accept_points: true, accept_cash: true, monthly_streams: 280000, total_streams: 4200000, estimated_revenue: 6200, verified_listing: true },
  { id: "2", listing_type: "seek_cowriter", listing_mode: "offer", title: "Looking for Alt R&B Songwriter — 50/50 Publishing Split", creator_type: "artist", creator_name: "Lyra Bloom", genre: "Alt R&B", asking_price: null, accept_points: false, accept_cash: true, verified_listing: false },
  { id: "3", listing_type: "offer_beat", listing_mode: "fixed", title: "Dark Trap Type Beat — 140 BPM — Exclusive License", creator_type: "producer", creator_name: "BLKOUT Beats", genre: "Trap", asking_price: 450, accept_points: true, accept_cash: true, verified_listing: false },
  { id: "4", listing_type: "sell_master_points", listing_mode: "auction", title: "5% Master Points — 'Neon Soul' Auction (Closing Soon)", creator_type: "artist", creator_name: "KASE", genre: "Electronic", asking_price: 15000, accept_points: false, accept_cash: true, monthly_streams: 520000, total_streams: 8100000, auction_ends_in_hours: 18, highest_bid: 12400, bid_count: 7, verified_listing: true },
  { id: "5", listing_type: "seek_producer", listing_mode: "offer", title: "Need Drill Producer for EP — 4 tracks, 50/50 points", creator_type: "artist", creator_name: "Mara J", genre: "Drill", accept_points: true, accept_cash: false, verified_listing: false },
  { id: "6", listing_type: "sell_publishing_points", listing_mode: "fixed", title: "3% Publishing — 'Meridian' (Sync-placed in Netflix)", creator_type: "songwriter", creator_name: "Theo March", genre: "Cinematic Pop", asking_price: 4200, accept_points: false, accept_cash: true, monthly_streams: 95000, total_streams: 1200000, verified_listing: true },
];

function fmt(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toString();
}

function ListingCard({ listing }: { listing: Listing }) {
  const badge = TYPE_BADGE[listing.listing_type] ?? { label: listing.listing_type, color: "bg-gray-500/20 text-gray-300 border-gray-500/30" };
  return (
    <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 flex flex-col gap-4 hover:border-[#8b5cf6]/40 transition-colors group">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${badge.color}`}>{badge.label}</span>
          {listing.verified_listing && <span className="text-xs font-semibold px-2 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">✓ Verified</span>}
        </div>
        <span className="text-xs text-[#6b7280] shrink-0 capitalize">{listing.creator_type}</span>
      </div>
      <h3 className="text-[#f9fafb] font-semibold text-sm leading-snug group-hover:text-[#8b5cf6] transition-colors">{listing.title}</h3>
      <p className="text-[#6b7280] text-xs">by {listing.creator_name} · {listing.genre}</p>
      {listing.monthly_streams != null && (
        <div className="flex gap-4 text-xs text-[#9ca3af]">
          <span>{fmt(listing.monthly_streams)}<span className="text-[#6b7280]"> /mo</span></span>
          <span>{fmt(listing.total_streams!)}<span className="text-[#6b7280]"> total</span></span>
          {listing.estimated_revenue && <span className="text-[#10b981]">${fmt(listing.estimated_revenue!)}<span className="text-[#6b7280]">/yr est.</span></span>}
        </div>
      )}
      {listing.listing_mode === "auction" && listing.auction_ends_in_hours != null && (
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg px-3 py-2 flex items-center justify-between text-xs">
          <span className="text-orange-400 font-semibold">AUCTION — {listing.auction_ends_in_hours}h left</span>
          <span className="text-[#9ca3af]">{listing.bid_count} bids</span>
        </div>
      )}
      <div className="mt-auto flex items-center justify-between">
        <div>
          {listing.listing_mode === "auction" && listing.highest_bid != null ? (
            <div><p className="text-[#6b7280] text-xs">Highest bid</p><p className="text-[#f9fafb] font-bold">${fmt(listing.highest_bid!)}</p></div>
          ) : listing.asking_price != null ? (
            <div><p className="text-[#6b7280] text-xs">Asking</p><p className="text-[#f9fafb] font-bold">${fmt(listing.asking_price)}</p></div>
          ) : (
            <p className="text-[#10b981] text-sm font-semibold">Open to Offers</p>
          )}
        </div>
        {listing.accept_points && <span className="text-xs text-[#8b5cf6] bg-[#8b5cf6]/10 px-2 py-0.5 rounded-full border border-[#8b5cf6]/20">♦ Points OK</span>}
      </div>
      <Link href={`/dealroom/${listing.id}`} className="w-full text-center text-sm font-semibold py-2 rounded-lg bg-[#1e1e2e] hover:bg-[#8b5cf6] text-[#9ca3af] hover:text-white border border-[#2a2a3a] hover:border-[#8b5cf6] transition-all duration-200">
        View Deal
      </Link>
    </div>
  );
}

export default function DealRoomPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [activeFilter, setActiveFilter] = useState(searchParams.get("type") || "all");
  const [maxPrice, setMaxPrice] = useState<string>(searchParams.get("max") || "");

  useEffect(() => {
    const params = new URLSearchParams();
    if (search) params.set("q", search);
    if (activeFilter !== "all") params.set("type", activeFilter);
    if (maxPrice) params.set("max", maxPrice);
    const qs = params.toString();
    router.replace(qs ? `/dealroom?${qs}` : "/dealroom", { scroll: false });
  }, [search, activeFilter, maxPrice]);

  const { data: apiListings = [], isLoading } = useQuery({
    queryKey: ["deal-room"],
    queryFn: fetchDealRoom,
  });

  // Use API data if available, otherwise fall back to mock
  const allListings = apiListings.length > 0 ? apiListings : MOCK_LISTINGS;

  const filtered = allListings.filter((l) => {
    if (search && !l.title.toLowerCase().includes(search.toLowerCase()) && !l.creator_name.toLowerCase().includes(search.toLowerCase())) return false;
    if (activeFilter !== "all") {
      if (activeFilter === "auction") return l.listing_mode === "auction";
      if (l.listing_type !== activeFilter) return false;
    }
    if (maxPrice && l.asking_price != null && l.asking_price > Number(maxPrice)) return false;
    return true;
  });

  const STATS = {
    active_listings: allListings.length,
    points_for_sale: allListings.filter(l => l.listing_type.includes("points")).length,
    cowrite_opportunities: allListings.filter(l => l.listing_type === "seek_cowriter").length,
    deals_completed: 2341,
    total_value_traded: 4820000,
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <section className="pt-28 pb-12 px-4 text-center">
        <div className="inline-flex items-center gap-2 bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 px-4 py-1.5 rounded-full text-xs text-[#8b5cf6] font-semibold mb-6">CREATOR MARKETPLACE</div>
        <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4">Deal Room</h1>
        <p className="text-[#9ca3af] text-lg max-w-xl mx-auto">Trade rights. Sell masters. Build together.</p>
        <div className="mt-8">
          <Link href="/dealroom/create" className="inline-flex items-center gap-2 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-6 py-3 rounded-xl transition-colors text-sm shadow-lg shadow-[#8b5cf6]/20">
            + Post a Listing
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-6xl mx-auto px-4 mb-10">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: "Active Listings", value: fmt(STATS.active_listings) },
            { label: "Points for Sale", value: fmt(STATS.points_for_sale) },
            { label: "Co-write Opps", value: fmt(STATS.cowrite_opportunities) },
            { label: "Deals Completed", value: fmt(STATS.deals_completed) },
            { label: "Total Value Traded", value: `$${fmt(STATS.total_value_traded)}` },
          ].map((stat) => (
            <div key={stat.label} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4 text-center">
              <p className="text-xl font-black text-[#8b5cf6]">{stat.value}</p>
              <p className="text-xs text-[#6b7280] mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Search + Filters */}
      <section className="max-w-6xl mx-auto px-4 mb-6 space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7280]" width="16" height="16" fill="none" viewBox="0 0 16 16">
              <path d="M7 13A6 6 0 1 0 7 1a6 6 0 0 0 0 12zM13 13l-2.5-2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search listings or creators…" className="w-full bg-[#13131a] border border-[#2a2a3a] rounded-lg pl-9 pr-4 py-2.5 text-sm text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] transition-all" />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-[#9ca3af] whitespace-nowrap">Max price:</label>
            <input type="number" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} placeholder="No limit" className="w-28 bg-[#13131a] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] placeholder:text-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] transition-all" />
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {LISTING_TYPES.map((t) => (
            <button key={t.key} onClick={() => setActiveFilter(t.key)} className={`text-sm font-semibold px-4 py-2 rounded-lg border transition-all ${activeFilter === t.key ? "bg-[#8b5cf6] border-[#8b5cf6] text-white" : "bg-[#13131a] border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/50 hover:text-white"}`}>
              {t.label}
            </button>
          ))}
        </div>
      </section>

      {/* Listings Grid */}
      <section className="max-w-6xl mx-auto px-4 pb-20">
        {isLoading ? (
          <div className="space-y-3">{[1,2,3,4].map(i => <SkeletonListItem key={i} />)}</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-4xl mb-4">🔍</div>
            <div className="text-[#6b7280] text-lg mb-2">No listings match your filters.</div>
            <button onClick={() => { setSearch(""); setActiveFilter("all"); setMaxPrice(""); }} className="text-sm text-[#8b5cf6] hover:underline">Clear filters</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((listing) => <ListingCard key={listing.id} listing={listing} />)}
          </div>
        )}
        <div className="mt-14 text-center">
          <p className="text-[#6b7280] text-sm mb-4">Ready to trade your rights or find a collaborator?</p>
          <Link href="/dealroom/create" className="inline-flex items-center gap-2 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-8 py-3 rounded-xl transition-colors">Post a Listing</Link>
        </div>
      </section>
    </div>
  );
}
