"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class NicheType(str, Enum):
    DENTIST = "dentist"
    RESTAURANTS = "restaurants"
    PLUMBERS = "plumbers"
    ELECTRICIANS = "electricians"
    LAWYERS = "lawyers"
    REAL_ESTATE_AGENTS = "real_estate_agents"
    COFFEE_SHOPS = "coffee_shops"
    HAIR_SALONS = "hair_salons"
    AUTO_REPAIR = "auto_repair"
    GYMS = "gyms"
    LANDSCAPERS = "landscapers"
    ROOFERS = "roofers"
    OTHER = "other"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    CONVERTED = "converted"
    ARCHIVED = "archived"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# Niche Display Labels (Romanian)
# ============================================================================

NICHE_LABELS_RO: dict[str, str] = {
    "dentist": "Dentiști",
    "restaurants": "Restaurante",
    "plumbers": "Instalatori",
    "electricians": "Electricieni",
    "lawyers": "Avocați",
    "real_estate_agents": "Agenți Imobiliari",
    "coffee_shops": "Cafenele",
    "hair_salons": "Saloane de Coafură",
    "auto_repair": "Service Auto",
    "gyms": "Săli de Fitness",
    "landscapers": "Peisagiști",
    "roofers": "Montatori Acoperișuri",
    "other": "Altele",
}

# Niche -> Google Maps search keywords
NICHE_SEARCH_QUERIES: dict[str, list[str]] = {
    "dentist": ["dentist", "stomatolog", "cabinet stomatologic", "clinica dentara", "implant dentar"],
    "restaurants": ["restaurant", "restaurante"],
    "plumbers": ["instalator", "instalatii sanitare", "plumber"],
    "electricians": ["electrician", "reparatii electrice", "instalatii electrice"],
    "lawyers": ["avocat", "cabinet avocatura", "firma de avocatura"],
    "real_estate_agents": ["agentie imobiliara", "agent imobiliar", "imobiliare"],
    "coffee_shops": ["cafenea", "coffee shop", "cofetarie"],
    "hair_salons": ["salon coafura", "salon infrumusetare", "frizerie", "coafor"],
    "auto_repair": ["service auto", "reparatii auto", "mecanic auto", "vulcanizare"],
    "gyms": ["sala fitness", "sala de forta", "gym", "sala fitness"],
    "landscapers": ["amenajari gradini", "peisagistica", "gradinar", "spatii verzi"],
    "roofers": ["reparatii acoperis", "acoperisuri", "roofer", "montaj acoperis"],
    "other": [],
}


# ============================================================================
# Request Models
# ============================================================================

class ScrapeRequest(BaseModel):
    """Request to start a lead scraping job."""
    location: str = Field(..., min_length=2, max_length=200, description="City or area name")
    niche: NicheType = Field(..., description="Business niche to scrape")
    max_results: int = Field(default=100, ge=10, le=500, description="Max results per query")


class AnalyzeRequest(BaseModel):
    """Request to analyze competitors for a specific lead."""
    lead_id: str = Field(..., description="UUID of the lead to analyze")
    top_n: int = Field(default=3, ge=1, le=5, description="Number of top competitors to analyze")


class LeadUpdateRequest(BaseModel):
    """Request to update a lead's status or notes."""
    status: Optional[LeadStatus] = None
    notes: Optional[str] = None


# ============================================================================
# Response Models
# ============================================================================

class LeadResponse(BaseModel):
    """Single lead response."""
    id: str
    name: str
    google_maps_link: Optional[str] = None
    place_id: Optional[str] = None
    niche: str
    categories: list[str] = []
    tier: int = 3
    phone: Optional[str] = None
    emails: list[str] = []
    address: Optional[str] = None
    city: str = "București"
    borough: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    review_count: int = 0
    review_rating: float = 0.0
    website_url: Optional[str] = None
    website_status: str = "missing"
    status: str = "new"
    notes: Optional[str] = None
    scraped_at: Optional[str] = None
    created_at: Optional[str] = None


class LeadListResponse(BaseModel):
    """Paginated list of leads."""
    leads: list[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class DesignTokens(BaseModel):
    """Extracted design tokens from a competitor's website."""
    color_palette: list[str] = []
    dominant_color: Optional[str] = None
    font_families: list[str] = []


class WebsiteStructure(BaseModel):
    """Structural analysis of a competitor's website."""
    sections: list[str] = []
    has_before_after: bool = False
    has_booking_form: bool = False
    has_pricing: bool = False
    has_blog: bool = False
    has_gallery: bool = False
    has_testimonials: bool = False
    has_faq: bool = False
    has_map: bool = False


class Copywriting(BaseModel):
    """Copywriting analysis."""
    h1_headline: Optional[str] = None
    h2_headlines: list[str] = []
    cta_buttons: list[str] = []
    value_propositions: list[str] = []
    tone: str = "professional"


class CompetitorData(BaseModel):
    """Full competitor analysis data."""
    name: str
    website_url: Optional[str] = None
    google_maps_link: Optional[str] = None
    rating: float = 0.0
    review_count: int = 0
    rank: int = 0
    design_tokens: DesignTokens = DesignTokens()
    structure: WebsiteStructure = WebsiteStructure()
    copywriting: Copywriting = Copywriting()
    meta: dict = {}


class CommonPatterns(BaseModel):
    """Aggregated patterns across all competitors."""
    dominant_colors: list[str] = []
    common_sections: list[str] = []
    common_cta_text: list[str] = []
    messaging_themes: list[str] = []
    recommended_structure: list[str] = []
    summary_ro: str = ""


class MarketIntelligenceResponse(BaseModel):
    """Full market intelligence response."""
    id: str
    lead_id: str
    niche: str
    location: str
    analysis_status: str
    competitors: list[CompetitorData] = []
    common_patterns: CommonPatterns = CommonPatterns()
    strategy_summary: Optional[str] = None
    error_message: Optional[str] = None
    analyzed_at: Optional[str] = None
    created_at: Optional[str] = None


class ScrapeJobResponse(BaseModel):
    """Scrape job status response."""
    id: str
    location: str
    niche: str
    query: str
    status: str
    total_results: int = 0
    filtered_leads: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None


class StatsResponse(BaseModel):
    """Dashboard statistics."""
    total_leads: int = 0
    new_leads: int = 0
    analyzed_leads: int = 0
    total_analyses: int = 0
    leads_by_niche: dict[str, int] = {}
    leads_by_tier: dict[str, int] = {}
    avg_rating: float = 0.0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str
    database: str = "disconnected"
