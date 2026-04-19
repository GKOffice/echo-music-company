-- Migration: Add missing tables for Vault, Deal Room, and External Catalog
-- Date: 2026-04-07
-- Author: B (AI CEO) — system test remediation

-- ── Deal Room: deal_listings ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deal_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL,
    creator_type VARCHAR(20) NOT NULL,       -- artist | producer | songwriter
    listing_type VARCHAR(50) NOT NULL,        -- sell_master_points | sell_publishing_points | seek_cowriter | ...
    title VARCHAR(255) NOT NULL,
    description TEXT,
    track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,
    release_id UUID REFERENCES releases(id) ON DELETE SET NULL,
    points_qty NUMERIC(10,4),
    asking_price NUMERIC(12,2),
    accept_points BOOLEAN DEFAULT FALSE,
    accept_cash BOOLEAN DEFAULT TRUE,
    points_price NUMERIC(12,2),
    genre VARCHAR(100),
    mood TEXT[],
    bpm_min INT,
    bpm_max INT,
    status VARCHAR(20) DEFAULT 'active',     -- active | closed | withdrawn | expired | completed
    views INT DEFAULT 0,
    expires_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deal_listings_status ON deal_listings(status);
CREATE INDEX IF NOT EXISTS idx_deal_listings_creator ON deal_listings(creator_id);
CREATE INDEX IF NOT EXISTS idx_deal_listings_type ON deal_listings(listing_type);

-- ── Deal Room: deal_offers ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deal_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES deal_listings(id) ON DELETE CASCADE,
    offerer_id UUID NOT NULL,
    offer_type VARCHAR(20) NOT NULL,         -- cash | points | hybrid
    cash_amount NUMERIC(12,2),
    points_offered NUMERIC(10,4),
    points_track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',    -- pending | accepted | rejected | countered | withdrawn | expired
    counter_cash NUMERIC(12,2),
    counter_points NUMERIC(10,4),
    counter_message TEXT,
    responded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deal_offers_listing ON deal_offers(listing_id);
CREATE INDEX IF NOT EXISTS idx_deal_offers_offerer ON deal_offers(offerer_id);
CREATE INDEX IF NOT EXISTS idx_deal_offers_status ON deal_offers(status);

-- ── Deal Room: deals (completed transactions) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID REFERENCES deal_listings(id) ON DELETE SET NULL,
    offer_id UUID REFERENCES deal_offers(id) ON DELETE SET NULL,
    buyer_id UUID NOT NULL,
    seller_id UUID NOT NULL,
    deal_type VARCHAR(50),
    track_id UUID REFERENCES tracks(id) ON DELETE SET NULL,
    points_transferred NUMERIC(10,4),
    cash_paid NUMERIC(12,2),
    points_paid NUMERIC(10,4),
    status VARCHAR(20) DEFAULT 'pending',    -- pending | completed | disputed | cancelled
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_id);
CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_id);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);

-- ── Deal Room: deal_messages ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS deal_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_offer_id UUID NOT NULL REFERENCES deal_offers(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,
    message TEXT NOT NULL,
    attachment_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Deal Room: external_catalog ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS external_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    artist_id UUID REFERENCES artists(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    isrc VARCHAR(20),
    spotify_url TEXT,
    apple_url TEXT,
    youtube_url TEXT,
    monthly_streams INT DEFAULT 0,
    total_streams INT DEFAULT 0,
    estimated_annual_revenue NUMERIC(12,2),
    genre VARCHAR(100),
    release_year INT,
    rights_type VARCHAR(20) DEFAULT 'master',
    status VARCHAR(20) DEFAULT 'pending',    -- pending | verified | rejected
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_external_catalog_status ON external_catalog(status);
CREATE INDEX IF NOT EXISTS idx_external_catalog_user ON external_catalog(user_id);

-- ── Vault: point_drops ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS point_drops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artist_id UUID REFERENCES artists(id) ON DELETE CASCADE,
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    title VARCHAR(255),
    points_available NUMERIC(10,4) NOT NULL,
    points_sold NUMERIC(10,4) DEFAULT 0,
    price_per_point NUMERIC(12,4) NOT NULL,
    marketing_budget_allocated NUMERIC(12,2) DEFAULT 0,
    ai_confidence_score NUMERIC(5,2),
    status VARCHAR(20) DEFAULT 'active',     -- active | sold_out | paused | expired
    drop_date TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_point_drops_status ON point_drops(status);
CREATE INDEX IF NOT EXISTS idx_point_drops_artist ON point_drops(artist_id);
CREATE INDEX IF NOT EXISTS idx_point_drops_track ON point_drops(track_id);

-- ── Vault: exchange_orders ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS exchange_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    echo_point_id UUID REFERENCES echo_points(id) ON DELETE SET NULL,
    seller_id UUID NOT NULL,
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    order_type VARCHAR(10) NOT NULL,         -- sell | buy
    points_qty NUMERIC(10,4) NOT NULL,
    price_per_point NUMERIC(12,4) NOT NULL,
    total_value NUMERIC(12,2),
    status VARCHAR(20) DEFAULT 'open',       -- open | matched | completed | cancelled | expired
    matched_order_id UUID,                   -- self-reference filled on match
    buyer_id UUID,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
    matched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exchange_orders_status ON exchange_orders(status);
CREATE INDEX IF NOT EXISTS idx_exchange_orders_track ON exchange_orders(track_id);
CREATE INDEX IF NOT EXISTS idx_exchange_orders_seller ON exchange_orders(seller_id);
CREATE INDEX IF NOT EXISTS idx_exchange_orders_type ON exchange_orders(order_type, status);
