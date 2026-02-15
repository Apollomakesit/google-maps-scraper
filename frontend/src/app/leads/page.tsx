"use client";

import { useEffect, useState, useCallback } from "react";
import { Search } from "lucide-react";
import LeadTable from "@/components/LeadTable";
import LeadFilters from "@/components/LeadFilters";
import StrategyCard from "@/components/StrategyCard";
import { getLeads, startAnalysis, getIntelligenceForLead } from "@/lib/api";
import type {
  LeadListResponse,
  Lead,
  MarketIntelligence,
  NicheType,
  LeadStatus,
} from "@/lib/types";

export default function LeadsPage() {
  const [leadsData, setLeadsData] = useState<LeadListResponse | null>(null);
  const [selectedIntelligence, setSelectedIntelligence] = useState<MarketIntelligence | null>(null);
  const [leadsLoading, setLeadsLoading] = useState(true);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const [analyzingLeadId, setAnalyzingLeadId] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [niche, setNiche] = useState<NicheType | "">("");
  const [tier, setTier] = useState<number | null>(null);
  const [status, setStatus] = useState<LeadStatus | "">("");
  const [sortBy, setSortBy] = useState("review_count");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const hasFilters = !!(search || niche || tier || status);

  const loadLeads = useCallback(async () => {
    setLeadsLoading(true);
    try {
      const data = await getLeads({
        page,
        per_page: 25,
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

  function handleSort(field: string) {
    if (sortBy === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  }

  async function handleAnalyze(lead: Lead) {
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

    setAnalyzingLeadId(lead.id);
    setSelectedIntelligence(null);
    setIntelligenceLoading(true);

    try {
      const intel = await startAnalysis({ lead_id: lead.id, top_n: 3 });
      setSelectedIntelligence(intel);

      const pollInterval = setInterval(async () => {
        try {
          const updated = await getIntelligenceForLead(lead.id);
          if (updated) {
            setSelectedIntelligence(updated);
            if (updated.analysis_status === "completed" || updated.analysis_status === "failed") {
              clearInterval(pollInterval);
              setAnalyzingLeadId(null);
              setIntelligenceLoading(false);
              loadLeads();
            }
          }
        } catch {
          // Continue polling
        }
      }, 5000);

      setTimeout(() => {
        clearInterval(pollInterval);
        setAnalyzingLeadId(null);
        setIntelligenceLoading(false);
      }, 300000);
    } catch (err) {
      console.error("Failed to start analysis:", err);
      setAnalyzingLeadId(null);
      setIntelligenceLoading(false);
    }
  }

  function clearFilters() {
    setSearch("");
    setNiche("");
    setTier(null);
    setStatus("");
    setPage(1);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--foreground)] flex items-center gap-3">
          <Search size={28} className="text-[var(--accent)]" />
          Lead-uri
        </h1>
        <p className="text-sm text-[var(--muted)] mt-1">
          Afaceri fără site web descoperite prin Google Maps
        </p>
      </div>

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

      {(selectedIntelligence || intelligenceLoading) && (
        <StrategyCard
          intelligence={selectedIntelligence}
          loading={intelligenceLoading}
        />
      )}
    </div>
  );
}
