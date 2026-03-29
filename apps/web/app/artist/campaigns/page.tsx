"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

const CAMPAIGNS = [
  {
    id: "point-drop-boost",
    icon: "🚀",
    name: "Point Drop Boost",
    tagline: "Pin your drop to the top of the Points Store",
    color: "#8b5cf6",
    prices: [
      { label: "3 Days", price: 50 },
      { label: "7 Days", price: 100 },
      { label: "14 Days", price: 180 },
    ],
    features: [
      "Pinned to top of /points store",
      "\"Featured Drop\" slot in fan dashboards",
      "Highlighted border + BOOSTED badge",
      "Priority in genre filter results",
    ],
  },
  {
    id: "fan-network-push",
    icon: "📡",
    name: "Fan Network Push",
    tagline: "Reach fans outside your existing network",
    color: "#10b981",
    prices: [
      { label: "Starter (500 fans)", price: 100 },
      { label: "Growth (2K fans)", price: 250 },
      { label: "Scale (10K fans)", price: 500 },
    ],
    features: [
      "Targeted by genre affinity",
      "Shown to fans of similar artists",
      "Email + dashboard notification",
      "Real reach analytics included",
    ],
  },
  {
    id: "release-day-campaign",
    icon: "⚡",
    name: "Release Day Campaign",
    tagline: "Full platform moment on your Release Day",
    color: "#f59e0b",
    prices: [
      { label: "Standard", price: 250 },
      { label: "Premium", price: 500 },
      { label: "Elite", price: 1000 },
    ],
    features: [
      "Homepage banner on Release Day",
      "Live ticker events across platform",
      "Email blast to genre-matched fans",
      "Coordinated with Release Day Settlement",
    ],
  },
];

export default function ArtistCampaignsPage() {
  const [selected, setSelected] = useState<Record<string, number>>({});
  const [launched, setLaunched] = useState<string | null>(null);

  function selectPrice(campaignId: string, idx: number) {
    setSelected(prev => ({ ...prev, [campaignId]: idx }));
  }

  function launch(campaignId: string) {
    setLaunched(campaignId);
    setTimeout(() => setLaunched(null), 3000);
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">📢</span>
            <h1 className="text-3xl font-bold text-white">Melodio Ad Campaigns</h1>
          </div>
          <p className="text-[#9ca3af] text-lg max-w-2xl">
            Grow your fanbase and sell more points inside Melodio. Every campaign targets fans by genre affinity — real reach, zero waste.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-2 text-sm text-[#9ca3af]">
              <span className="text-[#10b981] font-bold">✓</span> Only pays for real reach
            </div>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-2 text-sm text-[#9ca3af]">
              <span className="text-[#10b981] font-bold">✓</span> Genre-matched audiences
            </div>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-2 text-sm text-[#9ca3af]">
              <span className="text-[#8b5cf6] font-bold">★</span> Higher tier = more organic reach included free
            </div>
          </div>
        </div>

        {/* Artist Tier Unlock Note */}
        <div className="bg-gradient-to-r from-[#1a1a2e] to-[#16213e] border border-[#8b5cf6]/30 rounded-xl p-6 mb-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-white font-bold text-lg">👑 Melodio Elite artists get free Fan Network Pushes</h2>
              <p className="text-[#9ca3af] text-sm mt-1">Reach 25 releases and we promote you to our entire fan network — no ad spend required.</p>
            </div>
            <Link href="/dashboard" className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-6 py-3 rounded-lg transition-colors whitespace-nowrap">
              View My Progress →
            </Link>
          </div>
        </div>

        {/* Campaign Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {CAMPAIGNS.map((campaign) => {
            const selectedIdx = selected[campaign.id] ?? 0;
            const selectedPrice = campaign.prices[selectedIdx];
            const isLaunched = launched === campaign.id;

            return (
              <div
                key={campaign.id}
                className="bg-[#13131a] border border-[#2a2a3a] hover:border-[#8b5cf6]/50 rounded-xl p-6 flex flex-col transition-all"
              >
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">{campaign.icon}</span>
                  <div>
                    <h3 className="text-white font-bold text-lg">{campaign.name}</h3>
                    <p className="text-[#9ca3af] text-xs">{campaign.tagline}</p>
                  </div>
                </div>

                {/* Features */}
                <ul className="space-y-2 mb-6 flex-1">
                  {campaign.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#9ca3af]">
                      <span style={{ color: campaign.color }} className="mt-0.5 font-bold shrink-0">✓</span>
                      {f}
                    </li>
                  ))}
                </ul>

                {/* Price selector */}
                <div className="flex gap-2 mb-4">
                  {campaign.prices.map((p, i) => (
                    <button
                      key={i}
                      onClick={() => selectPrice(campaign.id, i)}
                      className="flex-1 text-center rounded-lg py-2 text-xs font-bold transition-all border"
                      style={selectedIdx === i ? {
                        background: `${campaign.color}30`,
                        color: campaign.color,
                        borderColor: campaign.color,
                      } : {
                        background: "transparent",
                        color: "#6b7280",
                        borderColor: "#2a2a3a",
                      }}
                    >
                      <div>{p.label}</div>
                      <div className="text-base mt-0.5">${p.price}</div>
                    </button>
                  ))}
                </div>

                {/* Launch button */}
                <button
                  onClick={() => launch(campaign.id)}
                  className="w-full font-bold py-3 rounded-xl transition-all text-white text-sm"
                  style={{
                    background: isLaunched ? "#10b981" : campaign.color,
                    boxShadow: `0 0 20px ${campaign.color}40`,
                  }}
                >
                  {isLaunched ? "✓ Campaign Queued!" : `Launch for $${selectedPrice.price}`}
                </button>
              </div>
            );
          })}
        </div>

        {/* How billing works */}
        <div className="mt-10 bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
          <h2 className="text-white font-bold mb-4">How billing works</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-[#9ca3af]">
            <div><span className="text-[#8b5cf6] font-bold">01.</span> Choose your campaign type and budget</div>
            <div><span className="text-[#8b5cf6] font-bold">02.</span> Charge goes to your Melodio artist account via Stripe</div>
            <div><span className="text-[#8b5cf6] font-bold">03.</span> Campaign runs automatically — analytics in your dashboard</div>
          </div>
        </div>
      </div>
    </div>
  );
}
