/**
 * ECHO Shared Configuration Constants
 */

export const ECHO_TIERS = {
  SEED:    { name: "Seed",    min_score: 0,    max_score: 199  },
  RISING:  { name: "Rising",  min_score: 200,  max_score: 399  },
  STAR:    { name: "Star",    min_score: 400,  max_score: 599  },
  HOT:     { name: "Hot",     min_score: 600,  max_score: 799  },
  DIAMOND: { name: "Diamond", min_score: 800,  max_score: 949  },
  LEGEND:  { name: "Legend",  min_score: 950,  max_score: 1000 },
} as const;

export const POINT_LIMITS = {
  MAX_SOLD_PER_TRACK:    25,
  ARTIST_MIN_RETAINED:   30,
  ARTIST_MAX_SELL:       10,
} as const;

export const ARTIST_SPLITS = {
  PRE_RECOUP:  { artist: 0.60, label: 0.40 },
  POST_RECOUP: { artist: 0.60, label: 0.40 },
} as const;

export const BUILD_PHASES = [
  { phase: 0, name: "Foundation",    description: "Infrastructure, DB schema, API, agent framework" },
  { phase: 1, name: "Core Ops",      description: "All 21 agents live, internal dashboard, first artist" },
  { phase: 2, name: "First Release", description: "Sign artist, produce track, distribute worldwide" },
  { phase: 3, name: "Points Store",  description: "ECHO Points live, fan purchases, royalty payouts" },
  { phase: 4, name: "Open Platform", description: "À la carte services, producer hub, external labels" },
  { phase: 5, name: "Scale",         description: "100+ artists, automated everything, profitability" },
] as const;

export const AGENT_IDS = [
  "ceo",
  "ar",
  "production",
  "distribution",
  "marketing",
  "analytics",
  "social",
  "finance",
  "legal",
  "creative",
  "sync",
  "artist_dev",
  "pr",
  "comms",
  "qc",
  "infrastructure",
  "intake",
  "merch",
  "youtube",
  "hub",
  "vault",
] as const;

export type AgentId = typeof AGENT_IDS[number];
export type EchoTier = keyof typeof ECHO_TIERS;
