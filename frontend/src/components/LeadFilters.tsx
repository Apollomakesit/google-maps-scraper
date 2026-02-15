"use client";

import { Search, Filter, X } from "lucide-react";
import type { NicheType, LeadStatus } from "@/lib/types";
import { NICHE_LABELS, STATUS_LABELS } from "@/lib/types";

interface LeadFiltersProps {
  search: string;
  niche: NicheType | "";
  tier: number | null;
  status: LeadStatus | "";
  onSearchChange: (value: string) => void;
  onNicheChange: (value: NicheType | "") => void;
  onTierChange: (value: number | null) => void;
  onStatusChange: (value: LeadStatus | "") => void;
  onClear: () => void;
  hasFilters: boolean;
}

export default function LeadFilters({
  search,
  niche,
  tier,
  status,
  onSearchChange,
  onNicheChange,
  onTierChange,
  onStatusChange,
  onClear,
  hasFilters,
}: LeadFiltersProps) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Filter size={16} className="text-[var(--accent)]" />
        <h3 className="text-sm font-semibold text-[var(--foreground)]">
          Filtre
        </h3>
        {hasFilters && (
          <button
            onClick={onClear}
            className="ml-auto flex items-center gap-1 text-xs text-[var(--danger)] hover:text-red-400 transition-colors"
          >
            <X size={12} />
            Resetează
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Search */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Caută lead-uri..."
            className="input-field pl-9 text-sm"
          />
        </div>

        {/* Niche */}
        <select
          value={niche}
          onChange={(e) => onNicheChange(e.target.value as NicheType | "")}
          className="select-field text-sm"
        >
          <option value="">Toate nișele</option>
          {Object.entries(NICHE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>

        {/* Tier */}
        <select
          value={tier ?? ""}
          onChange={(e) => onTierChange(e.target.value ? Number(e.target.value) : null)}
          className="select-field text-sm"
        >
          <option value="">Toate nivelurile</option>
          <option value="1">Tier 1 - Urgență & High Value</option>
          <option value="2">Tier 2 - Vizual & Programări</option>
          <option value="3">Tier 3 - Alte categorii</option>
        </select>

        {/* Status */}
        <select
          value={status}
          onChange={(e) => onStatusChange(e.target.value as LeadStatus | "")}
          className="select-field text-sm"
        >
          <option value="">Toate statusurile</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
