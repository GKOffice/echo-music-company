"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
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
  agreement_id?: string;
  collaborator_id?: string;
  payment_status?: string;
}

export default function CollabOfferDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [offer, setOffer] = useState<CollabOffer | null>(null);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    fetch(`/api/v1/fan-economy/collaboration/offer/${id}`)
      .then((r) => r.json())
      .then((d) => { setOffer(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  async function handleAccept() {
    if (!confirm("Accept this offer? You agree to complete the work and receive payment on Release Day.")) return;
    setAccepting(true);
    try {
      const res = await fetch(`/api/v1/fan-economy/collaboration/offer/${id}/accept`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to accept");
      setMsg(data.message);
      setOffer(prev => prev ? { ...prev, status: "filled" } : prev);
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setAccepting(false);
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0f]"><Navbar />
      <div className="max-w-3xl mx-auto px-4 py-10 animate-pulse space-y-4">
        <div className="h-8 bg-[#2a2a3a] rounded w-2/3" />
        <div className="h-40 bg-[#2a2a3a] rounded" />
      </div>
    </div>
  );
  if (!offer) return <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center">Offer not found</div>;

  const isFilled = offer.status === "filled";

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-10">

        <div className="mb-6">
          <div className="flex items-center gap-3 mb-3">
            <span className="bg-[#8b5cf6]/20 text-[#8b5cf6] text-sm font-bold px-3 py-1 rounded-full">{offer.role_needed}</span>
            <span className="text-[#9ca3af] text-sm">{offer.artist_name}</span>
            {isFilled && <span className="bg-[#10b981]/20 text-[#10b981] text-xs font-bold px-2 py-0.5 rounded-full">Filled</span>}
          </div>
          <h1 className="text-3xl font-bold text-white">{offer.title}</h1>
        </div>

        {/* Key numbers */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 text-center">
            <div className="text-2xl font-bold text-[#10b981]">${offer.deferred_fee.toLocaleString()}</div>
            <div className="text-[#9ca3af] text-sm mt-1">Your fee — paid Release Day</div>
          </div>
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 text-center">
            <div className="text-2xl font-bold text-[#f59e0b]">${offer.fan_commitment_snapshot.toLocaleString()}</div>
            <div className="text-[#9ca3af] text-sm mt-1">Fan commitment total</div>
          </div>
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5 text-center col-span-2 sm:col-span-1">
            <div className="text-2xl font-bold text-[#8b5cf6]">${offer.protection_floor.toLocaleString()}</div>
            <div className="text-[#9ca3af] text-sm mt-1">Protection floor (40%)</div>
          </div>
        </div>

        {/* How it works */}
        <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 mb-6">
          <h3 className="text-white font-bold mb-4">How Deferred Collaboration Works</h3>
          <div className="space-y-3">
            {[
              { icon: "1️⃣", text: "You accept this offer and sign a Deferred Collaboration Agreement with the artist." },
              { icon: "2️⃣", text: "You complete the work (production, mixing, writing, etc.) for this project." },
              { icon: "3️⃣", text: "On Release Day, when the music goes live, Melodio settles all accounts." },
              { icon: "4️⃣", text: `Your fee of $${offer.deferred_fee.toLocaleString()} is released FIRST — before Melodio's fee and before the artist receives their balance.` },
            ].map(({ icon, text }) => (
              <div key={icon} className="flex gap-3">
                <span className="text-lg flex-shrink-0">{icon}</span>
                <span className="text-[#9ca3af] text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Payment waterfall */}
        <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 mb-6">
          <h3 className="text-white font-bold mb-4">Release Day Payment Order</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-3 p-3 bg-[#10b981]/10 border border-[#10b981]/30 rounded-lg">
              <span className="text-[#10b981] font-bold text-sm">1st</span>
              <span className="text-white text-sm font-semibold">Collaborators paid in full</span>
              <span className="text-[#10b981] text-xs ml-auto">← You</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-[#1e1e2e] rounded-lg">
              <span className="text-[#9ca3af] font-bold text-sm">2nd</span>
              <span className="text-[#9ca3af] text-sm">Melodio platform fee (5%)</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-[#1e1e2e] rounded-lg">
              <span className="text-[#9ca3af] font-bold text-sm">3rd</span>
              <span className="text-[#9ca3af] text-sm">Artist receives remaining balance</span>
            </div>
          </div>
        </div>

        {/* Accept / status */}
        {!isFilled ? (
          <div className="space-y-4">
            <div className="bg-[#1a1a2e] border border-[#8b5cf6]/30 rounded-xl p-4">
              <p className="text-[#9ca3af] text-sm">
                By accepting this offer, you agree to complete the work described and receive your deferred fee of
                <span className="text-white font-bold"> ${offer.deferred_fee.toLocaleString()}</span> on Release Day.
                A formal Deferred Collaboration Agreement will be provided by the artist before work begins.
              </p>
            </div>
            <button
              onClick={handleAccept}
              disabled={accepting}
              className="w-full bg-[#10b981] hover:bg-[#059669] disabled:opacity-50 text-white font-bold py-4 rounded-xl transition-colors text-lg"
            >
              {accepting ? "Accepting..." : `Accept — ${offer.role_needed} for $${offer.deferred_fee.toLocaleString()} →`}
            </button>
          </div>
        ) : (
          <div className="bg-[#10b981]/10 border border-[#10b981]/30 rounded-xl p-6 text-center">
            <div className="text-3xl mb-2">✅</div>
            <p className="text-[#10b981] font-bold">This offer has been filled</p>
            <p className="text-[#9ca3af] text-sm mt-1">A collaborator has already accepted this position.</p>
          </div>
        )}

        {msg && (
          <div className="mt-4 bg-[#8b5cf6]/10 border border-[#8b5cf6]/30 rounded-lg px-4 py-3 text-[#8b5cf6] text-sm">
            {msg}
          </div>
        )}
      </div>
    </div>
  );
}
