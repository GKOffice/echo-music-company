"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";

interface Campaign {
  id: string;
  artist_name: string;
  title: string;
  goal_amount: number;
  total_pledged: number;
  live_total_pledged: number;
  pledge_count: number;
  release_date: string | null;
  description: string;
  reward_tiers: Array<{ level: number; min_amount: number; title: string; perks: string }>;
  status: string;
}

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [pledgeAmount, setPledgeAmount] = useState("");
  const [pledgeTier, setPledgeTier] = useState(1);
  const [pledging, setPledging] = useState(false);
  const [pledgeMsg, setPledgeMsg] = useState("");
  const [withdrawing, setWithdrawing] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/fan-economy/studio-fund/${id}`)
      .then((r) => r.json())
      .then((d) => { setCampaign(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  async function handlePledge(e: React.FormEvent) {
    e.preventDefault();
    setPledging(true);
    setPledgeMsg("");
    try {
      const res = await fetch(`/api/v1/fan-economy/studio-fund/${id}/pledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: parseFloat(pledgeAmount), tier_level: pledgeTier }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Pledge failed");
      setPledgeMsg(data.message);
      router.refresh();
    } catch (err: unknown) {
      setPledgeMsg(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setPledging(false);
    }
  }

  async function handleWithdraw() {
    setWithdrawing(true);
    try {
      await fetch(`/api/v1/fan-economy/studio-fund/${id}/pledge`, { method: "DELETE" });
      setPledgeMsg("Pledge withdrawn successfully.");
      router.refresh();
    } finally {
      setWithdrawing(false);
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-10">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-[#2a2a3a] rounded w-1/2" />
          <div className="h-4 bg-[#2a2a3a] rounded w-full" />
          <div className="h-40 bg-[#2a2a3a] rounded" />
        </div>
      </div>
    </div>
  );
  if (!campaign) return <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center">Campaign not found</div>;

  const pledged = campaign.live_total_pledged || campaign.total_pledged || 0;
  const pct = Math.min(100, Math.round((pledged / campaign.goal_amount) * 100));
  const tiers = campaign.reward_tiers || [];

  function getTierForAmount(amount: number) {
    const sorted = [...tiers].sort((a, b) => b.min_amount - a.min_amount);
    return sorted.find(t => amount >= t.min_amount) || tiers[0];
  }

  const selectedTierInfo = pledgeAmount ? getTierForAmount(parseFloat(pledgeAmount) || 0) : null;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-10">

        <div className="mb-6">
          <div className="text-[#8b5cf6] font-semibold text-sm mb-1 uppercase tracking-wide">{campaign.artist_name}</div>
          <h1 className="text-3xl font-bold text-white mb-3">{campaign.title}</h1>
          <p className="text-[#9ca3af] text-lg">{campaign.description}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left — stats + pledge */}
          <div className="lg:col-span-1 space-y-6">

            {/* Progress */}
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
              <div className="text-2xl font-bold text-[#10b981] mb-1">${pledged.toLocaleString()}</div>
              <div className="text-[#9ca3af] text-sm mb-3">pledged of ${campaign.goal_amount.toLocaleString()} goal</div>
              <div className="w-full bg-[#1e1e2e] rounded-full h-3 mb-3">
                <div className="h-3 rounded-full bg-gradient-to-r from-[#8b5cf6] to-[#10b981]" style={{ width: `${pct}%` }} />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-white font-bold">{campaign.pledge_count} supporters</span>
                <span className="text-[#9ca3af]">{pct}% funded</span>
              </div>
              {campaign.release_date && (
                <div className="mt-3 pt-3 border-t border-[#2a2a3a] text-sm text-[#9ca3af]">
                  🗓 Release Day: <span className="text-white font-semibold">
                    {new Date(campaign.release_date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
                  </span>
                </div>
              )}
            </div>

            {/* Pledge form */}
            {campaign.status === "active" && (
              <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
                <h3 className="text-white font-bold mb-4">Pledge Your Support</h3>
                <form onSubmit={handlePledge} className="space-y-4">
                  <div>
                    <label className="block text-sm text-[#9ca3af] mb-2">Pledge Amount ($)</label>
                    <input
                      type="number"
                      value={pledgeAmount}
                      onChange={(e) => { setPledgeAmount(e.target.value); if (tiers.length) { const t = getTierForAmount(parseFloat(e.target.value)||0); if(t) setPledgeTier(t.level); } }}
                      placeholder="e.g. 100"
                      min="5"
                      required
                      className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-[#8b5cf6]"
                    />
                  </div>
                  {selectedTierInfo && (
                    <div className="bg-[#8b5cf6]/10 border border-[#8b5cf6]/30 rounded-lg px-3 py-2">
                      <div className="text-[#8b5cf6] font-bold text-sm">{selectedTierInfo.title}</div>
                      <div className="text-[#9ca3af] text-xs mt-0.5">{selectedTierInfo.perks}</div>
                    </div>
                  )}
                  <button
                    type="submit"
                    disabled={pledging}
                    className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-50 text-white font-bold py-3 rounded-lg transition-colors"
                  >
                    {pledging ? "Pledging..." : "Pledge Support →"}
                  </button>
                  <p className="text-xs text-[#6b7280] text-center">No charge until Release Day · Withdraw anytime</p>
                </form>

                <button
                  onClick={handleWithdraw}
                  disabled={withdrawing}
                  className="w-full mt-3 text-[#9ca3af] hover:text-white text-sm py-2 transition-colors"
                >
                  {withdrawing ? "Withdrawing..." : "Withdraw my pledge"}
                </button>

                {pledgeMsg && (
                  <div className="mt-3 bg-[#10b981]/10 border border-[#10b981]/30 rounded-lg px-3 py-2 text-[#10b981] text-sm">
                    {pledgeMsg}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right — reward tiers */}
          <div className="lg:col-span-2">
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
              <h3 className="text-white font-bold text-lg mb-5">Supporter Tiers</h3>
              <div className="space-y-3">
                {tiers.length === 0 ? (
                  <p className="text-[#9ca3af] text-sm">No reward tiers set for this campaign.</p>
                ) : (
                  tiers.sort((a, b) => a.level - b.level).map((tier) => (
                    <div key={tier.level} className="flex gap-4 p-4 bg-[#1e1e2e] rounded-xl border border-[#2a2a3a]">
                      <div className="text-center flex-shrink-0">
                        <div className="bg-[#8b5cf6]/20 text-[#8b5cf6] font-bold text-lg w-12 h-12 rounded-xl flex items-center justify-center">
                          ${tier.min_amount >= 1000 ? `${tier.min_amount/1000}K` : tier.min_amount}
                        </div>
                        <div className="text-xs text-[#6b7280] mt-1">min</div>
                      </div>
                      <div>
                        <div className="text-white font-bold">{tier.title}</div>
                        <div className="text-[#9ca3af] text-sm mt-0.5">{tier.perks}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Legal disclaimer */}
            <div className="mt-4 bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4">
              <p className="text-xs text-[#6b7280] leading-relaxed">
                <strong className="text-[#9ca3af]">Note:</strong> Pledging to a Studio Fund is a non-binding expression of support.
                No charge is made until Release Day. You may withdraw your pledge at any time before Release Day.
                Reward tiers provide access and recognition perks only — no royalty ownership or financial return is implied or guaranteed at this stage.
                Royalty purchase opportunities are separate and available on Release Day.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
