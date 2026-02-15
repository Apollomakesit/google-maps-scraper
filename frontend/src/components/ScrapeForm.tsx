"use client";

import { useState } from "react";
import { Zap, MapPin, Tag, Hash, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import type { NicheType, ScrapeJob } from "@/lib/types";
import { NICHE_LABELS } from "@/lib/types";
import { startScrape, getScrapeJob } from "@/lib/api";

const NICHE_OPTIONS: { value: NicheType; label: string }[] = Object.entries(NICHE_LABELS).map(
  ([value, label]) => ({ value: value as NicheType, label })
);

interface ScrapeFormProps {
  onJobComplete?: () => void;
}

export default function ScrapeForm({ onJobComplete }: ScrapeFormProps) {
  const [location, setLocation] = useState("București");
  const [niche, setNiche] = useState<NicheType>("dentist");
  const [maxResults, setMaxResults] = useState(100);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentJob, setCurrentJob] = useState<ScrapeJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function pollJobStatus(jobId: string) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const job = await getScrapeJob(jobId);
        setCurrentJob(job);

        if (job.status === "completed" || job.status === "failed") {
          setIsSubmitting(false);
          if (job.status === "completed" && onJobComplete) {
            onJobComplete();
          }
          if (job.status === "failed") {
            setError(job.error_message || "Job-ul de scraping a eșuat");
          }
          return;
        }
      } catch {
        // Continue polling
      }

      attempts++;
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }

    setIsSubmitting(false);
    setError("Timeout - job-ul durează prea mult");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    setCurrentJob(null);

    try {
      const job = await startScrape({
        location,
        niche,
        max_results: maxResults,
      });
      setCurrentJob(job);
      pollJobStatus(job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la pornirea scraping-ului");
      setIsSubmitting(false);
    }
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--accent)] to-purple-600 flex items-center justify-center">
          <Zap size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-[var(--foreground)]">
            Scraping Nou - Gap Finder
          </h2>
          <p className="text-xs text-[var(--muted)]">
            Găsește afaceri fără site web în zona selectată
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Location */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-[var(--foreground)] mb-2">
            <MapPin size={14} className="text-[var(--accent)]" />
            Locație
          </label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="ex: București, Cluj-Napoca, Timișoara"
            className="input-field"
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Niche */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-[var(--foreground)] mb-2">
            <Tag size={14} className="text-[var(--accent)]" />
            Nișă
          </label>
          <select
            value={niche}
            onChange={(e) => setNiche(e.target.value as NicheType)}
            className="select-field"
            disabled={isSubmitting}
          >
            {NICHE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Max Results */}
        <div>
          <label className="flex items-center gap-2 text-sm font-medium text-[var(--foreground)] mb-2">
            <Hash size={14} className="text-[var(--accent)]" />
            Rezultate Maxime
          </label>
          <input
            type="number"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            min={10}
            max={500}
            step={10}
            className="input-field"
            disabled={isSubmitting}
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="flex items-start gap-2 p-3 bg-[var(--danger)]/10 border border-[var(--danger)]/20 rounded-xl">
            <AlertCircle size={16} className="text-[var(--danger)] mt-0.5 flex-shrink-0" />
            <p className="text-sm text-[var(--danger)]">{error}</p>
          </div>
        )}

        {/* Job Status */}
        {currentJob && (
          <div className="p-4 glass-card-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-[var(--foreground)]">
                Status Job
              </span>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  currentJob.status === "completed"
                    ? "bg-[var(--success)]/15 text-[var(--success)]"
                    : currentJob.status === "failed"
                    ? "bg-[var(--danger)]/15 text-[var(--danger)]"
                    : "bg-[var(--warning)]/15 text-[var(--warning)]"
                }`}
              >
                {currentJob.status === "completed"
                  ? "Finalizat"
                  : currentJob.status === "failed"
                  ? "Eșuat"
                  : currentJob.status === "running"
                  ? "În curs..."
                  : "În așteptare"}
              </span>
            </div>

            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1.5">
                <CheckCircle2
                  size={14}
                  className={
                    currentJob.status === "completed"
                      ? "text-[var(--success)]"
                      : "text-[var(--warning)]"
                  }
                />
                <span className="text-[var(--muted)]">
                  {currentJob.total_results} rezultate scanate
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2
                  size={14}
                  className={
                    currentJob.status === "completed"
                      ? "text-[var(--accent)]"
                      : "text-[var(--warning)]"
                  }
                />
                <span className="text-[var(--muted)]">
                  {currentJob.filtered_leads} lead-uri fără website
                </span>
              </div>
            </div>

            {(currentJob.status === "running" || currentJob.status === "queued") && (
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-[var(--accent)] to-purple-500 rounded-full animate-pulse-glow w-1/2" />
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || !location.trim()}
          className="w-full btn-primary py-3 text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Se procesează...
            </>
          ) : (
            <>
              <Zap size={16} />
              Pornește Scraping-ul
            </>
          )}
        </button>
      </form>
    </div>
  );
}
