"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "../../../components/Navbar";

// Mock listing data
const MOCK_LISTING = {
  id: "4",
  listing_type: "sell_master_points",
  listing_mode: "auction",
  title: "5% Master Points — 'Neon Soul' (Electronic)",
  creator_type: "artist",
  creator_name: "KASE",
  genre: "Electronic",
  description:
    "Selling 5% of my master recording royalties for 'Neon Soul'. Track has been growing 22% MoM for 6 months and was recently featured on Spotify's Electronic Rising playlist. Verified rights holder. Smart contract escrow included.",
  asking_price: 15000,
  reserve_price: 10000,
  accept_points: false,
  accept_cash: true,
  monthly_streams: 520000,
  total_streams: 8100000,
  estimated_revenue: 12400,
  growth_pct: 22,
  auction_ends_hours: 18,
  auction_ends_minutes: 34,
  highest_bid: 12400,
  bid_count: 7,
  verified_listing: true,
  escrow_required: true,
  rights_info: {
    type: "Master Recording",
    pct: 5,
    track: "Neon Soul",
    isrc: "USXYZ2410042",
    registered: true,
  },
};

const MOCK_BIDS = [
  { id: "b1", bidder: "ProducerX", amount: 12400, time: "2h ago" },
  { id: "b2", bidder: "InvestorA", amount: 11800, time: "5h ago" },
  { id: "b3", bidder: "SoundDAO", amount: 10500, time: "9h ago" },
  { id: "b4", bidder: "MusicFund", amount: 10000, time: "14h ago" },
];

function formatNumber(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toString();
}

function Countdown({ hours, minutes }: { hours: number; minutes: number }) {
  return (
    <div className="flex gap-3 items-center">
      {[
        { val: hours, label: "hrs" },
        { val: minutes, label: "min" },
      ].map(({ val, label }) => (
        <div key={label} className="bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-4 py-2 text-center min-w-[60px]">
          <p className="text-2xl font-black text-[#f9fafb]">{String(val).padStart(2, "0")}</p>
          <p className="text-xs text-[#6b7280]">{label}</p>
        </div>
      ))}
    </div>
  );
}

export default function ListingDetailPage({ params }: { params: { id: string } }) {
  const listing = MOCK_LISTING;
  const [offerType, setOfferType] = useState<"cash" | "points" | "hybrid">("cash");
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState("");
  const [bidAmount, setBidAmount] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const isAuction = listing.listing_mode === "auction";
  const minBid = listing.highest_bid ? listing.highest_bid + 100 : listing.reserve_price;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitted(true);
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />

      <div className="max-w-5xl mx-auto px-4 pt-24 pb-20">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-[#6b7280] mb-6">
          <Link href="/dealroom" className="hover:text-[#9ca3af]">Deal Room</Link>
          <span>/</span>
          <span className="text-[#9ca3af]">Listing #{params.id}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Main Info */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Header */}
            <div>
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full border bg-purple-500/20 text-purple-300 border-purple-500/30">
                  Master Points
                </span>
                {listing.verified_listing && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full border bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                    ✓ Verified
                  </span>
                )}
                {listing.escrow_required && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full border bg-blue-500/10 text-blue-400 border-blue-500/30">
                    🔒 Escrow
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-black mb-2">{listing.title}</h1>
              <p className="text-[#9ca3af] text-sm">
                by <span className="text-[#f9fafb]">{listing.creator_name}</span> ·{" "}
                <span className="capitalize">{listing.creator_type}</span> · {listing.genre}
              </p>
            </div>

            {/* Streaming Stats */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-[#9ca3af] uppercase tracking-wide mb-4">
                Track Performance
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Monthly Streams", value: formatNumber(listing.monthly_streams) },
                  { label: "Total Streams", value: formatNumber(listing.total_streams) },
                  { label: "Est. Annual Rev.", value: `$${formatNumber(listing.estimated_revenue)}` },
                  { label: "MoM Growth", value: `+${listing.growth_pct}%`, green: true },
                ].map((s) => (
                  <div key={s.label}>
                    <p className="text-xs text-[#6b7280] mb-1">{s.label}</p>
                    <p className={`text-lg font-bold ${s.green ? "text-[#10b981]" : "text-[#f9fafb]"}`}>
                      {s.value}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Auction Panel */}
            {isAuction && (
              <div className="bg-orange-500/5 border border-orange-500/20 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-orange-400 uppercase tracking-wide">
                    Live Auction
                  </h3>
                  <Countdown hours={listing.auction_ends_hours} minutes={listing.auction_ends_minutes} />
                </div>
                <div className="flex items-baseline gap-3 mb-4">
                  <div>
                    <p className="text-xs text-[#6b7280]">Current highest bid</p>
                    <p className="text-3xl font-black text-[#f9fafb]">${formatNumber(listing.highest_bid)}</p>
                  </div>
                  <span className="text-[#6b7280] text-sm">{listing.bid_count} bids</span>
                </div>
                {/* Bid history */}
                <div className="space-y-2">
                  {MOCK_BIDS.map((bid) => (
                    <div key={bid.id} className="flex items-center justify-between text-sm py-1.5 border-b border-[#2a2a3a] last:border-0">
                      <span className="text-[#9ca3af]">{bid.bidder}</span>
                      <div className="flex gap-4">
                        <span className="text-[#f9fafb] font-semibold">${formatNumber(bid.amount)}</span>
                        <span className="text-[#6b7280]">{bid.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Description */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-[#9ca3af] uppercase tracking-wide mb-3">About this Listing</h3>
              <p className="text-[#9ca3af] text-sm leading-relaxed">{listing.description}</p>
            </div>

            {/* Rights Info */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-[#9ca3af] uppercase tracking-wide mb-4">Rights Details</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-[#6b7280]">Rights Type</span><p className="text-[#f9fafb] font-semibold mt-1">{listing.rights_info.type}</p></div>
                <div><span className="text-[#6b7280]">Percentage</span><p className="text-[#f9fafb] font-semibold mt-1">{listing.rights_info.pct}%</p></div>
                <div><span className="text-[#6b7280]">Track</span><p className="text-[#f9fafb] font-semibold mt-1">{listing.rights_info.track}</p></div>
                <div><span className="text-[#6b7280]">ISRC</span><p className="text-[#f9fafb] font-mono text-xs mt-1">{listing.rights_info.isrc}</p></div>
              </div>
              <div className="mt-3 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${listing.rights_info.registered ? "bg-emerald-400" : "bg-gray-400"}`} />
                <span className="text-xs text-[#9ca3af]">
                  {listing.rights_info.registered ? "Rights ownership verified by Melodio" : "Pending verification"}
                </span>
              </div>
            </div>

            {/* Education Box */}
            <div className="bg-[#8b5cf6]/5 border border-[#8b5cf6]/20 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-[#8b5cf6] mb-2">Why own music rights?</h3>
              <ul className="text-xs text-[#9ca3af] space-y-1.5">
                <li>• Earn a share of streaming, sync, and performance royalties forever</li>
                <li>• Points are liquid — resell on the Deal Room at any time</li>
                <li>• Quarterly payouts directly to your wallet via the Points Vault</li>
                <li>• Contracts are legally binding and generated automatically on acceptance</li>
              </ul>
            </div>
          </div>

          {/* Right: Offer / Bid Panel */}
          <div className="flex flex-col gap-5">
            {/* Price box */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <p className="text-xs text-[#6b7280] mb-1">
                {isAuction ? "Reserve price" : "Asking price"}
              </p>
              <p className="text-3xl font-black text-[#f9fafb] mb-1">
                ${formatNumber(isAuction ? listing.reserve_price : listing.asking_price)}
              </p>
              <div className="flex gap-2 mt-2">
                {listing.accept_cash && (
                  <span className="text-xs bg-[#1e1e2e] border border-[#2a2a3a] px-2 py-0.5 rounded text-[#9ca3af]">
                    💵 Cash
                  </span>
                )}
                {listing.accept_points && (
                  <span className="text-xs bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 px-2 py-0.5 rounded text-[#8b5cf6]">
                    ♦ Points
                  </span>
                )}
              </div>
            </div>

            {/* Offer / Bid Form */}
            {!submitted ? (
              <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
                <h3 className="text-sm font-semibold mb-4">
                  {isAuction ? "Place a Bid" : "Make an Offer"}
                </h3>

                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                  {!isAuction && (
                    <>
                      {/* Offer type toggle */}
                      <div>
                        <p className="text-xs text-[#6b7280] mb-2">Offer type</p>
                        <div className="flex gap-2">
                          {(["cash", "points", "hybrid"] as const).map((t) => (
                            <button
                              key={t}
                              type="button"
                              onClick={() => setOfferType(t)}
                              className={`flex-1 text-xs font-semibold py-1.5 rounded-lg border transition-all capitalize ${
                                offerType === t
                                  ? "bg-[#8b5cf6] border-[#8b5cf6] text-white"
                                  : "bg-[#1e1e2e] border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/40"
                              }`}
                            >
                              {t}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Amount input */}
                      {(offerType === "cash" || offerType === "hybrid") && (
                        <div>
                          <label className="text-xs text-[#6b7280] block mb-1">
                            {offerType === "hybrid" ? "Cash amount ($)" : "Amount ($)"}
                          </label>
                          <input
                            type="number"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            placeholder="e.g. 10000"
                            className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563]"
                          />
                        </div>
                      )}

                      {(offerType === "points" || offerType === "hybrid") && (
                        <div>
                          <label className="text-xs text-[#6b7280] block mb-1">Points quantity</label>
                          <input
                            type="number"
                            placeholder="e.g. 2"
                            className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563]"
                          />
                        </div>
                      )}
                    </>
                  )}

                  {isAuction && (
                    <div>
                      <label className="text-xs text-[#6b7280] block mb-1">
                        Your bid (min ${formatNumber(minBid)})
                      </label>
                      <input
                        type="number"
                        value={bidAmount}
                        onChange={(e) => setBidAmount(e.target.value)}
                        placeholder={`e.g. ${minBid}`}
                        className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563]"
                      />
                    </div>
                  )}

                  {!isAuction && (
                    <div>
                      <label className="text-xs text-[#6b7280] block mb-1">Message to seller</label>
                      <textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        rows={3}
                        placeholder="Introduce yourself and explain your offer..."
                        className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-sm text-[#f9fafb] focus:outline-none focus:border-[#8b5cf6] placeholder:text-[#4b5563] resize-none"
                      />
                    </div>
                  )}

                  <button
                    type="submit"
                    className="w-full bg-[#10b981] hover:bg-[#059669] text-white font-bold py-3 rounded-xl transition-colors text-sm"
                  >
                    {isAuction ? "Place Bid" : "Submit Offer"}
                  </button>
                </form>
              </div>
            ) : (
              <div className="bg-[#10b981]/10 border border-[#10b981]/20 rounded-xl p-5 text-center">
                <p className="text-2xl mb-2">✓</p>
                <p className="text-[#10b981] font-semibold text-sm">
                  {isAuction ? "Bid placed!" : "Offer submitted!"}
                </p>
                <p className="text-[#9ca3af] text-xs mt-1">The seller will be notified.</p>
              </div>
            )}

            <Link
              href="/dealroom"
              className="text-center text-xs text-[#6b7280] hover:text-[#9ca3af] transition-colors py-2"
            >
              ← Back to marketplace
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
