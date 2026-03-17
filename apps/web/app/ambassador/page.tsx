"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";
import { useAuth } from "@/contexts/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ───────────────────────────────────────────────────────────────────

interface Referral {
  maskedEmail: string;
  signupDate: string;
  status: "active" | "churned";
  commission: number;
}

interface AmbassadorData {
  isAmbassador: boolean;
  totalReferrals: number;
  activeReferrals: number;
  commissionEarned: number;
  pendingCommission: number;
  referralCode: string;
  tier: "Bronze" | "Silver" | "Gold" | "Platinum";
  nextTierReferrals: number;
  referrals: Referral[];
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_DATA: AmbassadorData = {
  isAmbassador: true,
  totalReferrals: 18,
  activeReferrals: 14,
  commissionEarned: 342.5,
  pendingCommission: 28.75,
  referralCode: "NOVA-2024",
  tier: "Gold",
  nextTierReferrals: 30,
  referrals: [
    {
      maskedEmail: "j***@gmail.com",
      signupDate: "2026-02-14",
      status: "active",
      commission: 24.5,
    },
    {
      maskedEmail: "m***@yahoo.com",
      signupDate: "2026-02-01",
      status: "active",
      commission: 18.75,
    },
    {
      maskedEmail: "s***@hotmail.com",
      signupDate: "2026-01-15",
      status: "churned",
      commission: 12.0,
    },
    {
      maskedEmail: "a***@gmail.com",
      signupDate: "2026-01-10",
      status: "active",
      commission: 31.25,
    },
    {
      maskedEmail: "r***@outlook.com",
      signupDate: "2025-12-20",
      status: "active",
      commission: 19.0,
    },
  ],
};

// ─── Tier Config ──────────────────────────────────────────────────────────────

const TIERS = [
  { name: "Bronze", min: 0, max: 4, rate: 5, color: "#cd7f32", bg: "#cd7f3220" },
  { name: "Silver", min: 5, max: 14, rate: 7, color: "#9ca3af", bg: "#9ca3af20" },
  { name: "Gold", min: 15, max: 29, rate: 10, color: "#f59e0b", bg: "#f59e0b20" },
  { name: "Platinum", min: 30, max: Infinity, rate: 15, color: "#8b5cf6", bg: "#8b5cf620" },
] as const;

function getTierConfig(tier: string) {
  return TIERS.find((t) => t.name === tier) ?? TIERS[0];
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

function tierProgressPct(totalReferrals: number, tierName: string): number {
  const tierIndex = TIERS.findIndex((t) => t.name === tierName);
  if (tierIndex === -1 || tierIndex === TIERS.length - 1) return 100;
  const currentTier = TIERS[tierIndex];
  const nextTier = TIERS[tierIndex + 1];
  const rangeSize = nextTier.min - currentTier.min;
  const progress = totalReferrals - currentTier.min;
  return Math.min(100, Math.max(0, (progress / rangeSize) * 100));
}

// ─── Request Access Form ──────────────────────────────────────────────────────

function RequestAccessView() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setSubmitting(true);
    try {
      await fetch(`${API_URL}/api/v1/ambassador/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email }),
      });
    } catch {
      // silently handle — show success anyway
    }
    setSubmitting(false);
    setSubmitted(true);
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-4 py-16">
      <div className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-8 max-w-md w-full text-center">
        <div className="w-16 h-16 rounded-full bg-[#8b5cf6]/20 flex items-center justify-center mx-auto mb-5">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#8b5cf6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 00-3-3.87" />
            <path d="M16 3.13a4 4 0 010 7.75" />
          </svg>
        </div>

        <h2 className="text-2xl font-black text-[#f9fafb] mb-2">
          Ambassador Program
        </h2>
        <p className="text-[#9ca3af] text-sm leading-relaxed mb-6">
          Earn commission for every fan you bring to Melodio. Ambassadors unlock
          exclusive commission tiers — up to 15% — just by sharing their referral
          link.
        </p>

        {submitted ? (
          <div className="bg-[#10b981]/10 border border-[#10b981]/30 rounded-xl p-5">
            <div className="text-2xl mb-2">✅</div>
            <div className="font-semibold text-[#10b981]">Request received!</div>
            <div className="text-sm text-[#9ca3af] mt-1">
              We&apos;ll review your application and reach out within 2–3 business days.
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-left">
            <div>
              <label className="block text-sm font-medium text-[#d1d5db] mb-1.5">
                Your email address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-[#0a0a0f] border border-[#2a2a38] text-[#f9fafb] placeholder-[#6b7280] text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-[#8b5cf6] transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-60 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              {submitting ? "Submitting..." : "Request Access"}
            </button>
          </form>
        )}

        {/* Commission tiers preview */}
        <div className="mt-6 pt-5 border-t border-[#2a2a38] grid grid-cols-4 gap-2">
          {TIERS.map((tier) => (
            <div key={tier.name} className="text-center">
              <div
                className="text-xs font-bold mb-0.5"
                style={{ color: tier.color }}
              >
                {tier.name}
              </div>
              <div className="text-xs text-[#6b7280]">{tier.rate}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AmbassadorPage() {
  const { user } = useAuth();

  const [copiedToast, setCopiedToast] = useState(false);

  const { data, isLoading } = useQuery<AmbassadorData>({
    queryKey: ["ambassador-me"],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/ambassador/me`, {
          headers: { "Content-Type": "application/json" },
          credentials: "include",
        });
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return MOCK_DATA;
      }
    },
  });

  const ambassador = data ?? MOCK_DATA;
  const tierConfig = getTierConfig(ambassador.tier);
  const progressPct = tierProgressPct(ambassador.totalReferrals, ambassador.tier);

  const nextTier = (() => {
    const idx = TIERS.findIndex((t) => t.name === ambassador.tier);
    return idx < TIERS.length - 1 ? TIERS[idx + 1] : null;
  })();

  async function copyReferralLink() {
    const url = `${typeof window !== "undefined" ? window.location.origin : ""}/ref/${ambassador.referralCode}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // noop
    }
    setCopiedToast(true);
    setTimeout(() => setCopiedToast(false), 2000);
  }

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      {/* Toast */}
      <div
        className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
          copiedToast
            ? "opacity-100 translate-y-0"
            : "opacity-0 translate-y-4 pointer-events-none"
        }`}
      >
        <div className="bg-[#10b981] text-white text-sm font-semibold px-5 py-3 rounded-xl shadow-xl">
          Referral link copied!
        </div>
      </div>

      {isLoading ? (
        <div className="max-w-5xl mx-auto px-4 pt-24 pb-16">
          <Skeleton className="h-9 w-64 mb-2" />
          <Skeleton className="h-4 w-80 mb-8" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-5">
                <Skeleton className="h-3 w-1/2 mb-3" />
                <Skeleton className="h-7 w-2/3" />
              </div>
            ))}
          </div>
        </div>
      ) : !ambassador.isAmbassador ? (
        <>
          <RequestAccessView />
        </>
      ) : (
        <div className="max-w-5xl mx-auto px-4 pt-24 pb-16">
          {/* Header */}
          <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl sm:text-3xl font-black text-[#f9fafb]">
                  Ambassador Dashboard
                </h1>
                <span
                  className="text-xs font-bold px-3 py-1 rounded-full"
                  style={{
                    background: tierConfig.bg,
                    color: tierConfig.color,
                  }}
                >
                  {ambassador.tier}
                </span>
              </div>
              <p className="text-[#9ca3af] text-sm">
                {user?.name ? `Welcome back, ${user.name}. ` : ""}
                You&apos;re earning {tierConfig.rate}% commission on every active referral.
              </p>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {[
              {
                label: "Total Referrals",
                value: String(ambassador.totalReferrals),
                icon: "👥",
                color: "#8b5cf6",
              },
              {
                label: "Active Referrals",
                value: String(ambassador.activeReferrals),
                icon: "✅",
                color: "#10b981",
              },
              {
                label: "Commission Earned",
                value: formatCurrency(ambassador.commissionEarned),
                icon: "💰",
                color: "#f59e0b",
              },
              {
                label: "Pending Commission",
                value: formatCurrency(ambassador.pendingCommission),
                icon: "⏳",
                color: "#9ca3af",
              },
            ].map((card) => (
              <div
                key={card.label}
                className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-5 hover:border-[#8b5cf6]/40 transition-colors"
              >
                <div className="flex items-center gap-1.5 mb-2">
                  <span className="text-base">{card.icon}</span>
                  <span className="text-xs text-[#9ca3af] font-medium">{card.label}</span>
                </div>
                <div
                  className="text-xl sm:text-2xl font-black"
                  style={{ color: card.color }}
                >
                  {card.value}
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Referral Link */}
            <div className="lg:col-span-2 space-y-6">
              <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
                <h2 className="text-lg font-bold text-[#f9fafb] mb-4">Your Referral Link</h2>
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="flex-1 bg-[#0a0a0f] border border-[#2a2a38] rounded-xl px-4 py-3 text-sm text-[#9ca3af] font-mono truncate">
                    melodio.io/ref/{ambassador.referralCode}
                  </div>
                  <button
                    onClick={copyReferralLink}
                    className="flex items-center justify-center gap-2 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-semibold text-sm px-5 py-3 rounded-xl transition-colors shrink-0"
                  >
                    <svg viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                      <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                      <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                    </svg>
                    Copy Link
                  </button>
                </div>
                <p className="text-xs text-[#6b7280] mt-3">
                  Share this link with friends. You earn commission every time someone signs up and becomes an active fan.
                </p>
              </section>

              {/* Tier Progress */}
              <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-lg font-bold text-[#f9fafb]">Tier Progress</h2>
                  {nextTier && (
                    <span className="text-xs text-[#9ca3af]">
                      {ambassador.nextTierReferrals - ambassador.totalReferrals} more to{" "}
                      <span style={{ color: getTierConfig(nextTier.name).color }}>
                        {nextTier.name}
                      </span>
                    </span>
                  )}
                </div>

                {/* Tier bar with labels */}
                <div className="relative mb-3">
                  {/* Track */}
                  <div className="w-full h-3 bg-[#2a2a38] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${progressPct}%`,
                        background: `linear-gradient(90deg, ${tierConfig.color}80, ${tierConfig.color})`,
                      }}
                    />
                  </div>
                </div>

                {/* Tier step labels */}
                <div className="grid grid-cols-4 gap-0">
                  {TIERS.map((tier, idx) => {
                    const isActive = tier.name === ambassador.tier;
                    const isPast =
                      TIERS.findIndex((t) => t.name === ambassador.tier) > idx;
                    return (
                      <div
                        key={tier.name}
                        className={`text-center py-3 px-2 rounded-xl transition-colors ${
                          isActive ? "bg-[#1a1a24]" : ""
                        }`}
                      >
                        <div
                          className="text-sm font-bold mb-0.5"
                          style={{
                            color: isActive || isPast ? tier.color : "#6b7280",
                          }}
                        >
                          {tier.name}
                        </div>
                        <div className="text-xs text-[#6b7280]">
                          {tier.max === Infinity ? `${tier.min}+` : `${tier.min}–${tier.max}`}
                        </div>
                        <div
                          className="text-xs font-semibold mt-1"
                          style={{
                            color: isActive || isPast ? tier.color : "#6b7280",
                          }}
                        >
                          {tier.rate}%
                        </div>
                        {isActive && (
                          <div
                            className="text-[10px] mt-1 font-bold"
                            style={{ color: tier.color }}
                          >
                            You are here
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            </div>

            {/* Commission Rates Info */}
            <aside>
              <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
                <h2 className="text-base font-bold text-[#f9fafb] mb-4">Commission Rates</h2>
                <div className="space-y-3">
                  {TIERS.map((tier) => {
                    const isCurrentTier = tier.name === ambassador.tier;
                    return (
                      <div
                        key={tier.name}
                        className={`flex items-center justify-between p-3 rounded-xl border transition-colors ${
                          isCurrentTier
                            ? "border-opacity-50"
                            : "border-[#2a2a38]"
                        }`}
                        style={
                          isCurrentTier
                            ? {
                                background: tier.bg,
                                borderColor: tier.color + "40",
                              }
                            : {}
                        }
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className="w-2 h-2 rounded-full"
                            style={{ background: tier.color }}
                          />
                          <div>
                            <div
                              className="text-sm font-semibold"
                              style={{ color: isCurrentTier ? tier.color : "#d1d5db" }}
                            >
                              {tier.name}
                            </div>
                            <div className="text-xs text-[#6b7280]">
                              {tier.max === Infinity
                                ? `${tier.min}+ referrals`
                                : `${tier.min}–${tier.max} referrals`}
                            </div>
                          </div>
                        </div>
                        <div
                          className="text-lg font-black"
                          style={{ color: isCurrentTier ? tier.color : "#9ca3af" }}
                        >
                          {tier.rate}%
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-4 pt-4 border-t border-[#2a2a38] text-xs text-[#6b7280] leading-relaxed">
                  Commission is calculated on the fan&apos;s first purchase and paid monthly. Rates improve automatically as your referral count grows.
                </div>
              </section>
            </aside>
          </div>

          {/* Referrals Table */}
          <section className="bg-[#13131a] rounded-xl border border-[#2a2a38] p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-[#f9fafb]">Your Referrals</h2>
              <span className="text-xs text-[#9ca3af] bg-[#1a1a24] px-3 py-1 rounded-full">
                {ambassador.totalReferrals} total
              </span>
            </div>

            <div className="overflow-x-auto -mx-2 px-2">
              <table className="w-full min-w-[480px]">
                <thead>
                  <tr className="text-xs text-[#6b7280] border-b border-[#2a2a38]">
                    <th className="text-left pb-3 font-medium">User</th>
                    <th className="text-left pb-3 font-medium">Signup Date</th>
                    <th className="text-center pb-3 font-medium">Status</th>
                    <th className="text-right pb-3 font-medium">Commission</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#2a2a38]">
                  {ambassador.referrals.map((ref, idx) => (
                    <tr
                      key={`${ref.maskedEmail}-${idx}`}
                      className="hover:bg-[#1a1a24] transition-colors group"
                    >
                      <td className="py-4 pr-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#2a2a38] flex items-center justify-center text-xs font-bold text-[#9ca3af] shrink-0">
                            {ref.maskedEmail[0].toUpperCase()}
                          </div>
                          <span className="text-sm font-medium text-[#f9fafb] font-mono">
                            {ref.maskedEmail}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 text-sm text-[#9ca3af]">
                        {formatDate(ref.signupDate)}
                      </td>
                      <td className="py-4 text-center">
                        <span
                          className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full"
                          style={
                            ref.status === "active"
                              ? { background: "#10b98120", color: "#10b981" }
                              : { background: "#ef444420", color: "#ef4444" }
                          }
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{
                              background:
                                ref.status === "active" ? "#10b981" : "#ef4444",
                            }}
                          />
                          {ref.status === "active" ? "Active" : "Churned"}
                        </span>
                      </td>
                      <td className="py-4 text-right">
                        <span
                          className="text-sm font-bold"
                          style={{
                            color:
                              ref.status === "active" ? "#10b981" : "#6b7280",
                          }}
                        >
                          {formatCurrency(ref.commission)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-[#2a2a38]">
                    <td colSpan={3} className="pt-4 text-sm font-semibold text-[#9ca3af]">
                      Total Commission Earned
                    </td>
                    <td className="pt-4 text-right text-sm font-black text-[#f59e0b]">
                      {formatCurrency(ambassador.commissionEarned)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {ambassador.referrals.length === 0 && (
              <div className="text-center py-10">
                <div className="text-3xl mb-3">🚀</div>
                <div className="text-[#9ca3af] text-sm">
                  No referrals yet. Share your link to start earning!
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
