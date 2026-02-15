"use client";

import { useEffect, useState, useCallback } from "react";
import { BarChart3, TrendingUp, Users } from "lucide-react";
import StatCards from "@/components/StatCards";
import LeadTable from "@/components/LeadTable";
import LeadFilters from "@/components/LeadFilters";
import StrategyCard from "@/components/StrategyCard";
import { getLeads, getStats, startAnalysis, getIntelligenceForLead } from "@/lib/api";
import type {
  LeadListResponse,
  DashboardStats,
  Lead,
  MarketIntelligence,
  NicheType,
  LeadStatus,
} from "@/lib/types";

export default function DashboardPage() {
  // Data state
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [leadsData, setLeadsData] = useState<LeadListResponse | null>(null);
  const [selectedIntelligence, setSelectedIntelligence] = useState<MarketIntelligence | null>(null);

  // Loading state
  const [statsLoading, setStatsLoading] = useState(true);
  const [leadsLoading, setLeadsLoading] = useState(true);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const [analyzingLeadId, setAnalyzingLeadId] = useState<string | null>(null);

  // Filter state
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [niche, setNiche] = useState<NicheType | "">("");
  const [tier, setTier] = useState<number | null>(null);
  const [status, setStatus] = useState<LeadStatus | "">("");
  const [sortBy, setSortBy] = useState("review_count");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const hasFilters = !!(search || niche || tier || status);

  // Load stats
  useEffect(() => {
    async function loadStats() {
      try {
        const data = await getStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to load stats:", err);
      } finally {
        setStatsLoading(false);
      }
    }
    loadStats();
  }, []);

  // Load leads
  const loadLeads = useCallback(async () => {
    setLeadsLoading(true);
    try {
      const data = await getLeads({
        page,
        per_page: 15,
        niche: niche || undefined,
        tier: tier || undefined,
        status: status || undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setLeadsData(data);
    } catch (err) {
      console.error("Failed to load leads:", err);
    } finally {
      setLeadsLoading(false);
    }
  }, [page, niche, tier, status, search, sortBy, sortOrder]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  // Handle sorting
  function handleSort(field: string) {
    if (sortBy === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  }

  // Handle analyze
  async function handleAnalyze(lead: Lead) {
    // If already analyzed, show the intelligence
    if (lead.status === "analyzed") {
      setIntelligenceLoading(true);
      setSelectedIntelligence(null);
      try {
        const intel = await getIntelligenceForLead(lead.id);
        setSelectedIntelligence(intel);
      } catch (err) {
        console.error("Failed to load intelligence:", err);
      } finally {
        setIntelligenceLoading(false);
      }
      return;
    }

    // Start new analysis
    setAnalyzingLeadId(lead.id);
    setSelectedIntelligence(null);
    setIntelligenceLoading(true);

    try {
      const intel = await startAnalysis({ lead_id: lead.id, top_n: 3 });
      setSelectedIntelligence(intel);

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const updated = await getIntelligenceForLead(lead.id);
          if (updated) {
            setSelectedIntelligence(updated);
            if (updated.analysis_status === "completed" || updated.analysis_status === "failed") {
              clearInterval(pollInterval);
              setAnalyzingLeadId(null);
              setIntelligenceLoading(false);
              loadLeads(); // Refresh leads table
            }
          }
        } catch {
          // Continue polling
        }
      }, 5000);

      // Safety timeout
      setTimeout(() => {
        clearInterval(pollInterval);
        setAnalyzingLeadId(null);
        setIntelligenceLoading(false);
      }, 300000); // 5 minutes
    } catch (err) {
      console.error("Failed to start analysis:", err);
      setAnalyzingLeadId(null);
      setIntelligenceLoading(false);
    }
  }

  // Clear filters
  function clearFilters() {
    setSearch("");
    setNiche("");
    setTier(null);
    setStatus("");
    setPage(1);
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--foreground)] flex items-center gap-3">
            <BarChart3 size={28} className="text-[var(--accent)]" />
            Panou Principal
          </h1>
          <p className="text-sm text-[var(--muted)] mt-1">
            Generare lead-uri și analiză competitivă pentru afaceri fără site web
          </p>
        </div>
      </div>

      {/* Stats */}
      <StatCards stats={stats} loading={statsLoading} />

      {/* Niche Distribution */}
      {stats && Object.keys(stats.leads_by_niche).length > 0 && (
        <div className="glass-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-[var(--accent)]" />
            <h3 className="text-sm font-semibold text-[var(--foreground)]">
              Distribuție pe Nișe
            </h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.leads_by_niche)
              .sort((a, b) => b[1] - a[1])
              .map(([nicheLabel, count]) => (
                <div
                  key={nicheLabel}
                  className="flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg"
                >
                  <Users size={12} className="text-[var(--accent)]" />
                  <span className="text-xs font-medium text-[var(--foreground)]">
                    {nicheLabel}
                  </span>
                  <span className="text-xs text-[var(--accent)] font-bold bg-[var(--accent)]/10 px-1.5 py-0.5 rounded">
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <LeadFilters
        search={search}
        niche={niche}
        tier={tier}
        status={status}
        onSearchChange={(val) => { setSearch(val); setPage(1); }}
        onNicheChange={(val) => { setNiche(val); setPage(1); }}
        onTierChange={(val) => { setTier(val); setPage(1); }}
        onStatusChange={(val) => { setStatus(val); setPage(1); }}
        onClear={clearFilters}
        hasFilters={hasFilters}
      />

      {/* Lead Table */}
      <LeadTable
        data={leadsData}
        loading={leadsLoading}
        onPageChange={setPage}
        onAnalyze={handleAnalyze}
        onSort={handleSort}
        sortBy={sortBy}
        sortOrder={sortOrder}
        analyzingLeadId={analyzingLeadId}
      />

      {/* Strategy Card (shown when analysis is selected) */}
      {(selectedIntelligence || intelligenceLoading) && (
        <div id="strategy-section">
          <StrategyCard
            intelligence={selectedIntelligence}
            loading={intelligenceLoading}
          />
        </div>
      )}
    </div>
  );
}
