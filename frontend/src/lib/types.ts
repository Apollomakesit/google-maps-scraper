/** Core types matching the FastAPI backend models. */

export type NicheType =
  | "dentist"
  | "restaurants"
  | "plumbers"
  | "electricians"
  | "lawyers"
  | "real_estate_agents"
  | "coffee_shops"
  | "hair_salons"
  | "auto_repair"
  | "gyms"
  | "landscapers"
  | "roofers"
  | "other";

export type LeadStatus =
  | "new"
  | "contacted"
  | "analyzing"
  | "analyzed"
  | "converted"
  | "archived";

export type AnalysisStatus = "pending" | "in_progress" | "completed" | "failed";

export const NICHE_LABELS: Record<NicheType, string> = {
  dentist: "Dentiști",
  restaurants: "Restaurante",
  plumbers: "Instalatori",
  electricians: "Electricieni",
  lawyers: "Avocați",
  real_estate_agents: "Agenți Imobiliari",
  coffee_shops: "Cafenele",
  hair_salons: "Saloane de Coafură",
  auto_repair: "Service Auto",
  gyms: "Săli de Fitness",
  landscapers: "Peisagiști",
  roofers: "Montatori Acoperișuri",
  other: "Altele",
};

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new: "Nou",
  contacted: "Contactat",
  analyzing: "Se analizează",
  analyzed: "Analizat",
  converted: "Convertit",
  archived: "Arhivat",
};

export interface Lead {
  id: string;
  name: string;
  google_maps_link: string | null;
  place_id: string | null;
  niche: NicheType;
  categories: string[];
  tier: number;
  phone: string | null;
  emails: string[];
  address: string | null;
  city: string;
  borough: string | null;
  latitude: number | null;
  longitude: number | null;
  review_count: number;
  review_rating: number;
  website_url: string | null;
  website_status: string;
  status: LeadStatus;
  notes: string | null;
  scraped_at: string | null;
  created_at: string | null;
}

export interface LeadListResponse {
  leads: Lead[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface DesignTokens {
  color_palette: string[];
  dominant_color: string | null;
  font_families: string[];
}

export interface WebsiteStructure {
  sections: string[];
  has_before_after: boolean;
  has_booking_form: boolean;
  has_pricing: boolean;
  has_blog: boolean;
  has_gallery: boolean;
  has_testimonials: boolean;
  has_faq: boolean;
  has_map: boolean;
}

export interface CopywritingData {
  h1_headline: string | null;
  h2_headlines: string[];
  cta_buttons: string[];
  value_propositions: string[];
  tone: string;
}

export interface CompetitorData {
  name: string;
  website_url: string | null;
  google_maps_link: string | null;
  rating: number;
  review_count: number;
  rank: number;
  design_tokens: DesignTokens;
  structure: WebsiteStructure;
  copywriting: CopywritingData;
  meta: Record<string, string>;
}

export interface CommonPatterns {
  dominant_colors: string[];
  common_sections: string[];
  common_cta_text: string[];
  messaging_themes: string[];
  recommended_structure: string[];
  summary_ro: string;
}

export interface MarketIntelligence {
  id: string;
  lead_id: string;
  niche: string;
  location: string;
  analysis_status: AnalysisStatus;
  competitors: CompetitorData[];
  common_patterns: CommonPatterns;
  strategy_summary: string | null;
  error_message: string | null;
  analyzed_at: string | null;
  created_at: string | null;
}

export interface ScrapeJob {
  id: string;
  location: string;
  niche: string;
  query: string;
  status: string;
  total_results: number;
  filtered_leads: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string | null;
}

export interface DashboardStats {
  total_leads: number;
  new_leads: number;
  analyzed_leads: number;
  total_analyses: number;
  leads_by_niche: Record<string, number>;
  leads_by_tier: Record<string, number>;
  avg_rating: number;
}

export interface NicheOption {
  value: NicheType;
  label: string;
}
