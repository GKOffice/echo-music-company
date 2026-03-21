-- Migration: add_agent_memory
-- Persistent learning store for all ECHO agents.
-- Failure patterns survive restarts and are injected into future LLM prompts.

CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    error_type VARCHAR(50),
    input_summary TEXT,
    bad_output_summary TEXT,
    correction TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_success BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_lookup
    ON agent_memory(agent_id, task_type, created_at DESC);

-- -----------------------------------------------------------------------
-- Seed: known hallucination patterns
-- These prevent the A&R agent from ever repeating these fabrications.
-- -----------------------------------------------------------------------

INSERT INTO agent_memory (
    agent_id, task_type, error_type,
    input_summary, bad_output_summary, correction,
    confidence_score, is_success
)
SELECT
    'ar',
    'review_artist',
    'HALLUCINATION',
    '{"artist_name": "Dorin Hirvi"}',
    '{"name": "Dorin Hirvi", "spotify_id": "3abc123fake", "monthly_listeners": 45000, "genre": "electronic", "label": "Independent"}',
    'Dorin Hirvi does not exist in Spotify, MusicBrainz, or Chartmetric. All details were fabricated. Return found=false for unknown artists with no verified external ID.',
    0.0,
    FALSE
WHERE NOT EXISTS (
    SELECT 1 FROM agent_memory
    WHERE agent_id = 'ar'
      AND task_type = 'review_artist'
      AND input_summary LIKE '%Dorin Hirvi%'
);
