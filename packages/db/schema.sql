-- ECHO Database Schema
-- Phase 3: Release Engine
-- PostgreSQL 16

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- Users & Auth
-- ============================================================

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255),
  role VARCHAR(20) NOT NULL CHECK (role IN ('owner','artist','producer','developer','admin')),
  status VARCHAR(20) DEFAULT 'active',
  email_verified BOOLEAN DEFAULT FALSE,
  phone_verified BOOLEAN DEFAULT FALSE,
  two_factor_enabled BOOLEAN DEFAULT FALSE,
  two_factor_secret VARCHAR(255),
  last_login_at TIMESTAMPTZ,
  last_login_ip INET,
  failed_attempts INT DEFAULT 0,
  locked_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL,
  device_fingerprint VARCHAR(255),
  ip_address INET,
  user_agent TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  revoked_at TIMESTAMPTZ
);

-- ============================================================
-- Artists
-- ============================================================

CREATE TABLE artists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  stage_name VARCHAR(255),
  genre VARCHAR(100),
  subgenres TEXT[],
  monthly_listeners INT DEFAULT 0,
  total_streams BIGINT DEFAULT 0,
  spotify_id VARCHAR(255),
  apple_id VARCHAR(255),
  youtube_channel_id VARCHAR(255),
  instagram VARCHAR(255),
  tiktok VARCHAR(255),
  twitter VARCHAR(255),
  status VARCHAR(50) DEFAULT 'prospect',
  deal_type VARCHAR(50),
  echo_score DECIMAL(6,2) DEFAULT 0,
  tier VARCHAR(50) DEFAULT 'seed',
  profile_photo_url TEXT,
  brand_guidelines_url TEXT,
  advance_amount DECIMAL(12,2) DEFAULT 0,
  recoupment_balance DECIMAL(12,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Producers
-- ============================================================

CREATE TABLE producers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  genres TEXT[],
  quality_score DECIMAL(5,2) DEFAULT 0,
  tier VARCHAR(50) DEFAULT 'newcomer',
  producer_score DECIMAL(6,2) DEFAULT 0,
  total_placements INT DEFAULT 0,
  total_streams BIGINT DEFAULT 0,
  total_earned DECIMAL(12,2) DEFAULT 0,
  repeat_artist_rate DECIMAL(5,2) DEFAULT 0,
  avg_artist_rating DECIMAL(3,2) DEFAULT 0,
  response_time_hours DECIMAL(5,2),
  portfolio_url TEXT,
  payment_email VARCHAR(255),
  stripe_account_id VARCHAR(255),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Releases
-- ============================================================

CREATE TABLE releases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id UUID REFERENCES artists(id),
  title VARCHAR(500) NOT NULL,
  type VARCHAR(50) CHECK (type IN ('single','ep','album')),
  status VARCHAR(50) DEFAULT 'draft',
  priority VARCHAR(20) DEFAULT 'standard',
  genre VARCHAR(100),
  isrc VARCHAR(20),
  upc VARCHAR(20),
  release_date DATE,
  master_audio_url TEXT,
  artwork_url TEXT,
  spotify_url TEXT,
  apple_url TEXT,
  youtube_url TEXT,
  streams_total BIGINT DEFAULT 0,
  revenue_total DECIMAL(12,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Tracks
-- ============================================================

CREATE TABLE tracks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  release_id UUID REFERENCES releases(id),
  artist_id UUID REFERENCES artists(id),
  title VARCHAR(500) NOT NULL,
  isrc VARCHAR(20),
  duration_seconds INT,
  bpm DECIMAL(6,2),
  key VARCHAR(20),
  genre VARCHAR(100),
  master_url TEXT,
  instrumental_url TEXT,
  acapella_url TEXT,
  lyrics TEXT,
  credits_json JSONB DEFAULT '{}',
  sync_tags_json JSONB DEFAULT '{}',
  streams_total BIGINT DEFAULT 0,
  revenue_total DECIMAL(12,2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ECHO Points (Fractional Ownership)
-- ============================================================

CREATE TABLE echo_points (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID REFERENCES tracks(id),
  release_id UUID REFERENCES releases(id),
  buyer_user_id UUID REFERENCES users(id),
  point_type VARCHAR(20) CHECK (point_type IN ('master','publishing','bundle')),
  points_purchased DECIMAL(8,4) NOT NULL,
  price_paid DECIMAL(12,2) NOT NULL,
  price_per_point DECIMAL(12,2) NOT NULL,
  purchase_date TIMESTAMPTZ DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'active',
  holding_period_ends TIMESTAMPTZ,
  royalties_earned DECIMAL(12,2) DEFAULT 0,
  stripe_payment_id VARCHAR(255),
  license_agreement_signed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Royalties
-- ============================================================

CREATE TABLE royalties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID REFERENCES tracks(id),
  release_id UUID REFERENCES releases(id),
  artist_id UUID REFERENCES artists(id),
  source VARCHAR(50) CHECK (source IN ('streaming','mechanical','performance','sync','youtube','neighboring','print')),
  platform VARCHAR(100),
  gross_amount DECIMAL(12,2) NOT NULL,
  net_amount DECIMAL(12,2) NOT NULL,
  currency VARCHAR(10) DEFAULT 'USD',
  period_start DATE,
  period_end DATE,
  received_at TIMESTAMPTZ,
  distributed BOOLEAN DEFAULT FALSE,
  distributed_at TIMESTAMPTZ,
  reported_by_agent VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Contracts
-- ============================================================

CREATE TABLE contracts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id UUID REFERENCES artists(id),
  type VARCHAR(50) CHECK (type IN ('single','ep','album','publishing','services','producer')),
  status VARCHAR(50) DEFAULT 'draft',
  terms_json JSONB DEFAULT '{}',
  royalty_split_artist DECIMAL(5,2),
  royalty_split_label DECIMAL(5,2),
  advance_amount DECIMAL(12,2) DEFAULT 0,
  recoupment_balance DECIMAL(12,2) DEFAULT 0,
  reversion_date DATE,
  signed_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  execution_date DATE,
  document_url TEXT,
  docusign_envelope_id VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Agent Tasks (Message Bus Log)
-- ============================================================

CREATE TABLE agent_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id VARCHAR(50) NOT NULL,
  task_type VARCHAR(100) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  priority VARCHAR(20) DEFAULT 'normal',
  payload_json JSONB DEFAULT '{}',
  result_json JSONB,
  assigned_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  release_id UUID REFERENCES releases(id),
  artist_id UUID REFERENCES artists(id)
);

-- ============================================================
-- Agent Messages
-- ============================================================

CREATE TABLE agent_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  from_agent VARCHAR(50) NOT NULL,
  to_agent VARCHAR(50),
  topic VARCHAR(100),
  priority VARCHAR(20) DEFAULT 'normal',
  payload_json JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

-- ============================================================
-- Demo Submissions
-- ============================================================

CREATE TABLE submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  received_at TIMESTAMPTZ DEFAULT NOW(),
  channel VARCHAR(50),
  referral_code VARCHAR(100),
  artist_name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(20),
  genre VARCHAR(100),
  spotify_url TEXT,
  soundcloud_url TEXT,
  youtube_url TEXT,
  instagram_url TEXT,
  tiktok_url TEXT,
  audio_url TEXT,
  total_score DECIMAL(5,2),
  category VARCHAR(20),
  ai_detected BOOLEAN DEFAULT FALSE,
  already_signed BOOLEAN DEFAULT FALSE,
  duplicate BOOLEAN DEFAULT FALSE,
  response_sent_at TIMESTAMPTZ,
  escalated_to_ar BOOLEAN DEFAULT FALSE,
  ar_decision VARCHAR(20),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CRM Contacts
-- ============================================================

CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  role VARCHAR(100),
  company VARCHAR(255),
  tags TEXT[],
  relationship_score INT DEFAULT 0,
  last_contacted_at TIMESTAMPTZ,
  last_contacted_by VARCHAR(50),
  do_not_contact_until TIMESTAMPTZ,
  preferred_channel VARCHAR(50),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Audit Log
-- ============================================================

CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  actor_type VARCHAR(20),
  actor_id UUID,
  action VARCHAR(100),
  resource_type VARCHAR(50),
  resource_id UUID,
  details JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Hub Beats
-- ============================================================

CREATE TABLE hub_beats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  producer_id UUID REFERENCES producers(id),
  title VARCHAR(255) NOT NULL,
  type VARCHAR(50) DEFAULT 'beat',
  audio_url TEXT,
  stems_urls TEXT[],
  bpm DECIMAL(6,2),
  key VARCHAR(20),
  genre TEXT[],
  mood TEXT[],
  energy INT,
  instruments TEXT[],
  quality_score DECIMAL(5,2),
  uniqueness_score DECIMAL(5,2),
  sync_readiness DECIMAL(5,2),
  available_as VARCHAR(20) DEFAULT 'non_exclusive',
  collaboration_open BOOLEAN DEFAULT TRUE,
  price_min DECIMAL(10,2),
  price_max DECIMAL(10,2),
  preview_count INT DEFAULT 0,
  save_count INT DEFAULT 0,
  purchase_count INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'available',
  placed_on_track_id UUID REFERENCES tracks(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX idx_releases_artist ON releases(artist_id);
CREATE INDEX idx_tracks_release ON tracks(release_id);
CREATE INDEX idx_tracks_artist ON tracks(artist_id);
CREATE INDEX idx_echo_points_track ON echo_points(track_id);
CREATE INDEX idx_echo_points_buyer ON echo_points(buyer_user_id);
CREATE INDEX idx_royalties_track ON royalties(track_id);
CREATE INDEX idx_royalties_artist ON royalties(artist_id);
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_id, status);
CREATE INDEX idx_agent_messages_topic ON agent_messages(topic);
CREATE INDEX idx_audit_log_actor ON audit_log(actor_id, created_at DESC);
CREATE INDEX idx_hub_beats_producer ON hub_beats(producer_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_submissions_email ON submissions(email);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contracts_artist ON contracts(artist_id);
CREATE INDEX idx_echo_points_status ON echo_points(status, buyer_user_id);

-- ============================================================
-- Expenses
-- ============================================================

CREATE TABLE IF NOT EXISTS expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artist_id UUID REFERENCES artists(id),
  release_id UUID REFERENCES releases(id),
  category VARCHAR(50) CHECK (category IN ('recording','marketing','distribution','legal','creative','advance','other')),
  amount DECIMAL(12,2) NOT NULL,
  recoupable BOOLEAN DEFAULT FALSE,
  description TEXT,
  vendor VARCHAR(255),
  paid_at TIMESTAMPTZ DEFAULT NOW(),
  created_by VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Copyright Registrations
-- ============================================================

CREATE TABLE IF NOT EXISTS copyright_registrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID REFERENCES tracks(id),
  release_id UUID REFERENCES releases(id),
  society VARCHAR(50) CHECK (society IN ('ascap','bmi','sesac','mlc','soundexchange','songtrust','copyright_office','content_id')),
  status VARCHAR(20) DEFAULT 'pending',
  registration_number VARCHAR(255),
  submitted_at TIMESTAMPTZ,
  confirmed_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- DMCA Requests
-- ============================================================

CREATE TABLE IF NOT EXISTS dmca_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  track_id UUID REFERENCES tracks(id),
  claimant VARCHAR(255),
  platform VARCHAR(100),
  claim_type VARCHAR(50),
  status VARCHAR(20) DEFAULT 'received',
  received_at TIMESTAMPTZ DEFAULT NOW(),
  responded_at TIMESTAMPTZ,
  resolved_at TIMESTAMPTZ,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_expenses_artist ON expenses(artist_id);
CREATE INDEX IF NOT EXISTS idx_copyright_track ON copyright_registrations(track_id);
CREATE INDEX IF NOT EXISTS idx_dmca_track ON dmca_requests(track_id);

-- ============================================================
-- Updated_at trigger function
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_artists_updated_at BEFORE UPDATE ON artists
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_producers_updated_at BEFORE UPDATE ON producers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_releases_updated_at BEFORE UPDATE ON releases
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_contracts_updated_at BEFORE UPDATE ON contracts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_contacts_updated_at BEFORE UPDATE ON contacts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- Digital Merchandise
-- ============================================================

CREATE TABLE digital_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artist_id UUID NOT NULL REFERENCES artists(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    product_type VARCHAR(50) NOT NULL CHECK (product_type IN ('track_download','stems','sample_pack','beat_license','exclusive_audio','digital_art','video','lyric_sheet','chord_chart','preset_pack','bundle')),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    file_url TEXT,
    preview_url TEXT,
    cover_art_url TEXT,
    file_size_mb DECIMAL(8,2),
    file_format VARCHAR(50),
    license_type VARCHAR(50) DEFAULT 'personal' CHECK (license_type IN ('personal','commercial','exclusive')),
    download_limit INTEGER DEFAULT NULL,
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    units_sold INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    melodio_fee_pct DECIMAL(5,2) DEFAULT 15.00,
    tags TEXT[],
    release_id UUID REFERENCES releases(id),
    track_id UUID REFERENCES tracks(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE digital_purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES digital_products(id),
    buyer_user_id UUID NOT NULL REFERENCES users(id),
    artist_id UUID NOT NULL REFERENCES artists(id),
    amount_paid DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    melodio_fee DECIMAL(10,2) NOT NULL,
    artist_payout DECIMAL(10,2) NOT NULL,
    stripe_payment_intent_id VARCHAR(255),
    download_token UUID DEFAULT gen_random_uuid(),
    download_count INTEGER DEFAULT 0,
    max_downloads INTEGER DEFAULT 5,
    license_key VARCHAR(100),
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending','completed','refunded','disputed')),
    expires_at TIMESTAMPTZ,
    purchased_at TIMESTAMPTZ DEFAULT NOW(),
    last_downloaded_at TIMESTAMPTZ
);

CREATE TABLE digital_bundle_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id UUID NOT NULL REFERENCES digital_products(id),
    item_id UUID NOT NULL REFERENCES digital_products(id),
    UNIQUE(bundle_id, item_id)
);

CREATE INDEX idx_digital_products_artist ON digital_products(artist_id);
CREATE INDEX idx_digital_products_type ON digital_products(product_type);
CREATE INDEX idx_digital_products_active ON digital_products(is_active);
CREATE INDEX idx_digital_purchases_product ON digital_purchases(product_id);
CREATE INDEX idx_digital_purchases_buyer ON digital_purchases(buyer_user_id);
CREATE INDEX idx_digital_purchases_token ON digital_purchases(download_token);

CREATE TRIGGER trg_digital_products_updated_at BEFORE UPDATE ON digital_products
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
