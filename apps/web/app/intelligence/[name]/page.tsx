"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getIntelligenceReport, type IntelligenceReport } from "@/lib/api";

// ── Score gauge component ─────────────────────────────────────────────

function ScoreGauge({ score, size = 180 }: { score: number; size?: number }) {
  const radius = (size - 20) / 2;
  const circumference = Math.PI * radius; // half circle
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? "#10b981" : score >= 60 ? "#8b5cf6" : score >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size / 2 + 20} viewBox={`0 0 ${size} ${size / 2 + 20}`}>
        {/* Background arc */}
        <path
          d={`M 10 ${size / 2 + 10} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2 + 10}`}
          fill="none" stroke="#2a2a3a" strokeWidth="12" strokeLinecap="round"
        />
        {/* Score arc */}
        <path
          d={`M 10 ${size / 2 + 10} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2 + 10}`}
          fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
        {/* Score text */}
        <text x={size / 2} y={size / 2} textAnchor="middle" className="fill-white text-4xl font-black">
          {score}
        </text>
        <text x={size / 2} y={size / 2 + 20} textAnchor="middle" className="fill-gray-400 text-xs">
          / 100
        </text>
      </svg>
    </div>
  );
}

// ── Progress bar ─────────────────────────────────────────────────────

function ScoreBar({ label, score, weight }: { label: string; score: number; weight: string }) {
  const color = score >= 80 ? "bg-[#10b981]" : score >= 60 ? "bg-[#8b5cf6]" : score >= 40 ? "bg-[#f59e0b]" : "bg-[#ef4444]";
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-300">{label} <span className="text-gray-500 text-xs">({weight})</span></span>
        <span className="text-white font-bold">{score}</span>
      </div>
      <div className="h-2 bg-[#2a2a3a] rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-1000`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

// ── Trend icon ──────────────────────────────────────────────────────

function TrendIcon({ trend }: { trend: string }) {
  if (trend === "up") return <span className="text-[#10b981] text-lg">↑</span>;
  if (trend === "down") return <span className="text-[#ef4444] text-lg">↓</span>;
  return <span className="text-gray-400 text-lg">→</span>;
}

// ── Skeleton ─────────────────────────────────────────────────────────

function ReportSkeleton() {
  return (
    <main className="min-h-screen bg-[#0a0a0f] pt-20 pb-16">
      <div className="max-w-5xl mx-auto px-4 pt-12">
        <div className="animate-pulse space-y-8">
          <div className="flex items-center gap-6">
            <div className="w-24 h-24 rounded-full bg-[#1a1a2e]" />
            <div className="space-y-3 flex-1">
              <div className="h-8 bg-[#1a1a2e] rounded w-64" />
              <div className="h-4 bg-[#1a1a2e] rounded w-40" />
            </div>
          </div>
          <div className="h-40 bg-[#1a1a2e] rounded-xl" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(6)].map((_, i) => <div key={i} className="h-32 bg-[#1a1a2e] rounded-xl" />)}
          </div>
          <div className="h-60 bg-[#1a1a2e] rounded-xl" />
        </div>
        <p className="text-center text-[#8b5cf6] mt-8 animate-pulse">
          🔍 Scanning platforms and generating AI analysis... This takes 15-30 seconds.
        </p>
      </div>
    </main>
  );
}

// ── Format numbers ──────────────────────────────────────────────────

function fmt(n: number | undefined): string {
  if (!n) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

// ── MAIN PAGE ───────────────────────────────────────────────────────

export default function IntelligenceReportPage() {
  const params = useParams();
  const router = useRouter();
  const artistName = decodeURIComponent(params.name as string);
  const [report, setReport] = useState<IntelligenceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      const data = await getIntelligenceReport(artistName);
      if (cancelled) return;
      if (!data) {
        setError("Failed to generate report. Try again.");
      } else {
        setReport(data);
      }
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, [artistName]);

  if (loading) return <ReportSkeleton />;
  if (error) {
    return (
      <main className="min-h-screen bg-[#0a0a0f] pt-20 pb-16 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error}</p>
          <button onClick={() => router.back()} className="text-[#8b5cf6] hover:underline">← Go back</button>
        </div>
      </main>
    );
  }
  if (!report) return null;

  // Normalize API response shape
  const scoreObj = (report as any).melodio_score || {};
  const melodioTotal = typeof scoreObj === "number" ? scoreObj : (scoreObj.total ?? 0);
  const bd = {
    music_quality: scoreObj.music_quality ?? 0,
    social_momentum: scoreObj.social_momentum ?? 0,
    commercial_traction: scoreObj.commercial_traction ?? 0,
    brand_strength: scoreObj.brand_strength ?? 0,
    market_timing: scoreObj.market_timing ?? 0,
  };
  // Build a unified stats object from various API response shapes
  const rawStats = (report as any).platform_stats || {};
  const stats: any = { ...rawStats };
  // Merge top-level fields into stats for the frontend
  if ((report as any).discography) stats.musicbrainz = { ...((report as any).discography), available: true };
  if ((report as any).live_events) stats.bandsintown = { ...((report as any).live_events), available: true };
  if ((report as any).genius_data) stats.genius = { ...((report as any).genius_data), available: true };
  if ((report as any).wikipedia_extract) stats.wikipedia = { summary: (report as any).wikipedia_extract, available: true };
  // predictive_angles may be object {key: {score, trend, explanation}} or array
  const rawAngles = (report as any).predictive_angles || {};
  const angles: { name: string; score: number; trend: string; explanation: string; emoji: string }[] = Array.isArray(rawAngles)
    ? rawAngles
    : Object.entries(rawAngles).map(([key, val]: [string, any]) => ({
        name: key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
        score: val.score ?? 0,
        trend: val.trend === "neutral" ? "stable" : (val.trend || "stable"),
        explanation: val.explanation || "",
        emoji: val.emoji || ({ collaboration_network: "🔗", platform_velocity: "🚀", genre_timing: "🎵", content_to_music_ratio: "📱", live_performance_trajectory: "🎤", sync_readiness: "🎬", fanbase_quality: "💎", release_cadence: "📅", cross_platform_correlation: "🔄", breakout_probability: "💥" }[key] || "📊"),
      }));
  const rawRec = (report as any).sign_recommendation || {};
  const rec = {
    should_sign: rawRec.should_sign === true || rawRec.decision === "yes" || rawRec.decision === "Yes",
    confidence: rawRec.confidence ?? 0,
    reasoning: typeof rawRec.reasoning === "string" ? rawRec.reasoning : JSON.stringify(rawRec.reasoning || ""),
  };
  const aiSummary = (report as any).executive_summary || (report as any).ai_summary || "";
  const discography = ((report as any).discography || []) as { title: string; date: string; status: string }[];

  return (
    <main className="min-h-screen bg-[#0a0a0f] pt-20 pb-16">
      <div className="max-w-5xl mx-auto px-4 pt-8">

        {/* Back + header */}
        <Link href="/intelligence" className="text-[#8b5cf6] hover:underline text-sm mb-6 inline-block">← Back to Search</Link>

        <div className="flex flex-col md:flex-row items-start md:items-center gap-6 mb-10">
          <div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-gradient-to-br from-[#8b5cf6] to-[#10b981] flex items-center justify-center shrink-0">
            <span className="text-white text-3xl md:text-4xl font-black">{artistName[0]}</span>
          </div>
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-black text-white">{report.artist_name}</h1>
            {(() => {
              const genres = (report as any).genres || stats.spotify?.genres || [];
              const genreClass = (report as any).genre_classification;
              const allGenres = genres.length > 0 ? genres : (genreClass ? genreClass.split(/[,\/]/).map((g: string) => g.trim()) : []);
              return allGenres.length > 0 ? (
                <div className="flex flex-wrap gap-2 mt-2">
                  {allGenres.slice(0, 5).map((g: string) => (
                    <span key={g} className="bg-[#8b5cf6]/10 text-[#8b5cf6] text-xs px-3 py-1 rounded-full border border-[#8b5cf6]/20">{g}</span>
                  ))}
                </div>
              ) : null;
            })()}
            <div className="flex flex-wrap gap-4 mt-3 text-xs text-gray-400">
              {((report as any).sources_used || []).map((s: any) => {
                const label = typeof s === "string" ? s : s?.source || String(s);
                return <span key={label} className="flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#10b981] rounded-full" />{label}</span>;
              })}
              {((report as any).sources_unavailable || (report as any).sources_failed || []).map((s: any, i: number) => {
                const label = typeof s === "string" ? s : s?.source || String(s);
                return <span key={`${label}-${i}`} className="flex items-center gap-1"><span className="w-1.5 h-1.5 bg-gray-600 rounded-full" />{label} (no data)</span>;
              })}
            </div>
          </div>
        </div>

        {/* ── Melodio Score ─────────────────────────────────────── */}
        <section className="bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-6 md:p-8 mb-6">
          <h2 className="text-lg font-bold text-white mb-6 text-center">Melodio Score</h2>
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ScoreGauge score={melodioTotal} />
            <div className="flex-1 w-full">
              <ScoreBar label="Music Quality" score={bd.music_quality} weight="35%" />
              <ScoreBar label="Social Momentum" score={bd.social_momentum} weight="20%" />
              <ScoreBar label="Commercial Traction" score={bd.commercial_traction} weight="25%" />
              <ScoreBar label="Brand Strength" score={bd.brand_strength} weight="10%" />
              <ScoreBar label="Market Timing" score={bd.market_timing} weight="10%" />
            </div>
          </div>
        </section>

        {/* ── Sign Recommendation ──────────────────────────────── */}
        <section className={`border rounded-2xl p-6 mb-6 ${rec.should_sign ? "bg-[#10b981]/5 border-[#10b981]/30" : "bg-[#f59e0b]/5 border-[#f59e0b]/30"}`}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className={`text-4xl ${rec.should_sign ? "" : ""}`}>
              {rec.should_sign ? "✅" : "⏳"}
            </div>
            <div className="flex-1">
              <h3 className="text-white font-bold text-lg">
                {rec.should_sign ? "Recommended to Sign" : "Not Recommended Yet"}
              </h3>
              <p className="text-gray-400 text-sm mt-1">{rec.reasoning}</p>
            </div>
            <div className="text-right shrink-0">
              <div className="text-2xl font-black text-white">{rec.confidence}%</div>
              <div className="text-xs text-gray-400">confidence</div>
            </div>
          </div>
        </section>

        {/* ── Platform Stats ───────────────────────────────────── */}
        <section className="mb-6">
          <h2 className="text-lg font-bold text-white mb-4">Platform Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {(stats.spotify || stats.chartmetric) && (
              <StatCard icon="🎵" platform="Spotify" stats={[
                {
                  label: "Followers",
                  value: (stats.spotify?.followers && stats.spotify.followers > 0)
                    ? fmt(stats.spotify.followers)
                    : (stats.chartmetric?.sp_followers && stats.chartmetric.sp_followers > 0)
                    ? fmt(stats.chartmetric.sp_followers)
                    : "—"
                },
                {
                  label: "Monthly Listeners",
                  value: (stats.chartmetric?.sp_monthly_listeners && stats.chartmetric.sp_monthly_listeners > 0)
                    ? fmt(stats.chartmetric.sp_monthly_listeners)
                    : (stats.spotify?.monthly_listeners && stats.spotify.monthly_listeners > 0)
                    ? fmt(stats.spotify.monthly_listeners)
                    : "—"
                },
                {
                  label: "Popularity",
                  value: (stats.spotify?.popularity && stats.spotify.popularity > 0)
                    ? `${stats.spotify.popularity}/100`
                    : (stats.chartmetric?.cm_score && stats.chartmetric.cm_score > 0)
                    ? `${Math.round(stats.chartmetric.cm_score)}/100 (CM)`
                    : "—"
                },
              ]} />
            )}
            {stats.youtube?.subscribers !== undefined && (
              <StatCard icon="🎬" platform="YouTube" stats={[
                { label: "Subscribers", value: fmt(stats.youtube.subscribers) },
                { label: "Total Views", value: fmt(stats.youtube.total_views) },
              ]} />
            )}
            {stats.genius?.song_count !== undefined && (
              <StatCard icon="📝" platform="Genius" stats={[
                { label: "Songs", value: fmt(stats.genius.song_count) },
                { label: "Pageviews", value: fmt(stats.genius.pageviews) },
              ]} />
            )}
            {stats.bandsintown?.upcoming_events !== undefined && (
              <StatCard icon="🎤" platform="Live Shows" stats={[
                { label: "Upcoming", value: String(stats.bandsintown.upcoming_events) },
                { label: "Past Events", value: fmt(stats.bandsintown.past_events) },
              ]} />
            )}
            {stats.musicbrainz?.release_count !== undefined && (
              <StatCard icon="💿" platform="Discography" stats={[
                { label: "Releases", value: fmt(stats.musicbrainz.release_count) },
                { label: "First Release", value: stats.musicbrainz.first_release || "—" },
              ]} />
            )}
          </div>
        </section>

        {/* ── 10 Predictive Signals ────────────────────────────── */}
        {angles.length > 0 && (
          <section className="mb-6">
            <h2 className="text-lg font-bold text-white mb-4">Predictive Signals</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {angles.map((angle, i) => (
                <div key={i} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4 hover:border-[#8b5cf6]/30 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{angle.emoji}</span>
                      <span className="text-white font-semibold text-sm">{angle.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendIcon trend={angle.trend} />
                      <span className={`text-lg font-black ${angle.score >= 70 ? "text-[#10b981]" : angle.score >= 40 ? "text-[#8b5cf6]" : "text-[#f59e0b]"}`}>
                        {angle.score}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-400 text-xs leading-relaxed">{angle.explanation}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── Key Strengths & Risks ─────────────────────────────── */}
        {(((report as any).key_strengths?.length > 0) || ((report as any).key_risks?.length > 0)) && (
          <section className="mb-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {(report as any).key_strengths?.length > 0 && (
              <div className="bg-[#10b981]/5 border border-[#10b981]/20 rounded-xl p-5">
                <h3 className="text-[#10b981] font-bold text-sm mb-3">✅ Key Strengths</h3>
                <ul className="space-y-2">
                  {(report as any).key_strengths.map((s: string, i: number) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <span className="text-[#10b981] shrink-0 mt-0.5">•</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(report as any).key_risks?.length > 0 && (
              <div className="bg-[#f59e0b]/5 border border-[#f59e0b]/20 rounded-xl p-5">
                <h3 className="text-[#f59e0b] font-bold text-sm mb-3">⚠️ Key Risks</h3>
                <ul className="space-y-2">
                  {(report as any).key_risks.map((s: string, i: number) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <span className="text-[#f59e0b] shrink-0 mt-0.5">•</span>{s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {/* ── Collaborators ─────────────────────────────────────── */}
        {(((report as any).notable_collaborators?.length > 0) || (stats.musicbrainz?.collaborators?.length > 0)) && (
          <section className="mb-6">
            <h2 className="text-lg font-bold text-white mb-4">Collaboration Network</h2>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <div className="flex flex-wrap gap-2">
                {((report as any).notable_collaborators || stats.musicbrainz?.collaborators || []).map((c: string, i: number) => (
                  <span key={i} className="bg-[#8b5cf6]/10 text-[#8b5cf6] text-xs px-3 py-1.5 rounded-full border border-[#8b5cf6]/20">{c}</span>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ── AI Executive Summary ─────────────────────────────── */}
        {aiSummary && (
          <section className="mb-6">
            <h2 className="text-lg font-bold text-white mb-4">AI Executive Summary</h2>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-2xl p-6">
              <div className="prose prose-invert prose-sm max-w-none">
                {aiSummary.split("\n").filter(Boolean).map((p: string, i: number) => (
                  <p key={i} className="text-gray-300 leading-relaxed mb-3 last:mb-0">{p}</p>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ── Wikipedia ────────────────────────────────────────── */}
        {stats.wikipedia?.summary && (
          <section className="mb-6">
            <h2 className="text-lg font-bold text-white mb-4">Background</h2>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-5">
              <p className="text-gray-400 text-sm leading-relaxed">{stats.wikipedia.summary}</p>
              {stats.wikipedia.url && (
                <a href={stats.wikipedia.url} target="_blank" rel="noopener noreferrer"
                   className="text-[#8b5cf6] text-xs hover:underline mt-2 inline-block">
                  Read more on Wikipedia →
                </a>
              )}
            </div>
          </section>
        )}

        {/* ── Top Tracks ───────────────────────────────────────── */}
        {stats.spotify?.top_tracks && stats.spotify.top_tracks.length > 0 && (
          <section className="mb-6">
            <h2 className="text-lg font-bold text-white mb-4">Top Tracks</h2>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              {stats.spotify.top_tracks.slice(0, 5).map((t: any, i: number) => (
                <div key={i} className="flex items-center gap-4 px-5 py-3 border-b border-[#2a2a3a] last:border-0">
                  <span className="text-gray-500 text-sm font-mono w-5">{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm font-medium truncate">{t.name || t.title}</div>
                    {t.album && <div className="text-gray-500 text-xs truncate">{t.album}</div>}
                  </div>
                  {t.popularity && (
                    <div className="text-xs text-gray-400 shrink-0">{t.popularity}/100</div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── Upcoming Shows ───────────────────────────────────── */}
        {stats.bandsintown?.events && stats.bandsintown.events.length > 0 && (
          <section className="mb-10">
            <h2 className="text-lg font-bold text-white mb-4">Upcoming Shows</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {stats.bandsintown.events.slice(0, 6).map((e: any, i: number) => (
                <div key={i} className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4">
                  <div className="text-white text-sm font-medium">{e.venue || "TBA"}</div>
                  <div className="text-gray-400 text-xs mt-1">{e.location || ""}</div>
                  <div className="text-[#8b5cf6] text-xs mt-1">{e.date || ""}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── Discography ─────────────────────────────────────── */}
        {discography.length > 0 && (
          <section className="mb-6">
            <h2 className="text-lg font-bold text-white mb-4">Discography</h2>
            <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl overflow-hidden">
              {discography.slice(0, 10).map((r, i) => (
                <div key={i} className="flex items-center gap-4 px-5 py-3 border-b border-[#2a2a3a] last:border-0">
                  <span className="text-gray-500 text-xs font-mono w-16 shrink-0">{r.date || "—"}</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm font-medium truncate">{r.title}</div>
                  </div>
                  {r.status && (
                    <span className={`text-xs px-2 py-0.5 rounded-full shrink-0 ${r.status === "Official" ? "bg-[#10b981]/10 text-[#10b981]" : "bg-gray-700/50 text-gray-400"}`}>{r.status}</span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Footer meta */}
        <div className="text-center text-gray-600 text-xs pb-8">
          Report generated {(report as any).generated_at ? new Date((report as any).generated_at).toLocaleString() : "just now"} • 
          Sources: {((report as any).sources_used || []).map((s: any) => typeof s === "string" ? s : s?.source).join(", ") || "AI analysis"}
        </div>
      </div>
    </main>
  );
}

// ── Stat card ────────────────────────────────────────────────────────

function StatCard({ icon, platform, stats }: { icon: string; platform: string; stats: { label: string; value: string }[] }) {
  return (
    <div className="bg-[#13131a] border border-[#2a2a3a] rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{icon}</span>
        <span className="text-white font-semibold text-sm">{platform}</span>
      </div>
      {stats.map((s, i) => (
        <div key={i} className="flex justify-between text-xs mb-1.5 last:mb-0">
          <span className="text-gray-400">{s.label}</span>
          <span className="text-white font-medium">{s.value}</span>
        </div>
      ))}
    </div>
  );
}
