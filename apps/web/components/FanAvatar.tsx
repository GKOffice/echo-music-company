"use client";

import { getFanTier } from "@/lib/fanTiers";

interface FanAvatarProps {
  totalPoints: number;
  initial?: string;
  size?: "sm" | "md" | "lg";
  showBadge?: boolean;
}

const SIZE_MAP = {
  sm: { outer: 36, inner: 28, badge: 14, text: "text-xs" },
  md: { outer: 48, inner: 38, badge: 18, text: "text-sm" },
  lg: { outer: 72, inner: 58, badge: 24, text: "text-lg" },
};

export function FanAvatar({ totalPoints, initial = "F", size = "md", showBadge = true }: FanAvatarProps) {
  const tier = getFanTier(totalPoints);
  const s = SIZE_MAP[size];
  const isPulse = tier.ringStyle === "pulse";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: s.outer, height: s.outer }}>
      {/* Ring */}
      <div
        className={`absolute inset-0 rounded-full ${isPulse ? "animate-pulse" : ""}`}
        style={{
          background: tier.ringStyle === "gold"
            ? `conic-gradient(#f59e0b, #fbbf24, #f97316, #f59e0b)`
            : `conic-gradient(${tier.ringColor}, ${tier.ringColor}80, ${tier.ringColor})`,
          padding: 2,
        }}
      />
      {/* Avatar */}
      <div
        className={`relative rounded-full flex items-center justify-center font-bold text-white ${s.text}`}
        style={{
          width: s.inner,
          height: s.inner,
          background: `linear-gradient(135deg, ${tier.ringColor}60, #0a0a0f)`,
          border: `2px solid #0a0a0f`,
        }}
      >
        {initial.toUpperCase()}
      </div>
      {/* Badge */}
      {showBadge && (
        <div
          className="absolute -bottom-1 -right-1 rounded-full flex items-center justify-center bg-[#0a0a0f]"
          style={{ width: s.badge, height: s.badge, fontSize: s.badge * 0.6 }}
        >
          {tier.emoji}
        </div>
      )}
    </div>
  );
}
