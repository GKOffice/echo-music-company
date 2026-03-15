/**
 * ECHO Shared TypeScript Types
 */

export interface Artist {
  id: string;
  name: string;
  stage_name: string;
  genre: string;
  monthly_listeners: number;
  echo_score: number;
  tier: "SEED" | "RISING" | "STAR" | "HOT" | "DIAMOND" | "LEGEND";
  status: "prospect" | "signed" | "suspended" | "released";
}

export interface Release {
  id: string;
  artist_id: string;
  title: string;
  type: "single" | "ep" | "album" | "mixtape";
  status: "draft" | "in_pipeline" | "distributed" | "live" | "pulled";
  release_date: string | null;
  streams_total: number;
  revenue_total: number;
}

export interface EchoPoint {
  id: string;
  track_id: string;
  buyer_user_id: string;
  point_type: "standard" | "gold" | "platinum";
  points_purchased: number;
  price_paid: number;
  royalties_earned: number;
  status: "active" | "transferred" | "redeemed";
}

export interface Track {
  id: string;
  release_id: string;
  title: string;
  isrc: string | null;
  bpm: number | null;
  key: string | null;
  genre: string | null;
  streams_total: number;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
