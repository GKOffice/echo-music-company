import { API_URL } from "./config";

export interface Artist {
  id: string;
  name: string;
  genre: string;
  tier: "diamond" | "fire" | "star";
  echoScore: number;
  monthlyListeners: number;
  totalStreams: number;
  photo?: string;
  pointsAvailable: number;
  pointsTotal: number;
  pricePerPoint: number;
  growthPct: number;
  holderCount?: number;
  recentBuyers?: number;
  releaseCount?: number;
}

export interface Release {
  id: string;
  artistId: string;
  title: string;
  status: "live" | "pending" | "processing" | "draft";
  streams: number;
  revenue: number;
  pointsSold: number;
  releaseDate: string;
  artwork?: string;
}

export interface PointDrop {
  id: string;
  artist: Artist;
  aiConfidence: number;
  pointsAvailable: number;
  pointsTotal: number;
  pricePerPoint: number;
  conservativeEst: number;
  expectedEst: number;
  optimisticEst: number;
  description: string;
}

export interface DemoFormData {
  artistName: string;
  email: string;
  genre: string;
  spotifyUrl: string;
  instagram: string;
  soundcloudUrl?: string;
  bio: string;
  audioFile?: File;
}

export interface AgentStatus {
  id: string;
  name: string;
  status: "online" | "busy" | "idle";
  lastActivity: string;
}

export interface DashboardArtist {
  id: string;
  name: string;
  monthly_listeners: number;
  total_streams: number;
  revenue_mtd: number;
  melodio_score: number;
  tier: string;
  points_sold: number;
  points_total: number;
  price_per_point: number;
  total_raised: number;
  paid_to_holders: number;
  next_payout: string;
}

export interface ActivityItem {
  id: string;
  icon: string;
  text: string;
  time: string;
  accent: string;
}

export interface PlatformStats {
  artists: number;
  fans: number;
  paid_to_artists: number;
  sync_placements: number;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_ARTISTS: Artist[] = [
  {
    id: "1",
    name: "Nova Vex",
    genre: "Afrobeats",
    tier: "diamond",
    echoScore: 94,
    monthlyListeners: 284000,
    totalStreams: 4200000,
    pointsAvailable: 3,
    pointsTotal: 15,
    pricePerPoint: 250,
    growthPct: 34,
    holderCount: 12,
    recentBuyers: 3,
    releaseCount: 8,
  },
  {
    id: "2",
    name: "Lyra Bloom",
    genre: "Alt R&B",
    tier: "fire",
    echoScore: 87,
    monthlyListeners: 142000,
    totalStreams: 1800000,
    pointsAvailable: 8,
    pointsTotal: 20,
    pricePerPoint: 150,
    growthPct: 22,
    holderCount: 7,
    recentBuyers: 2,
    releaseCount: 5,
  },
  {
    id: "3",
    name: "Khai Dusk",
    genre: "Trap Soul",
    tier: "fire",
    echoScore: 82,
    monthlyListeners: 98000,
    totalStreams: 950000,
    pointsAvailable: 12,
    pointsTotal: 25,
    pricePerPoint: 100,
    growthPct: 18,
    holderCount: 5,
    recentBuyers: 1,
    releaseCount: 3,
  },
  {
    id: "4",
    name: "Zara Sol",
    genre: "Pop",
    tier: "star",
    echoScore: 76,
    monthlyListeners: 67000,
    totalStreams: 620000,
    pointsAvailable: 20,
    pointsTotal: 30,
    pricePerPoint: 75,
    growthPct: 11,
    holderCount: 4,
    recentBuyers: 0,
    releaseCount: 1,
  },
  {
    id: "5",
    name: "Melo Cipher",
    genre: "Hip-Hop",
    tier: "fire",
    echoScore: 89,
    monthlyListeners: 210000,
    totalStreams: 3100000,
    pointsAvailable: 5,
    pointsTotal: 18,
    pricePerPoint: 200,
    growthPct: 28,
    holderCount: 9,
    recentBuyers: 4,
    releaseCount: 12,
  },
  {
    id: "6",
    name: "Indie Haze",
    genre: "Indie Pop",
    tier: "star",
    echoScore: 71,
    monthlyListeners: 41000,
    totalStreams: 380000,
    pointsAvailable: 25,
    pointsTotal: 35,
    pricePerPoint: 50,
    growthPct: 9,
    holderCount: 2,
    recentBuyers: 0,
    releaseCount: 2,
  },
];

const MOCK_RELEASES: Release[] = [
  {
    id: "r1",
    artistId: "1",
    title: "Midnight Drive",
    status: "live",
    streams: 1240000,
    revenue: 4960,
    pointsSold: 12,
    releaseDate: "2026-02-14",
  },
  {
    id: "r2",
    artistId: "1",
    title: "Neon Fever",
    status: "live",
    streams: 860000,
    revenue: 3440,
    pointsSold: 8,
    releaseDate: "2026-01-20",
  },
  {
    id: "r3",
    artistId: "1",
    title: "Dark Matter EP",
    status: "processing",
    streams: 0,
    revenue: 0,
    pointsSold: 0,
    releaseDate: "2026-03-22",
  },
];

const MOCK_AGENT_STATUSES: AgentStatus[] = [
  { id: "ceo", name: "CEO Agent", status: "online", lastActivity: "2 min ago" },
  { id: "ar", name: "A&R Agent", status: "busy", lastActivity: "Just now" },
  { id: "distribution", name: "Distribution Agent", status: "online", lastActivity: "5 min ago" },
  { id: "marketing", name: "Marketing Agent", status: "busy", lastActivity: "1 min ago" },
];

const MOCK_DASHBOARD_ARTIST: DashboardArtist = {
  id: "1",
  name: "Nova Vex",
  monthly_listeners: 284000,
  total_streams: 4200000,
  revenue_mtd: 8412,
  melodio_score: 94,
  tier: "Diamond",
  points_sold: 12,
  points_total: 15,
  price_per_point: 250,
  total_raised: 3000,
  paid_to_holders: 4960,
  next_payout: "Apr 1, 2026",
};

const MOCK_ACTIVITY: ActivityItem[] = [
  { id: "1", icon: "📀", text: "Midnight Drive added to 3 editorial playlists", time: "2h ago", accent: "#8b5cf6" },
  { id: "2", icon: "💰", text: "2 Melodio Points sold · $500 earned", time: "5h ago", accent: "#10b981" },
  { id: "3", icon: "🏆", text: "Milestone: 1M streams on Midnight Drive", time: "1d ago", accent: "#f59e0b" },
  { id: "4", icon: "📈", text: "Monthly listeners up 12% — Melodio Score raised to 94", time: "2d ago", accent: "#8b5cf6" },
  { id: "5", icon: "💰", text: "Royalty payout: $4,960 distributed to 12 holders", time: "3d ago", accent: "#10b981" },
  { id: "6", icon: "🎤", text: "Distribution Agent deployed Neon Fever to 47 DSPs", time: "1w ago", accent: "#9ca3af" },
];

// ─── API Functions ────────────────────────────────────────────────────────────

export async function fetchArtists(): Promise<Artist[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/artists`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_ARTISTS;
  }
}

export async function fetchArtist(id: string): Promise<Artist | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/artists/${id}`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_ARTISTS.find((a) => a.id === id) ?? MOCK_ARTISTS[0];
  }
}

export async function fetchReleases(artistId: string): Promise<Release[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/releases?artist_id=${artistId}`, {
      next: { revalidate: 30 },
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_RELEASES.filter((r) => r.artistId === artistId);
  }
}

export async function fetchPoints(): Promise<Artist[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/points`, { next: { revalidate: 30 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_ARTISTS;
  }
}

export async function fetchPointDrop(id: string): Promise<PointDrop | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/points/${id}`, { next: { revalidate: 30 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    const artist = MOCK_ARTISTS.find((a) => a.id === id) ?? MOCK_ARTISTS[0];
    return {
      id: artist.id,
      artist,
      aiConfidence: artist.echoScore,
      pointsAvailable: artist.pointsAvailable,
      pointsTotal: artist.pointsTotal,
      pricePerPoint: artist.pricePerPoint,
      conservativeEst: Math.round(artist.pricePerPoint * 0.08),
      expectedEst: Math.round(artist.pricePerPoint * 0.18),
      optimisticEst: Math.round(artist.pricePerPoint * 0.34),
      description: `${artist.name} is a rising ${artist.genre} artist with a strong streaming trajectory and high ECHO Score. This point drop gives fans fractional royalty ownership across their upcoming release catalog.`,
    };
  }
}

export async function submitDemo(data: DemoFormData): Promise<{ success: boolean; message: string }> {
  try {
    const formData = new FormData();
    formData.append("artist_name", data.artistName);
    formData.append("email", data.email);
    formData.append("genre", data.genre);
    formData.append("spotify_url", data.spotifyUrl);
    formData.append("instagram", data.instagram);
    if (data.soundcloudUrl) formData.append("soundcloud_url", data.soundcloudUrl);
    formData.append("bio", data.bio);
    if (data.audioFile) formData.append("audio", data.audioFile);

    const res = await fetch(`${API_URL}/api/v1/submissions`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error("API error");
    return { success: true, message: "We received your demo. Expect a response within 48 hours." };
  } catch {
    // Simulate success for demo
    await new Promise((r) => setTimeout(r, 1200));
    return { success: true, message: "We received your demo. Expect a response within 48 hours." };
  }
}

export async function fetchAgentStatus(): Promise<AgentStatus[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/agents/status`, { next: { revalidate: 10 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_AGENT_STATUSES;
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toString();
}

export function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

export function tierBadge(tier: Artist["tier"]): string {
  if (tier === "diamond") return "💎";
  if (tier === "fire") return "🔥";
  return "⭐";
}

// ─── Additional Interfaces ─────────────────────────────────────────────────────

export interface Listing {
  id: string;
  listing_type: string;
  listing_mode: string;
  title: string;
  creator_type: string;
  creator_name: string;
  genre: string;
  asking_price?: number | null;
  accept_points: boolean;
  accept_cash: boolean;
  monthly_streams?: number | null;
  total_streams?: number | null;
  estimated_revenue?: number | null;
  verified_listing: boolean;
  auction_ends_in_hours?: number;
  highest_bid?: number;
  bid_count?: number;
}

export interface MerchItem {
  id: string;
  title: string;
  artist: string;
  type: "download" | "stems" | "sample_pack" | "beat_license" | "exclusive" | "preset" | "bundle";
  price: number;
  description: string;
  artwork?: string;
}

export interface Songwriter {
  id: string;
  name: string;
  genre: string;
  songs_registered: number;
  monthly_earnings: number;
  bio?: string;
}

// ─── Payment API Functions ─────────────────────────────────────────────────────

export async function createCheckoutSession(
  dropId: string,
  quantity: number
): Promise<{ url: string }> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/payments/create-checkout-session`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ drop_id: dropId, quantity }),
    });
    if (!res.ok) throw new Error("Payment error");
    return res.json();
  } catch {
    return { url: "" };
  }
}

// ─── Notification Preferences ──────────────────────────────────────────────────

export async function updateNotificationPrefs(
  prefs: Record<string, boolean>
): Promise<{ success: boolean }> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/auth/notification-preferences`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(prefs),
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return { success: true }; // optimistic
  }
}

// ─── Additional Data Fetches ───────────────────────────────────────────────────

export async function fetchDealRoom(): Promise<Listing[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/deal-room`, { next: { revalidate: 30 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchDigitalMerch(): Promise<MerchItem[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/digital-merch`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchSongwriters(): Promise<Songwriter[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/songwriters`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchMyArtist(): Promise<DashboardArtist> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/artists/me`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_DASHBOARD_ARTIST;
  }
}

export async function fetchMyReleases(): Promise<Release[]> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/releases?mine=true`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_RELEASES;
  }
}

export async function fetchMyActivity(): Promise<ActivityItem[]> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/artists/me/activity`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_ACTIVITY;
  }
}

export async function fetchPlatformStats(): Promise<PlatformStats | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/analytics/platform-stats`, { next: { revalidate: 300 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return null;
  }
}

// ─── New Feature Interfaces ────────────────────────────────────────────────────

export interface OwnedPointEntry {
  artistId: string;
  artistName: string;
  genre: string;
  points: number;
  purchasePrice: number;
  currentValue: number;
  royaltiesEarned: number;
  badgeEmoji: string;
}

export interface MonthlyRoyalty {
  month: string;
  royalties: number;
  streams: number;
}

export interface FanPortfolio {
  totalPoints: number;
  totalSpent: number;
  totalEarned: number;
  portfolioValue: number;
  earningsHistory: number[];
  earningsMonths: string[];
  ownedPoints: OwnedPointEntry[];
  monthlyBreakdown: MonthlyRoyalty[];
  nextPayout: string;
}

export interface ArtistSocialLinks {
  spotify?: string;
  instagram?: string;
  tiktok?: string;
  twitter?: string;
}

export interface ArtistRelease {
  id: string;
  title: string;
  releaseDate: string;
  streams: number;
  status: "live" | "upcoming" | "processing";
}

export interface ArtistScoreBreakdown {
  streaming: number;
  engagement: number;
  playlistPotential: number;
  growthTrajectory: number;
}

export interface ArtistProfile {
  id: string;
  slug: string;
  name: string;
  genre: string;
  bio: string;
  monthlyListeners: number;
  totalStreams: number;
  pointsAvailable: number;
  pointsTotal: number;
  pricePerPoint: number;
  melodioScore: number;
  scoreBreakdown: ArtistScoreBreakdown;
  social: ArtistSocialLinks;
  releases: ArtistRelease[];
}

export interface AmbassadorReferral {
  maskedEmail: string;
  signupDate: string;
  status: "active" | "churned";
  commission: number;
}

export interface AmbassadorData {
  isAmbassador: boolean;
  totalReferrals: number;
  activeReferrals: number;
  commissionEarned: number;
  pendingCommission: number;
  referralCode: string;
  tier: "Bronze" | "Silver" | "Gold" | "Platinum";
  nextTierReferrals: number;
  referrals: AmbassadorReferral[];
}

export interface TransparencyStats {
  totalRoyaltiesPaid: number;
  totalPointsSold: number;
  activeArtists: number;
  activeFans: number;
  avgRoyaltyPerArtist: number;
}

export interface TransparencyActivity {
  id: string;
  icon: string;
  text: string;
  time: string;
}

export interface MonthlyPayout {
  month: string;
  amount: number;
}

export interface TransparencyData {
  stats: TransparencyStats;
  activityFeed: TransparencyActivity[];
  monthlyPayouts: MonthlyPayout[];
}

export interface Transaction {
  id: string;
  date: string;
  type: "purchase" | "royalty" | "withdrawal" | "system";
  description: string;
  amount: number;
  status: "completed" | "pending" | "failed";
}

export interface AppNotification {
  id: string;
  type: "royalty_payout" | "new_release" | "point_price_change" | "system_announcement";
  title: string;
  description: string;
  time: string;
  read: boolean;
}

export interface LeaderboardArtist {
  rank: number;
  name: string;
  genre: string;
  monthlyStreams: number;
  melodioScore: number;
  pointsSold: number;
  badge: string;
}

export interface LeaderboardSupporter {
  rank: number;
  username: string;
  pointsOwned: number;
  totalSpent: number;
  artistsSupported: number;
  badge: string;
}

export interface LeaderboardRisingStar {
  rank: number;
  name: string;
  genre: string;
  growthPct: number;
  weeksOnPlatform: number;
  badge: string;
}

// ─── New API Functions ─────────────────────────────────────────────────────────

const MOCK_FAN_PORTFOLIO: FanPortfolio = {
  totalPoints: 47,
  totalSpent: 4250,
  totalEarned: 892,
  portfolioValue: 5140,
  earningsHistory: [120, 145, 198, 210, 98, 121],
  earningsMonths: ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
  ownedPoints: [
    { artistId: "1", artistName: "Nova Vex", genre: "Afrobeats", points: 12, purchasePrice: 250, currentValue: 320, royaltiesEarned: 412, badgeEmoji: "💎" },
    { artistId: "2", artistName: "Lyra Bloom", genre: "Alt R&B", points: 8, purchasePrice: 150, currentValue: 178, royaltiesEarned: 234, badgeEmoji: "🔥" },
    { artistId: "5", artistName: "Melo Cipher", genre: "Hip-Hop", points: 5, purchasePrice: 200, currentValue: 240, royaltiesEarned: 156, badgeEmoji: "🔥" },
    { artistId: "6", artistName: "Indie Haze", genre: "Indie Pop", points: 22, purchasePrice: 50, currentValue: 42, royaltiesEarned: 90, badgeEmoji: "⭐" },
  ],
  monthlyBreakdown: [
    { month: "Mar 2026", royalties: 121, streams: 48200 },
    { month: "Feb 2026", royalties: 98, streams: 39100 },
    { month: "Jan 2026", royalties: 210, streams: 84000 },
    { month: "Dec 2025", royalties: 198, streams: 79200 },
    { month: "Nov 2025", royalties: 145, streams: 58000 },
    { month: "Oct 2025", royalties: 120, streams: 48000 },
  ],
  nextPayout: "April 1, 2026",
};

const MOCK_ARTIST_PROFILES: ArtistProfile[] = [
  {
    id: "1",
    slug: "nova-vex",
    name: "Nova Vex",
    genre: "Afrobeats",
    bio: "Nova Vex is a London-based Afrobeats artist blending West African rhythms with UK club culture. Signed to Melodio's inaugural artist roster in 2025, she's amassed 284K monthly listeners in just 8 months.",
    monthlyListeners: 284000,
    totalStreams: 4200000,
    pointsAvailable: 3,
    pointsTotal: 15,
    pricePerPoint: 250,
    melodioScore: 94,
    scoreBreakdown: { streaming: 24, engagement: 23, playlistPotential: 24, growthTrajectory: 23 },
    social: { spotify: "#", instagram: "#", tiktok: "#", twitter: "#" },
    releases: [
      { id: "r1", title: "Midnight Drive", releaseDate: "2026-02-14", streams: 1240000, status: "live" },
      { id: "r2", title: "Neon Fever", releaseDate: "2026-01-20", streams: 860000, status: "live" },
      { id: "r3", title: "Dark Matter EP", releaseDate: "2026-03-22", streams: 0, status: "upcoming" },
    ],
  },
  {
    id: "2",
    slug: "lyra-bloom",
    name: "Lyra Bloom",
    genre: "Alt R&B",
    bio: "Lyra Bloom crafts introspective Alt R&B with lush production and raw lyricism. Based in Atlanta, her debut EP crossed 1.8M streams in its first quarter on Melodio.",
    monthlyListeners: 142000,
    totalStreams: 1800000,
    pointsAvailable: 8,
    pointsTotal: 20,
    pricePerPoint: 150,
    melodioScore: 87,
    scoreBreakdown: { streaming: 22, engagement: 21, playlistPotential: 22, growthTrajectory: 22 },
    social: { spotify: "#", instagram: "#", tiktok: "#", twitter: "#" },
    releases: [
      { id: "r4", title: "Lavender Haze", releaseDate: "2026-01-10", streams: 980000, status: "live" },
      { id: "r5", title: "Glass", releaseDate: "2025-11-05", streams: 820000, status: "live" },
    ],
  },
];

const MOCK_AMBASSADOR: AmbassadorData = {
  isAmbassador: true,
  totalReferrals: 18,
  activeReferrals: 14,
  commissionEarned: 342.50,
  pendingCommission: 28.75,
  referralCode: "NOVA-2024",
  tier: "Gold",
  nextTierReferrals: 30,
  referrals: [
    { maskedEmail: "j***@gmail.com", signupDate: "2026-02-14", status: "active", commission: 24.50 },
    { maskedEmail: "m***@yahoo.com", signupDate: "2026-02-01", status: "active", commission: 18.75 },
    { maskedEmail: "s***@hotmail.com", signupDate: "2026-01-15", status: "churned", commission: 12.00 },
    { maskedEmail: "a***@gmail.com", signupDate: "2026-01-10", status: "active", commission: 31.25 },
    { maskedEmail: "r***@outlook.com", signupDate: "2025-12-20", status: "active", commission: 19.00 },
  ],
};

const MOCK_TRANSPARENCY: TransparencyData = {
  stats: { totalRoyaltiesPaid: 1240000, totalPointsSold: 2847, activeArtists: 127, activeFans: 8934, avgRoyaltyPerArtist: 976 },
  activityFeed: [
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
  ],
  monthlyPayouts: [
    { month: "Oct", amount: 142000 },
    { month: "Nov", amount: 168000 },
    { month: "Dec", amount: 198000 },
    { month: "Jan", amount: 221000 },
    { month: "Feb", amount: 195000 },
    { month: "Mar", amount: 243000 },
  ],
};

const MOCK_TRANSACTIONS: Transaction[] = [
  { id: "t1", date: "2026-03-10", type: "royalty", description: "Nova Vex Q1 Royalty Payout", amount: 124.50, status: "completed" },
  { id: "t2", date: "2026-03-01", type: "royalty", description: "Lyra Bloom Monthly Royalty", amount: 67.25, status: "completed" },
  { id: "t3", date: "2026-02-28", type: "purchase", description: "Purchased 2 Nova Vex Points", amount: -500.00, status: "completed" },
  { id: "t4", date: "2026-02-20", type: "royalty", description: "Melo Cipher Royalty Payout", amount: 45.00, status: "completed" },
  { id: "t5", date: "2026-02-14", type: "purchase", description: "Purchased 3 Lyra Bloom Points", amount: -450.00, status: "completed" },
  { id: "t6", date: "2026-02-01", type: "withdrawal", description: "Withdrawal to bank account ****4521", amount: -200.00, status: "completed" },
  { id: "t7", date: "2026-01-25", type: "royalty", description: "Nova Vex Royalty Payout", amount: 98.75, status: "completed" },
  { id: "t8", date: "2026-01-15", type: "purchase", description: "Purchased 5 Khai Dusk Points", amount: -500.00, status: "completed" },
  { id: "t9", date: "2026-01-10", type: "withdrawal", description: "Withdrawal to PayPal", amount: -150.00, status: "pending" },
  { id: "t10", date: "2026-01-05", type: "royalty", description: "Indie Haze Royalty Payout", amount: 22.00, status: "completed" },
];

const MOCK_NOTIFICATIONS: AppNotification[] = [
  { id: "n1", type: "royalty_payout", title: "Royalty Payout Received", description: "You received $124.50 from Nova Vex quarterly royalties.", time: "2026-03-10T14:30:00Z", read: false },
  { id: "n2", type: "new_release", title: "New Release: Dark Matter EP", description: "Nova Vex just dropped 'Dark Matter EP' — available on all streaming platforms.", time: "2026-03-09T10:00:00Z", read: false },
  { id: "n3", type: "point_price_change", title: "Point Value Update", description: "Nova Vex point value increased to $320 (+28% from your purchase price).", time: "2026-03-08T09:15:00Z", read: true },
  { id: "n4", type: "royalty_payout", title: "Royalty Payout Received", description: "You received $67.25 from Lyra Bloom monthly royalties.", time: "2026-03-01T12:00:00Z", read: true },
  { id: "n5", type: "system_announcement", title: "New Feature: Leaderboards", description: "Check out the new Melodio Leaderboards — see top artists and supporters!", time: "2026-02-28T16:00:00Z", read: true },
  { id: "n6", type: "new_release", title: "New Release: Golden Hour", description: "Zara Sol released 'Golden Hour' — now live on Spotify, Apple Music, and more.", time: "2026-02-25T11:30:00Z", read: true },
  { id: "n7", type: "point_price_change", title: "Point Value Update", description: "Lyra Bloom point value increased to $178 (+19% from your purchase price).", time: "2026-02-20T08:00:00Z", read: true },
  { id: "n8", type: "royalty_payout", title: "Royalty Payout Received", description: "You received $45.00 from Melo Cipher royalties.", time: "2026-02-20T07:45:00Z", read: true },
];

export async function fetchFanPortfolio(): Promise<FanPortfolio> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/fan/portfolio`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_FAN_PORTFOLIO;
  }
}

export async function fetchArtistBySlug(slug: string): Promise<ArtistProfile | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/artists/${slug}`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_ARTIST_PROFILES.find((a) => a.slug === slug) ?? MOCK_ARTIST_PROFILES[0];
  }
}

export async function fetchAmbassador(): Promise<AmbassadorData> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/ambassador/me`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_AMBASSADOR;
  }
}

export async function fetchTransparency(): Promise<TransparencyData> {
  try {
    const res = await fetch(`${API_URL}/api/v1/analytics/transparency`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_TRANSPARENCY;
  }
}

export async function fetchTransactions(): Promise<Transaction[]> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/transactions`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_TRANSACTIONS;
  }
}

export async function fetchNotifications(): Promise<AppNotification[]> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/notifications`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return MOCK_NOTIFICATIONS;
  }
}

export async function markAllNotificationsRead(): Promise<{ success: boolean }> {
  try {
    const token = typeof window !== "undefined" ? localStorage.getItem("melodio_token") : null;
    const res = await fetch(`${API_URL}/api/v1/notifications/read-all`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    return { success: true };
  }
}

export async function fetchLeaderboard(
  type: "artists" | "supporters" | "rising-stars"
): Promise<LeaderboardArtist[] | LeaderboardSupporter[] | LeaderboardRisingStar[]> {
  try {
    const res = await fetch(`${API_URL}/api/v1/leaderboards/${type}`, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error("API error");
    return res.json();
  } catch {
    if (type === "artists") {
      return [
        { rank: 1, name: "Nova Vex", genre: "Afrobeats", monthlyStreams: 284000, melodioScore: 94, pointsSold: 12, badge: "🔥" },
        { rank: 2, name: "Melo Cipher", genre: "Hip-Hop", monthlyStreams: 210000, melodioScore: 89, pointsSold: 13, badge: "🚀" },
        { rank: 3, name: "Lyra Bloom", genre: "Alt R&B", monthlyStreams: 142000, melodioScore: 87, pointsSold: 12, badge: "💎" },
        { rank: 4, name: "Khai Dusk", genre: "Trap Soul", monthlyStreams: 98000, melodioScore: 82, pointsSold: 13, badge: "⚡" },
        { rank: 5, name: "Zara Sol", genre: "Pop", monthlyStreams: 67000, melodioScore: 76, pointsSold: 10, badge: "🎯" },
        { rank: 6, name: "Indie Haze", genre: "Indie Pop", monthlyStreams: 41000, melodioScore: 71, pointsSold: 10, badge: "🔥" },
      ] as LeaderboardArtist[];
    }
    if (type === "supporters") {
      return [
        { rank: 1, username: "m***r", pointsOwned: 47, totalSpent: 4250, artistsSupported: 4, badge: "💎" },
        { rank: 2, username: "b***x", pointsOwned: 38, totalSpent: 3800, artistsSupported: 6, badge: "🔥" },
        { rank: 3, username: "s***k", pointsOwned: 31, totalSpent: 2900, artistsSupported: 3, badge: "🚀" },
        { rank: 4, username: "t***o", pointsOwned: 25, totalSpent: 2100, artistsSupported: 5, badge: "🎯" },
        { rank: 5, username: "j***n", pointsOwned: 22, totalSpent: 1650, artistsSupported: 4, badge: "⚡" },
      ] as LeaderboardSupporter[];
    }
    return [
      { rank: 1, name: "Indie Haze", genre: "Indie Pop", growthPct: 89, weeksOnPlatform: 6, badge: "🚀" },
      { rank: 2, name: "Khai Dusk", genre: "Trap Soul", growthPct: 67, weeksOnPlatform: 12, badge: "⚡" },
      { rank: 3, name: "Zara Sol", genre: "Pop", growthPct: 54, weeksOnPlatform: 18, badge: "🎯" },
      { rank: 4, name: "Lyra Bloom", genre: "Alt R&B", growthPct: 41, weeksOnPlatform: 32, badge: "🔥" },
      { rank: 5, name: "Nova Vex", genre: "Afrobeats", growthPct: 34, weeksOnPlatform: 38, badge: "💎" },
    ] as LeaderboardRisingStar[];
  }
}

// ─── Artist Intelligence ────────────────────────────────────────────────

export interface IntelligenceSearchResult {
  name: string;
  image: string;
  genres: string[];
  followers: number;
  spotify_id?: string;
}

export interface PredictiveAngle {
  name: string;
  score: number;
  trend: "up" | "down" | "stable";
  explanation: string;
  emoji: string;
}

export interface IntelligenceReport {
  artist_name: string;
  generated_at: string;
  melodio_score: number;
  score_breakdown: {
    music_quality: number;
    social_momentum: number;
    commercial_traction: number;
    brand_strength: number;
    market_timing: number;
  };
  predictive_angles: PredictiveAngle[];
  platform_stats: {
    spotify?: { followers: number; monthly_listeners: number; popularity: number; top_tracks: any[]; genres: string[] };
    youtube?: { subscribers: number; total_views: number; recent_videos: any[] };
    genius?: { song_count: number; pageviews: number; top_songs: any[] };
    musicbrainz?: { release_count: number; first_release: string; labels: string[]; collaborators: string[] };
    bandsintown?: { upcoming_events: number; past_events: number; events: any[] };
    wikipedia?: { summary: string; url: string };
  };
  ai_summary: string;
  sign_recommendation: { should_sign: boolean; confidence: number; reasoning: string };
  sources_used: string[];
  sources_failed: string[];
}

export async function searchArtistIntelligence(q: string): Promise<{ results: IntelligenceSearchResult[] }> {
  try {
    const res = await fetch(`${API_URL}/api/v1/intelligence/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) return { results: [] };
    return await res.json();
  } catch {
    return { results: [] };
  }
}

export async function getIntelligenceReport(name: string): Promise<IntelligenceReport | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/intelligence/report/${encodeURIComponent(name)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function compareArtists(names: string[]): Promise<any> {
  try {
    const res = await fetch(`${API_URL}/api/v1/intelligence/compare?artists=${names.map(encodeURIComponent).join(",")}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
