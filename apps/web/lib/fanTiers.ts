export interface FanTier {
  id: number;
  name: string;
  emoji: string;
  minPoints: number;
  skinClass: string;
  ringColor: string;
  ringStyle: "solid" | "pulse" | "animated" | "gold";
  description: string;
}

export const FAN_TIERS: FanTier[] = [
  { id: 0, name: "Listener",  emoji: "🎧", minPoints: 0,  skinClass: "tier-listener",  ringColor: "#4b5563", ringStyle: "solid",    description: "Just getting started" },
  { id: 1, name: "Supporter", emoji: "🌟", minPoints: 1,  skinClass: "tier-supporter", ringColor: "#6366f1", ringStyle: "solid",    description: "First point purchased" },
  { id: 2, name: "Believer",  emoji: "🔥", minPoints: 5,  skinClass: "tier-believer",  ringColor: "#8b5cf6", ringStyle: "pulse",    description: "5+ points across artists" },
  { id: 3, name: "Holder",    emoji: "💎", minPoints: 10, skinClass: "tier-holder",    ringColor: "#06b6d4", ringStyle: "pulse",    description: "10+ points owned" },
  { id: 4, name: "Whale",     emoji: "👑", minPoints: 25, skinClass: "tier-whale",     ringColor: "#f59e0b", ringStyle: "animated", description: "25+ points — top tier fan" },
  { id: 5, name: "Legend",    emoji: "⚡", minPoints: 50, skinClass: "tier-legend",    ringColor: "#f97316", ringStyle: "gold",     description: "50+ points — Melodio Legend" },
];

export function getFanTier(totalPoints: number): FanTier {
  for (let i = FAN_TIERS.length - 1; i >= 0; i--) {
    if (totalPoints >= FAN_TIERS[i].minPoints) return FAN_TIERS[i];
  }
  return FAN_TIERS[0];
}

export function getNextFanTier(totalPoints: number): FanTier | null {
  const next = FAN_TIERS.find(t => t.minPoints > totalPoints);
  return next ?? null;
}

export function pointsToNextTier(totalPoints: number): number {
  const next = getNextFanTier(totalPoints);
  if (!next) return 0;
  return next.minPoints - totalPoints;
}
