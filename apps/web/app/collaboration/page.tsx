"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";

interface CollabOffer {
  id: string;
  artist_name: string;
  title: string;
  role_needed: string;
  deferred_fee: number;
  fan_commitment_snapshot: number;
  protection_floor: number;
  status: string;
  created_at: string;
}

const ROLES = ["All Roles", "Producer", "Songwriter", "Mixing Engineer", "Mastering Engineer", "Session Vocalist", "Guitarist", "Drummer", "Other"];

export default function CollaborationPage() {
  const [offers, setOffers] = useState<CollabOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState("All Roles");

  useEffect(() => {
    const params = roleFilter !== "All Roles" ? `?role=${encodeURIComponent(roleFilter)}` : "";
    fetch(`/api/v1/fan-economy/collaboration/offers${params}`)
      .then((r) => r.json())
      .then((d) => { setOffers(d.offers || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [roleFilter]);

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-10">

        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🎛️</span>
            <h1 className="text-3xl font-bold text-white">Collaboration Marketplace</h1>
          </div>
          <p className="text-[#9ca3af] text-lg max-w-2xl">
            Work with artists now. Get paid on Release Day — first, before anyone else.
            Every offer shows real fan commitment data so you know the money is real.
          </p>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-sm">
              <div className="text-[#8b5cf6] font-bold mb-1">🤝 Work Deferred</div>
              <div className="text-[#9ca3af]">No payment upfront. You do the work, get paid Release Day.</div>
            </div>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-sm">
              <div className="text-[#10b981] font-bold mb-1">💰 Paid First</div>
              <div className="text-[#9ca3af]">Collaborators are paid first on Release Day, before the artist.</div>
            </div>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-lg px-4 py-3 text-sm">
              <div className="text-[#f59e0b] font-bold mb-1">📊 Real Data</div>
              <div className="text-[#9ca3af]">Each offer shows fan commitment totals — see the demand behind the project.</div>
            </div>
          </div>
        </div>

        {/* Artist CTA */}
        <div className="bg-gradient-to-r from-[#1a1a2e] to-[#16213e] border border-[#8b5cf6]/30 rounded-xl p-5 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-white font-bold">Looking for collaborators?</h2>
            <p className="text-[#9ca3af] text-sm mt-1">Post a deferred offer backed by your fan commitment data.</p>
          </div>
          <Link
            href="/collaboration/create"
            className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold px-5 py-2.5 rounded-lg transition-colors text-sm whitespace-nowrap"
          >
            Post an Offer →
          </Link>
        </div>

        {/* Role filter */}
        <div className="flex flex-wrap gap-2 mb-8">
          {ROLES.map((role) => (
            <button
              key={role}
              onClick={() => { setRoleFilter(role); setLoading(true); }}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                roleFilter === role
                  ? "bg-[#8b5cf6] text-white"
                  : "bg-[#13131a] border border-[#2a2a3a] text-[#9ca3af] hover:border-[#8b5cf6]/50"
              }`}
            >
              {role}
            </button>
          ))}
        </div>

        {/* Offers */}
        {loading ? (
          <div className="space-y-4">
            {[1,2,3].map(i => (
              <div key={i} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 animate-pulse h-28" />
            ))}
          </div>
        ) : offers.length === 0 ? (
          <div className="text-center py-20 text-[#9ca3af]">
            <div className="text-5xl mb-4">🎵</div>
            <p className="text-lg font-semibold text-white mb-2">No open offers right now</p>
            <p>Check back soon or post your own offer.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {offers.map((offer) => (
              <Link key={offer.id} href={`/collaboration/${offer.id}`} className="block group">
                <div className="bg-[#13131a] border border-[#2a2a3a] hover:border-[#8b5cf6]/50 rounded-xl p-6 transition-all duration-200">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="bg-[#8b5cf6]/20 text-[#8b5cf6] text-xs font-bold px-2.5 py-1 rounded-full">
                          {offer.role_needed}
                        </span>
                        <span className="text-[#9ca3af] text-xs">{offer.artist_name}</span>
                      </div>
                      <h3 className="text-white font-bold text-lg group-hover:text-[#8b5cf6] transition-colors">
                        {offer.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-6 flex-shrink-0">
                      <div className="text-center">
                        <div className="text-[#10b981] font-bold text-xl">${offer.deferred_fee.toLocaleString()}</div>
                        <div className="text-[#9ca3af] text-xs">paid Release Day</div>
                      </div>
                      <div className="text-center">
                        <div className="text-[#f59e0b] font-bold text-lg">${offer.fan_commitment_snapshot.toLocaleString()}</div>
                        <div className="text-[#9ca3af] text-xs">fan commitments</div>
                      </div>
                      <div className="bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] text-xs font-bold px-3 py-1.5 rounded-lg">
                        Apply →
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-[#2a2a3a] flex items-center gap-4 text-xs text-[#6b7280]">
                    <span>💰 You get paid first on Release Day</span>
                    <span>·</span>
                    <span>Fixed fee — not revenue share</span>
                    <span>·</span>
                    <span>Protection floor: ${offer.protection_floor.toLocaleString()}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
