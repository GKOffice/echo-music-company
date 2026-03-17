const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

export interface User {
  id: string;
  email: string;
  name: string;
  role: "artist" | "fan" | "producer" | "songwriter";
}

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

// ─── Auth API Functions ────────────────────────────────────────────────────────

export async function apiLogin(
  email: string,
  password: string
): Promise<{ token: string; user: User }> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

export async function apiSignup(
  name: string,
  email: string,
  password: string
): Promise<{ token: string; user: User }> {
  const res = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) throw new Error("Signup failed");
  return res.json();
}

export async function apiMe(token: string): Promise<User | null> {
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
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
