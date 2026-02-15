"use client";

import {
  Phone,
  Mail,
  MapPin,
  Star,
  ExternalLink,
  Brain,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Loader2,
} from "lucide-react";
import clsx from "clsx";
import type { Lead, LeadListResponse, NicheType, LeadStatus } from "@/lib/types";
import { NICHE_LABELS, STATUS_LABELS } from "@/lib/types";

interface LeadTableProps {
  data: LeadListResponse | null;
  loading: boolean;
  onPageChange: (page: number) => void;
  onAnalyze: (lead: Lead) => void;
  onSort: (field: string) => void;
  sortBy: string;
  sortOrder: "asc" | "desc";
  analyzingLeadId: string | null;
}

function TierBadge({ tier }: { tier: number }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold",
        tier === 1 && "tier-1",
        tier === 2 && "tier-2",
        tier === 3 && "tier-3"
      )}
    >
      T{tier}
    </span>
  );
}

function StatusBadge({ status }: { status: LeadStatus }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        `status-${status}`
      )}
    >
      {STATUS_LABELS[status] || status}
    </span>
  );
}

function SortHeader({
  label,
  field,
  currentSort,
  sortOrder,
  onSort,
}: {
  label: string;
  field: string;
  currentSort: string;
  sortOrder: "asc" | "desc";
  onSort: (field: string) => void;
}) {
  const isActive = currentSort === field;
  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 text-xs font-semibold text-[var(--muted)] uppercase tracking-wider hover:text-[var(--foreground)] transition-colors"
    >
      {label}
      <ArrowUpDown
        size={12}
        className={clsx(
          isActive ? "text-[var(--accent)]" : "text-[var(--muted)]/50"
        )}
      />
    </button>
  );
}

export default function LeadTable({
  data,
  loading,
  onPageChange,
  onAnalyze,
  onSort,
  sortBy,
  sortOrder,
  analyzingLeadId,
}: LeadTableProps) {
  if (loading) {
    return (
      <div className="glass-card overflow-hidden">
        <div className="p-6 space-y-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 animate-pulse">
              <div className="h-4 w-8 bg-white/10 rounded" />
              <div className="h-4 w-40 bg-white/10 rounded" />
              <div className="h-4 w-24 bg-white/10 rounded" />
              <div className="h-4 w-20 bg-white/10 rounded" />
              <div className="h-4 w-16 bg-white/10 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.leads.length === 0) {
    return (
      <div className="glass-card p-12 text-center">
        <div className="text-[var(--muted)] text-lg mb-2">
          Nu au fost găsite lead-uri
        </div>
        <p className="text-[var(--muted)]/70 text-sm">
          Pornește o sesiune de scraping pentru a genera lead-uri noi.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--card-border)]">
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                  Tier
                </span>
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader label="Nume" field="name" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                  Nișă
                </span>
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                  Contact
                </span>
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader label="Recenzii" field="review_count" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader label="Rating" field="review_rating" currentSort={sortBy} sortOrder={sortOrder} onSort={onSort} />
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                  Status
                </span>
              </th>
              <th className="px-4 py-3 text-right">
                <span className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider">
                  Acțiuni
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {data.leads.map((lead) => (
              <tr key={lead.id} className="border-b border-[var(--card-border)]/50 table-row-hover">
                {/* Tier */}
                <td className="px-4 py-3">
                  <TierBadge tier={lead.tier} />
                </td>

                {/* Name + Address */}
                <td className="px-4 py-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-[var(--foreground)] line-clamp-1">
                      {lead.name}
                    </span>
                    {lead.address && (
                      <span className="text-xs text-[var(--muted)] flex items-center gap-1 mt-0.5 line-clamp-1">
                        <MapPin size={10} />
                        {lead.address}
                      </span>
                    )}
                  </div>
                </td>

                {/* Niche */}
                <td className="px-4 py-3">
                  <span className="text-xs text-[var(--muted)] bg-white/5 px-2 py-1 rounded-md">
                    {NICHE_LABELS[lead.niche as NicheType] || lead.niche}
                  </span>
                </td>

                {/* Contact */}
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-0.5">
                    {lead.phone && (
                      <a
                        href={`tel:${lead.phone}`}
                        className="text-xs text-[var(--accent)] hover:text-[var(--accent-hover)] flex items-center gap-1 transition-colors"
                      >
                        <Phone size={10} />
                        {lead.phone}
                      </a>
                    )}
                    {lead.emails.length > 0 && (
                      <a
                        href={`mailto:${lead.emails[0]}`}
                        className="text-xs text-[var(--accent)] hover:text-[var(--accent-hover)] flex items-center gap-1 transition-colors"
                      >
                        <Mail size={10} />
                        {lead.emails[0]}
                      </a>
                    )}
                  </div>
                </td>

                {/* Reviews */}
                <td className="px-4 py-3">
                  <span className="text-sm font-medium text-[var(--foreground)]">
                    {lead.review_count}
                  </span>
                </td>

                {/* Rating */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <Star size={12} className="text-yellow-400 fill-yellow-400" />
                    <span className="text-sm font-medium text-[var(--foreground)]">
                      {lead.review_rating.toFixed(1)}
                    </span>
                  </div>
                </td>

                {/* Status */}
                <td className="px-4 py-3">
                  <StatusBadge status={lead.status} />
                </td>

                {/* Actions */}
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    {lead.google_maps_link && (
                      <a
                        href={lead.google_maps_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5 transition-all"
                        title="Deschide în Google Maps"
                      >
                        <ExternalLink size={14} />
                      </a>
                    )}
                    <button
                      onClick={() => onAnalyze(lead)}
                      disabled={analyzingLeadId === lead.id || lead.status === "analyzing"}
                      className={clsx(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                        lead.status === "analyzed"
                          ? "bg-[var(--success)]/15 text-[var(--success)] hover:bg-[var(--success)]/25"
                          : analyzingLeadId === lead.id || lead.status === "analyzing"
                          ? "bg-[var(--warning)]/15 text-[var(--warning)] cursor-wait"
                          : "btn-primary text-xs"
                      )}
                    >
                      {analyzingLeadId === lead.id || lead.status === "analyzing" ? (
                        <>
                          <Loader2 size={12} className="animate-spin" />
                          Analizare...
                        </>
                      ) : lead.status === "analyzed" ? (
                        <>
                          <Brain size={12} />
                          Vezi Analiza
                        </>
                      ) : (
                        <>
                          <Brain size={12} />
                          Analizează
                        </>
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data.total_pages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--card-border)]">
          <span className="text-xs text-[var(--muted)]">
            Pagina {data.page} din {data.total_pages} ({data.total} lead-uri total)
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(data.page - 1)}
              disabled={data.page <= 1}
              className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: Math.min(data.total_pages, 5) }).map((_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  onClick={() => onPageChange(pageNum)}
                  className={clsx(
                    "w-8 h-8 rounded-lg text-xs font-medium transition-all",
                    data.page === pageNum
                      ? "bg-[var(--accent)] text-white"
                      : "text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5"
                  )}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              onClick={() => onPageChange(data.page + 1)}
              disabled={data.page >= data.total_pages}
              className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
