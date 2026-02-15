"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Phone,
  Mail,
  MapPin,
  Star,
  ExternalLink,
  Brain,
  Loader2,
  Clock,
  Globe,
  Tag,
} from "lucide-react";
import Link from "next/link";
import clsx from "clsx";
import StrategyCard from "@/components/StrategyCard";
import { getLead, startAnalysis, getIntelligenceForLead, updateLead } from "@/lib/api";
import type { Lead, MarketIntelligence, LeadStatus } from "@/lib/types";
import { NICHE_LABELS, STATUS_LABELS } from "@/lib/types";

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params.id as string;

  const [lead, setLead] = useState<Lead | null>(null);
  const [intelligence, setIntelligence] = useState<MarketIntelligence | null>(null);
  const [loading, setLoading] = useState(true);
  const [intelligenceLoading, setIntelligenceLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [leadData, intelData] = await Promise.all([
          getLead(leadId),
          getIntelligenceForLead(leadId),
        ]);
        setLead(leadData);
        setIntelligence(intelData);
      } catch (err) {
        console.error("Failed to load lead:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [leadId]);

  async function handleAnalyze() {
    if (!lead) return;
    setAnalyzing(true);
    setIntelligenceLoading(true);

    try {
      const intel = await startAnalysis({ lead_id: lead.id, top_n: 3 });
      setIntelligence(intel);

      const pollInterval = setInterval(async () => {
        try {
          const updated = await getIntelligenceForLead(lead.id);
          if (updated) {
            setIntelligence(updated);
            if (updated.analysis_status === "completed" || updated.analysis_status === "failed") {
              clearInterval(pollInterval);
              setAnalyzing(false);
              setIntelligenceLoading(false);
              const refreshedLead = await getLead(lead.id);
              setLead(refreshedLead);
            }
          }
        } catch {
          // Continue
        }
      }, 5000);

      setTimeout(() => {
        clearInterval(pollInterval);
        setAnalyzing(false);
        setIntelligenceLoading(false);
      }, 300000);
    } catch (err) {
      console.error("Failed to start analysis:", err);
      setAnalyzing(false);
      setIntelligenceLoading(false);
    }
  }

  async function handleStatusChange(newStatus: LeadStatus) {
    if (!lead) return;
    try {
      const updated = await updateLead(lead.id, { status: newStatus });
      setLead(updated);
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-white/10 rounded animate-pulse" />
        <div className="glass-card p-6 animate-pulse space-y-4">
          <div className="h-6 w-64 bg-white/10 rounded" />
          <div className="h-4 w-96 bg-white/10 rounded" />
          <div className="h-4 w-48 bg-white/10 rounded" />
        </div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="glass-card p-12 text-center">
        <p className="text-[var(--muted)] text-lg">Lead-ul nu a fost găsit.</p>
        <Link href="/leads" className="btn-primary inline-flex items-center gap-2 mt-4">
          <ArrowLeft size={14} />
          Înapoi la Lead-uri
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <Link
        href="/leads"
        className="inline-flex items-center gap-2 text-sm text-[var(--muted)] hover:text-[var(--foreground)] transition-colors"
      >
        <ArrowLeft size={14} />
        Înapoi la Lead-uri
      </Link>

      {/* Lead Info Card */}
      <div className="glass-card p-6">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span
                className={clsx(
                  "px-2.5 py-0.5 rounded-full text-xs font-bold",
                  lead.tier === 1 && "tier-1",
                  lead.tier === 2 && "tier-2",
                  lead.tier === 3 && "tier-3"
                )}
              >
                Tier {lead.tier}
              </span>
              <span className={`status-${lead.status} px-2.5 py-0.5 rounded-full text-xs font-medium`}>
                {STATUS_LABELS[lead.status]}
              </span>
            </div>

            <h1 className="text-2xl font-bold text-[var(--foreground)] mb-2">
              {lead.name}
            </h1>

            <div className="flex items-center gap-4 flex-wrap text-sm text-[var(--muted)]">
              {lead.address && (
                <span className="flex items-center gap-1.5">
                  <MapPin size={14} className="text-[var(--accent)]" />
                  {lead.address}
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <Tag size={14} className="text-[var(--accent)]" />
                {NICHE_LABELS[lead.niche] || lead.niche}
              </span>
            </div>

            {/* Contact info */}
            <div className="flex items-center gap-4 mt-4 flex-wrap">
              {lead.phone && (
                <a
                  href={`tel:${lead.phone}`}
                  className="flex items-center gap-2 text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  <Phone size={14} />
                  {lead.phone}
                </a>
              )}
              {lead.emails.map((email) => (
                <a
                  key={email}
                  href={`mailto:${email}`}
                  className="flex items-center gap-2 text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  <Mail size={14} />
                  {email}
                </a>
              ))}
              {lead.google_maps_link && (
                <a
                  href={lead.google_maps_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
                >
                  <ExternalLink size={14} />
                  Google Maps
                </a>
              )}
            </div>

            {/* Metrics */}
            <div className="flex items-center gap-6 mt-4">
              <div className="flex items-center gap-1.5">
                <Star size={16} className="text-yellow-400 fill-yellow-400" />
                <span className="text-lg font-bold text-[var(--foreground)]">
                  {lead.review_rating.toFixed(1)}
                </span>
                <span className="text-sm text-[var(--muted)]">
                  ({lead.review_count} recenzii)
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-sm text-[var(--muted)]">
                <Globe size={14} />
                <span>
                  Site web: <strong className="text-[var(--danger)]">{lead.website_status === "missing" ? "Lipsă" : lead.website_status}</strong>
                </span>
              </div>
              {lead.created_at && (
                <div className="flex items-center gap-1.5 text-sm text-[var(--muted)]">
                  <Clock size={14} />
                  {new Date(lead.created_at).toLocaleDateString("ro-RO")}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-2 lg:items-end">
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="btn-primary flex items-center gap-2"
            >
              {analyzing ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Se analizează...
                </>
              ) : intelligence?.analysis_status === "completed" ? (
                <>
                  <Brain size={16} />
                  Re-analizează Competitorii
                </>
              ) : (
                <>
                  <Brain size={16} />
                  Analizează Competitorii
                </>
              )}
            </button>

            {/* Status dropdown */}
            <select
              value={lead.status}
              onChange={(e) => handleStatusChange(e.target.value as LeadStatus)}
              className="select-field text-sm w-auto"
            >
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Strategy Card */}
      {(intelligence || intelligenceLoading) && (
        <StrategyCard
          intelligence={intelligence}
          loading={intelligenceLoading}
        />
      )}
    </div>
  );
}
