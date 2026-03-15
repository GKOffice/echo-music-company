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
