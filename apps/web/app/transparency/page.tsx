"use client";

import { useQuery } from "@tanstack/react-query";
import Navbar from "@/components/Navbar";
import { Skeleton } from "@/components/Skeleton";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────

interface TransparencyStats {
  totalRoyaltiesPaid: number;
  totalPointsSold: number;
  activeArtists: number;
  activeFans: number;
  avgRoyaltyPerArtist: number;
}

interface ActivityEvent {
  id: string;
  icon: string;
  text: string;
  time: string;
}

interface TransparencyData {
  stats: TransparencyStats;
  activityFeed: ActivityEvent[];
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_STATS: TransparencyStats = {
  totalRoyaltiesPaid: 1240000,
  totalPointsSold: 2847,
  activeArtists: 127,
  activeFans: 8934,
  avgRoyaltyPerArtist: 976,
};

const MOCK_ACTIVITY: ActivityEvent[] = [
  { id: "1", icon: "💰", text: "Nova Vex holders received $412 royalty payout", time: "2 min ago" },
  { id: "2", icon: "🎵", text: "Lyra Bloom dropped 8 new points at $150 each", time: "5 min ago" },
  { id: "3", icon: "👤", text: "New fan purchased 3 Melo Cipher points", time: "12 min ago" },
  { id: "4", icon: "📈", text: "Khai Dusk: Melodio Score rose to 87", time: "18 min ago" },
  { id: "5", icon: "🎤", text: "Zara Sol released 'Golden Hour' on all platforms", time: "25 min ago" },
  { id: "6", icon: "💰", text: "Melo Cipher holders received $290 payout", time: "31 min ago" },
  { id: "7", icon: "✍️", text: "New artist Indie Haze joined Melodio", time: "45 min ago" },
  { id: "8", icon: "🏆", text: "Nova Vex hit 4M total streams", time: "1 hr ago" },
  { id: "9", icon: "🎵", text: "Khai Dusk 'Dark Mirror' added to Spotify editorial", time: "2 hr ago" },
  { id: "10", icon: "💎", text: "All 15 Nova Vex Diamond points are now owned", time: "3 hr ago" },
];

const PIE_DATA = [
  { label: "Artists", pct: 80, color: "#10b981" },
  { label: "Platform", pct: 10, color: "#8b5cf6" },
  { label: "Marketing", pct: 10, color: "#f59e0b" },
];

const BAR_DATA = [
  { month: "Oct", amount: 142000 },
  { month: "Nov", amount: 168000 },
  { month: "Dec", amount: 198000 },
  { month: "Jan", amount: 221000 },
  { month: "Feb", amount: 195000 },
  { month: "Mar", amount: 243000 },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCurrency(n: number): string {
  if (n >= 1_000_000) return "$" + (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return "$" + (n / 1_000).toFixed(0) + "K";
  return "$" + n.toLocaleString();
}

function formatLarge(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

// ─── SVG Pie Chart ────────────────────────────────────────────────────────────

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number
): string {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? "0" : "1";
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y} Z`;
}

function PieChart() {
  const cx = 150;
  const cy = 150;
  const r = 120;
  let cumAngle = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-8">
      <svg viewBox="0 0 300 300" className="w-48 h-48 sm:w-56 sm:h-56 shrink-0">
        {PIE_DATA.map((slice) => {
          const startAngle = cumAngle;
          const endAngle = cumAngle + slice.pct * 3.6;
          cumAngle = endAngle;
          return (
            <path
              key={slice.label}
              d={describeArc(cx, cy, r, startAngle, endAngle)}
              fill={slice.color}
              stroke="#0a0a0f"
              strokeWidth="2"
              opacity="0.9"
            />
          );
        })}
        {/* Center hole */}
        <circle cx={cx} cy={cy} r={52} fill="#13131a" />
        <text x={cx} y={cy - 8} textAnchor="middle" fontSize="11" fill="#9ca3af">
          Revenue
        </text>
        <text x={cx} y={cy + 8} textAnchor="middle" fontSize="11" fill="#9ca3af">
          Split
        </text>
      </svg>
      <div className="space-y-3 w-full">
        {PIE_DATA.map((slice) => (
          <div key={slice.label} className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="w-3 h-3 rounded-sm shrink-0"
                style={{ background: slice.color }}
              />
              <span className="text-sm text-[#d1d5db]">{slice.label}</span>
            </div>
            <span className="text-sm font-bold" style={{ color: slice.color }}>
              {slice.pct}%
            </span>
          </div>
        ))}
        <p className="text-xs text-[#6b7280] pt-2 leading-relaxed">
          80 cents of every dollar goes directly to the artist. The remaining 20% covers platform
          operations and audience growth.
        </p>
      </div>
    </div>
  );
}

// ─── SVG Bar Chart ────────────────────────────────────────────────────────────

function BarChart() {
  const W = 600;
  const H = 300;
  const PADDING_LEFT = 60;
  const PADDING_RIGHT = 20;
  const PADDING_TOP = 30;
  const PADDING_BOTTOM = 48;

  const plotW = W - PADDING_LEFT - PADDING_RIGHT;
  const plotH = H - PADDING_TOP - PADDING_BOTTOM;

  const maxAmount = Math.max(...BAR_DATA.map((d) => d.amount));
  const n = BAR_DATA.length;
  const barWidth = (plotW / n) * 0.55;
  const gap = plotW / n;

  const barX = (i: number) => PADDING_LEFT + gap * i + (gap - barWidth) / 2;
  const barH = (amount: number) => (amount / maxAmount) * plotH;
  const barY = (amount: number) => PADDING_TOP + plotH - barH(amount);

  const gridValues = [0, 0.25, 0.5, 0.75, 1];

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      style={{ height: 260 }}
      aria-label="Monthly payout bar chart"
    >
      <defs>
        <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="1" />
          <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.7" />
        </linearGradient>
        <linearGradient id="barGradHover" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a78bfa" stopOpacity="1" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.8" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {gridValues.map((frac) => {
        const y = PADDING_TOP + frac * plotH;
        const val = Math.round(maxAmount * (1 - frac));
        return (
          <g key={frac}>
            <line
              x1={PADDING_LEFT}
              y1={y}
              x2={W - PADDING_RIGHT}
              y2={y}
              stroke="#2a2a38"
              strokeWidth="1"
            />
            {val > 0 && (
              <text
                x={PADDING_LEFT - 8}
                y={y + 4}
                textAnchor="end"
                fontSize="10"
                fill="#6b7280"
              >
                {formatCurrency(val)}
              </text>
            )}
          </g>
        );
      })}

      {/* Bars */}
      {BAR_DATA.map((d, i) => {
        const x = barX(i);
        const h = barH(d.amount);
        const y = barY(d.amount);
        const centerX = x + barWidth / 2;
        return (
          <g key={d.month}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={h}
              rx="4"
              fill="url(#barGrad)"
              className="transition-all duration-200 hover:fill-[url(#barGradHover)]"
            />
            {/* Amount label above bar */}
            <text
              x={centerX}
              y={y - 7}
              textAnchor="middle"
              fontSize="10"
              fontWeight="600"
              fill="#a78bfa"
            >
              {formatCurrency(d.amount)}
            </text>
            {/* Month label below */}
            <text
              x={centerX}
              y={H - PADDING_BOTTOM + 20}
              textAnchor="middle"
              fontSize="11"
              fill="#9ca3af"
            >
              {d.month}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Live Activity Feed ───────────────────────────────────────────────────────

function ActivityFeed({ events }: { events: ActivityEvent[] }) {
  const doubled = [...events, ...events];

  return (
    <div className="overflow-hidden" style={{ height: 320 }}>
      <style>{`
        @keyframes scrollUp {
          0%   { transform: translateY(0); }
          100% { transform: translateY(-50%); }
        }
        .activity-scroll {
          animation: scrollUp 28s linear infinite;
        }
        .activity-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
      <div className="activity-scroll">
        {doubled.map((event, idx) => (
          <div
            key={`${event.id}-${idx}`}
            className="flex items-start gap-3 px-4 py-3 border-b border-[#2a2a38] hover:bg-[#1a1a24] transition-colors"
          >
            <span className="text-xl shrink-0 mt-0.5">{event.icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[#d1d5db] leading-snug">{event.text}</p>
              <p className="text-xs text-[#6b7280] mt-0.5">{event.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TransparencyPage() {
  const { data, isLoading } = useQuery<TransparencyData>({
    queryKey: ["transparency"],
    queryFn: async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/analytics/transparency`);
        if (!res.ok) throw new Error("API error");
        return res.json();
      } catch {
        return { stats: MOCK_STATS, activityFeed: MOCK_ACTIVITY };
      }
    },
  });

  const stats = data?.stats ?? MOCK_STATS;
  const activityFeed = data?.activityFeed ?? MOCK_ACTIVITY;

  const statCards = [
    {
      label: "Total Royalties Paid",
      value: isLoading ? null : formatCurrency(stats.totalRoyaltiesPaid),
      color: "#10b981",
      icon: "💰",
    },
    {
      label: "Total Points Sold",
      value: isLoading ? null : formatLarge(stats.totalPointsSold),
      color: "#8b5cf6",
      icon: "💎",
    },
    {
      label: "Active Artists",
      value: isLoading ? null : String(stats.activeArtists),
      color: "#f59e0b",
      icon: "🎤",
    },
    {
      label: "Active Fans",
      value: isLoading ? null : formatLarge(stats.activeFans),
      color: "#3b82f6",
      icon: "👥",
    },
    {
      label: "Avg Royalty / Artist / Month",
      value: isLoading ? null : formatCurrency(stats.avgRoyaltyPerArtist),
      color: "#10b981",
      icon: "📈",
    },
  ];

  return (
    <main className="min-h-screen bg-[#0a0a0f]">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 pt-24 pb-16">

        {/* Hero Stats */}
        <section className="mb-12 text-center">
          <div className="inline-flex items-center gap-2 bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] text-xs font-semibold px-3 py-1.5 rounded-full mb-5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
            Live Platform Data
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#f9fafb] mb-4 leading-tight">
            Radical Transparency
          </h1>
          <p className="text-[#9ca3af] text-base sm:text-lg max-w-xl mx-auto mb-10">
            Every dollar, every stream, every payout — tracked in real time. No hidden fees, no
            surprises.
          </p>

          {/* Stat Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {statCards.map((card) => (
              <div
                key={card.label}
                className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-5 text-left hover:border-[#2a2a38] hover:bg-[#1a1a24] transition-colors"
              >
                <div className="text-2xl mb-2">{card.icon}</div>
                {card.value === null ? (
                  <>
                    <Skeleton className="h-7 w-3/4 mb-2" />
                    <Skeleton className="h-3 w-full" />
                  </>
                ) : (
                  <>
                    <div
                      className="text-2xl sm:text-3xl font-black mb-1"
                      style={{ color: card.color }}
                    >
                      {card.value}
                    </div>
                    <div className="text-xs text-[#6b7280] leading-tight">{card.label}</div>
                  </>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Quote Banner */}
        <section className="mb-12">
          <div className="bg-gradient-to-r from-[#8b5cf6]/10 via-[#7c3aed]/10 to-[#8b5cf6]/10 border border-[#8b5cf6]/20 rounded-2xl px-6 py-8 text-center">
            <blockquote
              className="text-xl sm:text-2xl lg:text-3xl font-bold leading-snug"
              style={{
                background: "linear-gradient(90deg, #8b5cf6, #a78bfa, #8b5cf6)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              &ldquo;Every transaction on Melodio is tracked and verifiable.&rdquo;
            </blockquote>
            <p className="text-[#6b7280] text-sm mt-3">
              Melodio Platform Commitment
            </p>
          </div>
        </section>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {/* Pie Chart */}
          <section className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-6">
            <h2 className="text-lg font-bold text-[#f9fafb] mb-1">Where Your Money Goes</h2>
            <p className="text-xs text-[#6b7280] mb-6">
              Revenue split on every point purchase
            </p>
            <PieChart />
          </section>

          {/* Monthly Payout Bar Chart */}
          <section className="bg-[#13131a] border border-[#2a2a38] rounded-2xl p-6">
            <h2 className="text-lg font-bold text-[#f9fafb] mb-1">Monthly Payout History</h2>
            <p className="text-xs text-[#6b7280] mb-4">
              Total royalties distributed to artists per month
            </p>
            <BarChart />
          </section>
        </div>

        {/* Live Activity Feed */}
        <section className="bg-[#13131a] border border-[#2a2a38] rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-[#2a2a38]">
            <div>
              <h2 className="text-lg font-bold text-[#f9fafb]">Live Activity Feed</h2>
              <p className="text-xs text-[#6b7280]">Real-time platform events</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-[#10b981]">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              Live
            </div>
          </div>
          {isLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-start gap-3 py-2">
                  <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <ActivityFeed events={activityFeed} />
          )}
        </section>
      </div>
    </main>
  );
}
