-- ============================================================================
-- LeadGen & Competitor Intelligence Pipeline
-- Supabase PostgreSQL Schema
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE lead_status AS ENUM (
    'new',
    'contacted',
    'analyzing',
    'analyzed',
    'converted',
    'archived'
);

CREATE TYPE niche_type AS ENUM (
    'dentist',
    'restaurants',
    'plumbers',
    'electricians',
    'lawyers',
    'real_estate_agents',
    'coffee_shops',
    'hair_salons',
    'auto_repair',
    'gyms',
    'landscapers',
    'roofers',
    'other'
);

CREATE TYPE analysis_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed'
);

-- ============================================================================
-- TABLE: leads
-- Stores "No Website" businesses found via Google Maps scraping (Phase 1)
-- ============================================================================

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Business Identity
    name TEXT NOT NULL,
    google_maps_link TEXT,
    place_id TEXT UNIQUE,
    cid TEXT,
    
    -- Classification
    niche niche_type NOT NULL DEFAULT 'other',
    categories TEXT[] DEFAULT '{}',
    tier SMALLINT DEFAULT 3 CHECK (tier BETWEEN 1 AND 3),
    
    -- Contact Information
    phone TEXT,
    emails TEXT[] DEFAULT '{}',
    
    -- Location
    address TEXT,
    city TEXT DEFAULT 'București',
    borough TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'RO',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    
    -- Google Maps Metrics
    review_count INTEGER DEFAULT 0,
    review_rating NUMERIC(2,1) DEFAULT 0.0,
    
    -- Website Status
    website_url TEXT,
    website_status TEXT DEFAULT 'missing', -- 'missing', '404', 'error'
    
    -- Lead Management
    status lead_status DEFAULT 'new',
    notes TEXT,
    
    -- Metadata
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_leads_niche ON leads(niche);
CREATE INDEX idx_leads_city ON leads(city);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_tier ON leads(tier);
CREATE INDEX idx_leads_rating ON leads(review_rating DESC);
CREATE INDEX idx_leads_review_count ON leads(review_count DESC);
CREATE INDEX idx_leads_place_id ON leads(place_id);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);

-- ============================================================================
-- TABLE: market_intelligence
-- Stores the "Winning Formula" competitor analysis results (Phase 2)
-- ============================================================================

CREATE TABLE IF NOT EXISTS market_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Link to the original lead
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    -- Analysis metadata
    niche niche_type NOT NULL,
    location TEXT NOT NULL,
    analysis_status analysis_status DEFAULT 'pending',
    
    -- Competitor data (structured JSON array)
    competitors JSONB DEFAULT '[]'::jsonb,
    /*
    competitors structure:
    [
        {
            "name": "Competitor Name",
            "website_url": "https://...",
            "google_maps_link": "https://...",
            "rating": 4.8,
            "review_count": 245,
            "rank": 1,
            "design_tokens": {
                "color_palette": ["#0055FF", "#FFFFFF", "#333333"],
                "dominant_color": "#0055FF",
                "font_families": ["Inter", "Roboto"]
            },
            "structure": {
                "sections": ["hero", "services", "testimonials", "gallery", "contact"],
                "has_before_after": false,
                "has_booking_form": true,
                "has_pricing": false,
                "has_blog": true,
                "has_gallery": true,
                "has_testimonials": true,
                "has_faq": false,
                "has_map": true
            },
            "copywriting": {
                "h1_headline": "Your Smile, Our Priority",
                "h2_headlines": ["Services", "About Us"],
                "cta_buttons": ["Book Now", "Call Us"],
                "value_propositions": ["Pain-Free", "Modern Equipment"],
                "tone": "professional"
            },
            "meta": {
                "title": "Page Title",
                "description": "Meta description",
                "og_image": "https://..."
            }
        }
    ]
    */
    
    -- Aggregated insights (AI-generated summary)
    common_patterns JSONB DEFAULT '{}'::jsonb,
    /*
    common_patterns structure:
    {
        "dominant_colors": ["#0055FF", "#FFFFFF"],
        "common_sections": ["hero", "services", "testimonials"],
        "common_cta_text": ["Programează", "Sună acum"],
        "messaging_themes": ["Pain-Free", "Modern", "Professional"],
        "recommended_structure": ["hero", "services", "gallery", "testimonials", "contact"],
        "summary_ro": "Competitorii folosesc albastru (#0055FF) și se concentrează pe mesaje de tip 'Fără durere'"
    }
    */
    
    -- Strategy recommendation
    strategy_summary TEXT,
    
    -- Error tracking
    error_message TEXT,
    
    -- Metadata
    analyzed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_mi_lead_id ON market_intelligence(lead_id);
CREATE INDEX idx_mi_niche ON market_intelligence(niche);
CREATE INDEX idx_mi_status ON market_intelligence(analysis_status);
CREATE INDEX idx_mi_created_at ON market_intelligence(created_at DESC);

-- ============================================================================
-- TABLE: scrape_jobs
-- Tracks scraping job status for the pipeline
-- ============================================================================

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Job parameters
    location TEXT NOT NULL,
    niche niche_type NOT NULL,
    query TEXT NOT NULL,
    
    -- Job status
    status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    total_results INTEGER DEFAULT 0,
    filtered_leads INTEGER DEFAULT 0,
    
    -- Error tracking
    error_message TEXT,
    
    -- Metadata
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON scrape_jobs(status);
CREATE INDEX idx_jobs_created_at ON scrape_jobs(created_at DESC);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_mi_updated_at
    BEFORE UPDATE ON market_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_jobs ENABLE ROW LEVEL SECURITY;

-- Service role policies (for backend API)
CREATE POLICY "Service role full access on leads"
    ON leads FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on market_intelligence"
    ON market_intelligence FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role full access on scrape_jobs"
    ON scrape_jobs FOR ALL
    USING (true)
    WITH CHECK (true);

-- Anon/authenticated read-only policies
CREATE POLICY "Authenticated users can read leads"
    ON leads FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can read market_intelligence"
    ON market_intelligence FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Authenticated users can read scrape_jobs"
    ON scrape_jobs FOR SELECT
    TO authenticated
    USING (true);
