/**
 * API client for communicating with the FastAPI backend.
 *
 * All requests use relative URLs (e.g. "/api/leads/scrape").
 * The Next.js catch-all route handler at /api/[...path]/route.ts
 * proxies these to the FastAPI backend using the server-side
 * BACKEND_URL environment variable. This approach:
 * - Avoids CORS issues (same-origin requests from the browser)
 * - Uses runtime env vars (no build-time configuration needed)
 * - Works on Railway with internal networking
 */

import type {
  LeadListResponse,
  Lead,
  MarketIntelligence,
  ScrapeJob,
  DashboardStats,
  NicheType,
  LeadStatus,
  NicheOption,
} from "./types";

async function fetchJSON<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Always use relative URLs — the Next.js API proxy handles forwarding
  const url = path;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Eroare API: ${response.status} ${response.statusText}`
    );
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// ─────────────────────────────────────────────
// Leads API
// ─────────────────────────────────────────────

export async function getLeads(params: {
  page?: number;
  per_page?: number;
  niche?: NicheType;
  tier?: number;
  status?: LeadStatus;
  search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  city?: string;
}): Promise<LeadListResponse> {
  const searchParams = new URLSearchParams();

  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));
  if (params.niche) searchParams.set("niche", params.niche);
  if (params.tier) searchParams.set("tier", String(params.tier));
  if (params.status) searchParams.set("status", params.status);
  if (params.search) searchParams.set("search", params.search);
  if (params.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params.sort_order) searchParams.set("sort_order", params.sort_order);
  if (params.city) searchParams.set("city", params.city);

  return fetchJSON<LeadListResponse>(
    `/api/leads?${searchParams.toString()}`
  );
}

export async function getLead(leadId: string): Promise<Lead> {
  return fetchJSON<Lead>(`/api/leads/${leadId}`);
}

export async function updateLead(
  leadId: string,
  data: { status?: LeadStatus; notes?: string }
): Promise<Lead> {
  return fetchJSON<Lead>(`/api/leads/${leadId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteLead(
  leadId: string
): Promise<{ message: string; id: string }> {
  return fetchJSON<{ message: string; id: string }>(`/api/leads/${leadId}`, {
    method: "DELETE",
  });
}

export async function getStats(): Promise<DashboardStats> {
  return fetchJSON<DashboardStats>("/api/leads/stats");
}

export async function getNiches(): Promise<{ niches: NicheOption[] }> {
  return fetchJSON<{ niches: NicheOption[] }>("/api/leads/niches/list");
}

// ─────────────────────────────────────────────
// Scraping API
// ─────────────────────────────────────────────

export async function startScrape(data: {
  location: string;
  niche: NicheType;
  max_results?: number;
}): Promise<ScrapeJob> {
  return fetchJSON<ScrapeJob>("/api/leads/scrape", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getScrapeJob(jobId: string): Promise<ScrapeJob> {
  return fetchJSON<ScrapeJob>(`/api/leads/jobs/${jobId}`);
}

// ─────────────────────────────────────────────
// Intelligence API
// ─────────────────────────────────────────────

export async function startAnalysis(data: {
  lead_id: string;
  top_n?: number;
}): Promise<MarketIntelligence> {
  return fetchJSON<MarketIntelligence>("/api/intelligence/analyze", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getIntelligenceForLead(
  leadId: string
): Promise<MarketIntelligence | null> {
  try {
    return await fetchJSON<MarketIntelligence>(
      `/api/intelligence/lead/${leadId}`
    );
  } catch {
    return null;
  }
}

export async function getIntelligence(
  intelligenceId: string
): Promise<MarketIntelligence> {
  return fetchJSON<MarketIntelligence>(
    `/api/intelligence/${intelligenceId}`
  );
}

export async function deleteIntelligence(
  intelligenceId: string
): Promise<{ message: string; id: string }> {
  return fetchJSON<{ message: string; id: string }>(
    `/api/intelligence/${intelligenceId}`,
    { method: "DELETE" }
  );
}
