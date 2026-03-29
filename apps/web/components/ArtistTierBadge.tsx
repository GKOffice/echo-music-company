"use client";

import { getArtistTier } from "@/lib/artistTiers";

interface ArtistTierBadgeProps {
  releaseCount: number;
  showName?: boolean;
  size?: "sm" | "md";
}

export function ArtistTierBadge({ releaseCount, showName = true, size = "sm" }: ArtistTierBadgeProps) {
  const tier = getArtistTier(releaseCount);

  return (
    <span
      className="inline-flex items-center gap-1 rounded-full font-bold"
      style={{
        background: tier.glowColor,
        color: tier.badgeColor,
        border: `1px solid ${tier.badgeColor}60`,
        fontSize: size === "sm" ? 11 : 13,
        padding: size === "sm" ? "2px 8px" : "4px 12px",
      }}
    >
      <span>{tier.emoji}</span>
      {showName && <span>{tier.name}</span>}
    </span>
  );
}
