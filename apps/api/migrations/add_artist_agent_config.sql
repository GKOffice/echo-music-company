-- Artist Agent Config
-- Stores per-artist preferences for Marketing and Creative agents
-- Set by artists via WhatsApp commands to the Comms Agent

CREATE TABLE IF NOT EXISTS artist_agent_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artist_id UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    agent_id VARCHAR(50) NOT NULL,        -- 'marketing' | 'creative'

    -- ── Marketing Agent Config ──────────────────────────────────────────────
    -- Which channels to prioritize (overrides default CHANNEL_ALLOCATION)
    preferred_channels JSONB DEFAULT '[]',          -- e.g. ["tiktok", "meta"]
    excluded_channels JSONB DEFAULT '[]',           -- e.g. ["google"]
    budget_style VARCHAR(50) DEFAULT 'balanced',    -- 'aggressive' | 'balanced' | 'conservative'
    target_audience TEXT,                           -- free text: "18-25 female, urban US"
    campaign_goals TEXT,                            -- "streams first, brand second"
    playlist_targets JSONB DEFAULT '[]',            -- artist-specified playlists to pitch
    avoid_content TEXT,                             -- what NOT to put in ads
    marketing_notes TEXT,                           -- any extra strategic notes

    -- ── Creative Agent Config ───────────────────────────────────────────────
    brand_tone VARCHAR(100),                        -- "dark and cinematic" | "bright and energetic"
    color_palette JSONB DEFAULT '{}',               -- {"primary": "#000", "accent": "#fff"}
    visual_style TEXT,                              -- "minimalist" | "maximalist" | "raw" etc.
    artist_persona TEXT,                            -- how artist wants to be portrayed
    content_do TEXT,                                -- visual directions TO follow
    content_dont TEXT,                              -- visual directions to AVOID
    sample_references TEXT,                         -- artists/visuals they want to reference
    creative_notes TEXT,                            -- any extra creative direction

    -- ── Shared ─────────────────────────────────────────────────────────────
    is_active BOOLEAN DEFAULT TRUE,
    set_via VARCHAR(50) DEFAULT 'whatsapp',         -- 'whatsapp' | 'dashboard' | 'api'
    version INTEGER DEFAULT 1,                      -- increments on each update
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (artist_id, agent_id)
);

CREATE INDEX IF NOT EXISTS idx_artist_agent_config_artist ON artist_agent_config(artist_id);
CREATE INDEX IF NOT EXISTS idx_artist_agent_config_agent ON artist_agent_config(agent_id);
