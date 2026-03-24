"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";

interface RewardTier {
  level: number;
  min_amount: number;
  title: string;
  perks: string;
}

const DEFAULT_TIERS: RewardTier[] = [
  { level: 1, min_amount: 5,   title: "Supporter",  perks: "Name in album thank-you credits" },
  { level: 2, min_amount: 20,  title: "Backer",     perks: "Credits + exclusive behind-the-scenes updates" },
  { level: 3, min_amount: 50,  title: "Champion",   perks: "Above + early listening access (48hrs before release)" },
  { level: 4, min_amount: 100, title: "Producer",   perks: "Above + digital stems pack from one song" },
  { level: 5, min_amount: 250, title: "Executive",  perks: "Above + signed digital poster + video message" },
  { level: 6, min_amount: 500, title: "First In ⭐", perks: "Above + guaranteed First In royalty access on Release Day" },
];

export default function CreateCampaignPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [goalAmount, setGoalAmount] = useState("");
  const [description, setDescription] = useState("");
  const [releaseDate, setReleaseDate] = useState("");
  const [tiers, setTiers] = useState<RewardTier[]>(DEFAULT_TIERS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/v1/fan-economy/studio-fund", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          goal_amount: parseFloat(goalAmount),
          description,
          reward_tiers: tiers,
          release_date: releaseDate || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to create campaign");
      router.push(`/studio-fund/${data.campaign_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#f9fafb]">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Launch Your Studio Fund</h1>
          <p className="text-[#9ca3af]">
            Show fans exactly what you're building and how you'll use their support.
            Pledges are collected on Release Day only — fans can withdraw anytime before.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6 space-y-5">
            <h2 className="text-white font-bold text-lg">Campaign Details</h2>

            <div>
              <label className="block text-sm font-medium text-[#9ca3af] mb-2">Campaign Title *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Recording my debut album at Electric Lady Studios"
                required
                className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-[#8b5cf6] transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#9ca3af] mb-2">Funding Goal ($) *</label>
              <input
                type="number"
                value={goalAmount}
                onChange={(e) => setGoalAmount(e.target.value)}
                placeholder="e.g. 40000"
                min="100"
                required
                className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-[#8b5cf6] transition-colors"
              />
              <p className="text-xs text-[#6b7280] mt-1">This is your goal — not a hard requirement. All pledges collected on Release Day.</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#9ca3af] mb-2">What will you use it for? *</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Be specific. e.g. $15K studio time, $20K producer fee, $5K mixing + mastering. Tell your fans exactly how their support makes the music better."
                required
                rows={4}
                className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-[#8b5cf6] transition-colors resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#9ca3af] mb-2">Expected Release Date</label>
              <input
                type="date"
                value={releaseDate}
                onChange={(e) => setReleaseDate(e.target.value)}
                className="bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-4 py-3 text-white focus:outline-none focus:border-[#8b5cf6] transition-colors"
              />
            </div>
          </div>

          {/* Reward Tiers */}
          <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-6">
            <h2 className="text-white font-bold text-lg mb-4">Supporter Tiers</h2>
            <p className="text-[#9ca3af] text-sm mb-5">Digital perks only. Customize what each level receives.</p>
            <div className="space-y-3">
              {tiers.map((tier, i) => (
                <div key={tier.level} className="flex gap-3 items-start">
                  <div className="bg-[#8b5cf6]/20 text-[#8b5cf6] font-bold text-sm w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                    {tier.level}
                  </div>
                  <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <div>
                      <input
                        type="number"
                        value={tier.min_amount}
                        onChange={(e) => {
                          const updated = [...tiers];
                          updated[i] = { ...updated[i], min_amount: parseFloat(e.target.value) };
                          setTiers(updated);
                        }}
                        placeholder="Min $"
                        className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-[#8b5cf6]"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        value={tier.title}
                        onChange={(e) => {
                          const updated = [...tiers];
                          updated[i] = { ...updated[i], title: e.target.value };
                          setTiers(updated);
                        }}
                        placeholder="Tier name"
                        className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-[#8b5cf6]"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        value={tier.perks}
                        onChange={(e) => {
                          const updated = [...tiers];
                          updated[i] = { ...updated[i], perks: e.target.value };
                          setTiers(updated);
                        }}
                        placeholder="What they get"
                        className="w-full bg-[#1e1e2e] border border-[#2a2a3a] rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-[#8b5cf6]"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-[#6b7280] mt-4">Note: No royalty promises in tier descriptions. Use: early access, credits, stems, video messages.</p>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-50 text-white font-bold py-4 rounded-xl transition-colors text-lg"
          >
            {loading ? "Launching..." : "Launch Studio Fund →"}
          </button>

          <p className="text-xs text-center text-[#6b7280]">
            Launching creates your campaign page. Pledges are non-binding — fans pay on Release Day only.
          </p>
        </form>
      </div>
    </div>
  );
}
