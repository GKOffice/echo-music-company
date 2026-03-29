export interface ArtistTier {
  id: number;
  name: string;
  emoji: string;
  minReleases: number;
  benefit: string;
  badgeColor: string;
  glowColor: string;
}

export const ARTIST_TIERS: ArtistTier[] = [
  { id: 0, name: "Emerging",       emoji: "🌱", minReleases: 1,  benefit: "Listed in marketplace",                       badgeColor: "#6b7280", glowColor: "#6b728040" },
  { id: 1, name: "Rising",         emoji: "⭐", minReleases: 3,  benefit: "Featured in genre feeds",                     badgeColor: "#6366f1", glowColor: "#6366f140" },
  { id: 2, name: "Established",    emoji: "🔥", minReleases: 7,  benefit: "Homepage rotation",                           badgeColor: "#8b5cf6", glowColor: "#8b5cf640" },
  { id: 3, name: "Signed Pro",     emoji: "💎", minReleases: 15, benefit: "Editorial playlist pitching",                 badgeColor: "#06b6d4", glowColor: "#06b6d440" },
  { id: 4, name: "Melodio Elite",  emoji: "👑", minReleases: 25, benefit: "Cross-promoted to all fan networks",          badgeColor: "#f59e0b", glowColor: "#f59e0b40" },
  { id: 5, name: "Icon",           emoji: "⚡", minReleases: 50, benefit: "Permanent featured placement + co-marketing", badgeColor: "#f97316", glowColor: "#f9731640" },
];

export function getArtistTier(releaseCount: number): ArtistTier {
  for (let i = ARTIST_TIERS.length - 1; i >= 0; i--) {
    if (releaseCount >= ARTIST_TIERS[i].minReleases) return ARTIST_TIERS[i];
  }
  return ARTIST_TIERS[0];
}
