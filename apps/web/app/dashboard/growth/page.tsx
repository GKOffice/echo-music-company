"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { API_URL } from "@/lib/config";

interface Strength {
  area: string;
  score: number;
  detail: string;
}

interface Gap {
  area: string;
  score: number;
  detail: string;
  fixable: boolean;
}

interface ActionItem {
  action: string;
  agent: string;
  what_we_do: string;
  your_result: string;
  auto: boolean;
}

interface ActionStep {
  step: number;
  action: string;
  why: string;
  time: string;
}

interface GrowthReport {
  artist_name: string;
  overall_score: number;
  tier: string;
  strengths: Strength[];
  gaps: Gap[];
  melodio_action_plan: {
    immediate: ActionItem[];
    week_1_to_4: ActionItem[];
    month_2_to_6: ActionItem[];
    artist_action_steps: ActionStep[];
  };
  melodio_advantage: {
    agents_working_for_you: number;
    estimated_monthly_value: string;
    what_you_pay: string;
    revenue_split: string;
    masters: string;
    contract: string;
  };
}

function tierColor(tier: string) {
  switch (tier) {
    case "Established": return { bg: "bg-[#8b5cf6]/20", border: "border-[#8b5cf6]", text: "text-[#a78bfa]" };
    case "Breaking": return { bg: "bg-[#3b82f6]/20", border: "border-[#3b82f6]", text: "text-[#60a5fa]" };
    case "Rising": return { bg: "bg-[#10b981]/20", border: "border-[#10b981]", text: "text-[#34d399]" };
    default: return { bg: "bg-[#f59e0b]/20", border: "border-[#f59e0b]", text: "text-[#fbbf24]" };
  }
}

function scoreColor(score: number) {
  if (score >= 75) return "#10b981";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
}

function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const color = scoreColor(score);

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#2a2a3a" strokeWidth="8" />
      <circle
        cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke={color} strokeWidth="8" strokeLinecap="round"
        strokeDasharray={circumference} strokeDashoffset={circumference - progress}
        className="transition-all duration-1000 ease-out"
      />
    </svg>
  );
}

function SkeletonReport() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="flex items-center gap-6">
        <div className="w-[120px] h-[120px] rounded-full bg-[#2a2a3a]" />
        <div className="space-y-3 flex-1">
          <div className="h-8 bg-[#2a2a3a] rounded w-48" />
          <div className="h-5 bg-[#2a2a3a] rounded w-32" />
        </div>
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-32 bg-[#13131a] rounded-xl border border-[#2a2a3a]" />
      ))}
    </div>
  );
}

export default function GrowthReportPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [report, setReport] = useState<GrowthReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login");
      return;
    }
    if (user) fetchReport();
  }, [user, authLoading]);

  async function fetchReport() {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("melodio_token");
      const res = await fetch(`${API_URL}/api/v1/growth/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to generate report");
      const data = await res.json();
      setReport(data);
    } catch (e: any) {
      setError(e.message || "Could not generate your growth report");
    } finally {
      setLoading(false);
    }
  }

  function toggleStep(step: number) {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(step)) next.delete(step);
      else next.add(step);
      return next;
    });
  }

  if (authLoading) return null;

  const tc = report ? tierColor(report.tier) : tierColor("Emerging");

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 pt-24 pb-16">
        {loading && <SkeletonReport />}

        {error && (
          <div className="bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#fca5a5] rounded-xl px-6 py-4 mt-8">
            <p className="font-medium">Could not generate report</p>
            <p className="text-sm mt-1 opacity-80">{error}</p>
            <button onClick={fetchReport} className="mt-3 text-sm text-[#8b5cf6] hover:underline">
              Try again
            </button>
          </div>
        )}

        {report && !loading && (
          <div className="space-y-8 animate-[fadeIn_0.5s_ease-out]">
            {/* Header — Score + Tier */}
            <div className="flex flex-col sm:flex-row items-center gap-6 bg-[#13131a] rounded-2xl border border-[#2a2a3a] p-6 sm:p-8">
              <div className="relative flex-shrink-0">
                <ScoreRing score={report.overall_score} />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-black text-[#f9fafb]">{report.overall_score}</span>
                  <span className="text-xs text-[#9ca3af]">/ 100</span>
                </div>
              </div>
              <div className="text-center sm:text-left">
                <h1 className="text-2xl sm:text-3xl font-black text-[#f9fafb]">
                  {report.artist_name}
                </h1>
                <div className="flex items-center justify-center sm:justify-start gap-3 mt-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-bold border ${tc.bg} ${tc.border} ${tc.text}`}>
                    {report.tier}
                  </span>
                  <span className="text-[#9ca3af] text-sm">Growth Report</span>
                </div>
                <p className="text-[#6b7280] text-sm mt-3 max-w-md">
                  Your personalized roadmap — powered by 21 Melodio AI agents working for you.
                </p>
              </div>
            </div>

            {/* Strengths */}
            <section>
              <h2 className="text-lg font-bold text-[#f9fafb] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#10b981]" />
                Strengths
              </h2>
              <div className="grid gap-3">
                {report.strengths.map((s, i) => (
                  <div key={i} className="bg-[#13131a] border border-[#10b981]/30 rounded-xl p-4 flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-[#10b981]/20 flex items-center justify-center">
                      <svg className="w-5 h-5 text-[#10b981]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-semibold text-[#f9fafb] text-sm">{s.area}</span>
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ color: scoreColor(s.score), backgroundColor: `${scoreColor(s.score)}20` }}>
                          {s.score}/100
                        </span>
                      </div>
                      <p className="text-[#9ca3af] text-sm mt-1">{s.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Gaps */}
            <section>
              <h2 className="text-lg font-bold text-[#f9fafb] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                Growth Opportunities
              </h2>
              <div className="grid gap-3">
                {report.gaps.map((g, i) => (
                  <div key={i} className="bg-[#13131a] border border-[#f59e0b]/30 rounded-xl p-4 flex items-start gap-4">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-[#f59e0b]/20 flex items-center justify-center">
                      <svg className="w-5 h-5 text-[#f59e0b]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-semibold text-[#f9fafb] text-sm">{g.area}</span>
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ color: scoreColor(g.score), backgroundColor: `${scoreColor(g.score)}20` }}>
                          {g.score}/100
                        </span>
                        {g.fixable && (
                          <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[#8b5cf6]/20 text-[#a78bfa] border border-[#8b5cf6]/30">
                            Melodio fixes this
                          </span>
                        )}
                      </div>
                      <p className="text-[#9ca3af] text-sm mt-1">{g.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Action Plan Timeline */}
            <section>
              <h2 className="text-lg font-bold text-[#f9fafb] mb-6 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#8b5cf6]" />
                Your Melodio Action Plan
              </h2>

              {/* Timeline */}
              <div className="space-y-8">
                {/* Immediate */}
                <TimelineSection
                  label="Immediate"
                  color="#8b5cf6"
                  items={report.melodio_action_plan.immediate}
                />

                {/* Week 1-4 */}
                <TimelineSection
                  label="Week 1 — 4"
                  color="#3b82f6"
                  items={report.melodio_action_plan.week_1_to_4}
                />

                {/* Month 2-6 */}
                <TimelineSection
                  label="Month 2 — 6"
                  color="#10b981"
                  items={report.melodio_action_plan.month_2_to_6}
                />
              </div>
            </section>

            {/* Artist Action Steps */}
            <section>
              <h2 className="text-lg font-bold text-[#f9fafb] mb-4 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                Your Next Steps
              </h2>
              <div className="bg-[#13131a] rounded-2xl border border-[#2a2a3a] divide-y divide-[#2a2a3a]">
                {report.melodio_action_plan.artist_action_steps.map((s) => {
                  const done = completedSteps.has(s.step);
                  return (
                    <button
                      key={s.step}
                      onClick={() => toggleStep(s.step)}
                      className="w-full text-left p-4 sm:p-5 flex items-start gap-4 hover:bg-[#1a1a24] transition-colors"
                    >
                      <div className={`flex-shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-colors ${done ? "bg-[#10b981] border-[#10b981]" : "border-[#4a4a5a]"}`}>
                        {done && (
                          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 flex-wrap">
                          <span className={`font-semibold text-sm ${done ? "text-[#6b7280] line-through" : "text-[#f9fafb]"}`}>
                            {s.action}
                          </span>
                          <span className="text-xs text-[#6b7280] bg-[#2a2a3a] px-2 py-0.5 rounded-full">
                            {s.time}
                          </span>
                        </div>
                        <p className="text-[#6b7280] text-sm mt-1">{s.why}</p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Melodio Advantage */}
            <section>
              <div className="relative overflow-hidden bg-gradient-to-br from-[#8b5cf6]/20 via-[#13131a] to-[#10b981]/20 rounded-2xl border border-[#8b5cf6]/30 p-6 sm:p-8">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-50" />
                <div className="relative">
                  <h2 className="text-xl font-black text-[#f9fafb] mb-1">The Melodio Advantage</h2>
                  <p className="text-[#9ca3af] text-sm mb-6">What you get when you build with us.</p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <AdvantageCard
                      label="AI Agents Working For You"
                      value={String(report.melodio_advantage.agents_working_for_you)}
                      accent="#8b5cf6"
                    />
                    <AdvantageCard
                      label="Estimated Monthly Value"
                      value={report.melodio_advantage.estimated_monthly_value}
                      accent="#10b981"
                    />
                    <AdvantageCard
                      label="What You Pay"
                      value={report.melodio_advantage.what_you_pay}
                      accent="#3b82f6"
                    />
                    <AdvantageCard
                      label="Revenue Split"
                      value={report.melodio_advantage.revenue_split}
                      accent="#f59e0b"
                    />
                    <AdvantageCard
                      label="Your Masters"
                      value={report.melodio_advantage.masters}
                      accent="#10b981"
                    />
                    <AdvantageCard
                      label="Contract Terms"
                      value={report.melodio_advantage.contract}
                      accent="#8b5cf6"
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* CTA */}
            <div className="text-center pt-4 pb-8">
              <button
                onClick={() => router.push("/dashboard")}
                className="bg-[#8b5cf6] hover:bg-[#7c3aed] text-white font-bold text-sm px-8 py-3.5 rounded-xl transition-colors"
                style={{ boxShadow: "0 0 30px rgba(139,92,246,0.3)" }}
              >
                Go to Dashboard
              </button>
              <p className="text-[#6b7280] text-xs mt-3">Your agents are already getting to work.</p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

function TimelineSection({ label, color, items }: { label: string; color: string; items: ActionItem[] }) {
  return (
    <div className="relative pl-8">
      {/* Timeline line */}
      <div className="absolute left-[11px] top-0 bottom-0 w-0.5" style={{ backgroundColor: `${color}30` }} />

      {/* Timeline dot */}
      <div className="absolute left-0 top-0 w-6 h-6 rounded-full border-2 flex items-center justify-center bg-[#0a0a0f]" style={{ borderColor: color }}>
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      </div>

      <div className="mb-3">
        <span className="text-sm font-bold" style={{ color }}>{label}</span>
      </div>

      <div className="space-y-3 pb-2">
        {items.map((item, i) => (
          <div key={i} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4 hover:border-[#3a3a4a] transition-colors">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="font-semibold text-[#f9fafb] text-sm">{item.action}</span>
              {item.auto && (
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#8b5cf6]/20 text-[#a78bfa] border border-[#8b5cf6]/30">
                  Auto
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs text-[#6b7280] bg-[#2a2a3a] px-2 py-0.5 rounded-full">{item.agent}</span>
            </div>
            <p className="text-[#9ca3af] text-sm">{item.what_we_do}</p>
            <p className="text-[#10b981] text-sm mt-2 font-medium">{item.your_result}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function AdvantageCard({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div className="bg-[#0a0a0f]/60 rounded-xl border border-[#2a2a3a] p-4">
      <p className="text-xs text-[#6b7280] mb-1">{label}</p>
      <p className="text-sm font-bold" style={{ color: accent }}>{value}</p>
    </div>
  );
}
