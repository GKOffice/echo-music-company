-- Migration: Add missing columns and tables
-- Date: 2026-04-07 — Round 2 remediation
-- Author: B (AI CEO)

-- ── artists: missing columns ──────────────────────────────────────────────────
ALTER TABLE artists
  ADD COLUMN IF NOT EXISTS bio TEXT,
  ADD COLUMN IF NOT EXISTS photo_url TEXT,
  ADD COLUMN IF NOT EXISTS social_links JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS streams_total BIGINT DEFAULT 0;

-- ── echo_points: add artist_id + amount_paid aliases ─────────────────────────
ALTER TABLE echo_points
  ADD COLUMN IF NOT EXISTS artist_id UUID REFERENCES artists(id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS amount_paid NUMERIC(12,2) GENERATED ALWAYS AS (price_paid) STORED;

-- Backfill artist_id via track → release → artist chain
UPDATE echo_points ep
SET artist_id = (
    SELECT a.id FROM artists a
    JOIN releases r ON r.artist_id = a.id
    JOIN tracks t ON t.release_id = r.id
    WHERE t.id = ep.track_id
    LIMIT 1
)
WHERE ep.artist_id IS NULL AND ep.track_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_echo_points_artist ON echo_points(artist_id);

-- ── point_payouts ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS point_payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,
    echo_point_id UUID REFERENCES echo_points(id) ON DELETE SET NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    points_held NUMERIC(10,4) NOT NULL,
    royalties_generated NUMERIC(12,2) NOT NULL DEFAULT 0,
    payout_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    payout_status VARCHAR(20) DEFAULT 'pending',  -- pending | processing | paid | failed
    stripe_transfer_id VARCHAR(255),
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_point_payouts_user ON point_payouts(user_id);
CREATE INDEX IF NOT EXISTS idx_point_payouts_track ON point_payouts(track_id);
CREATE INDEX IF NOT EXISTS idx_point_payouts_status ON point_payouts(payout_status);

-- ── release_platforms ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS release_platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    release_id UUID NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,               -- spotify | apple_music | youtube | amazon | tidal | ...
    status VARCHAR(30) DEFAULT 'pending',         -- pending | submitted | live | rejected | takedown
    platform_url TEXT,
    platform_id VARCHAR(255),
    went_live_at TIMESTAMPTZ,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_release_platforms_release ON release_platforms(release_id);
CREATE INDEX IF NOT EXISTS idx_release_platforms_status ON release_platforms(status);

-- ── digital_purchases: ensure user_id column exists ──────────────────────────
ALTER TABLE digital_purchases
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- ── studio_fund_campaigns: ensure artist_id + goal_amount ────────────────────
ALTER TABLE studio_fund_campaigns
  ADD COLUMN IF NOT EXISTS artist_id UUID REFERENCES artists(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS goal_amount NUMERIC(12,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS amount_raised NUMERIC(12,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
