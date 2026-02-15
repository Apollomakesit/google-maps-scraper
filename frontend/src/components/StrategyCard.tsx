"use client";

import {
  Palette,
  Layout,
  Type,
  MousePointerClick,
  Globe,
  Star,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertTriangle,
  ArrowRight,
  Lightbulb,
} from "lucide-react";
import clsx from "clsx";
import type { MarketIntelligence, CompetitorData } from "@/lib/types";

interface StrategyCardProps {
  intelligence: MarketIntelligence | null;
  loading: boolean;
}

function SectionLabel({ label, icon: Icon }: { label: string; icon: React.ComponentType<{ size?: number; className?: string }> }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <Icon size={16} className="text-[var(--accent)]" />
      <h4 className="text-sm font-semibold text-[var(--foreground)] uppercase tracking-wider">
        {label}
      </h4>
    </div>
  );
}

function CompetitorCard({ competitor }: { competitor: CompetitorData }) {
  const dt = competitor.design_tokens;
  const st = competitor.structure;
  const cw = competitor.copywriting;

  return (
    <div className="glass-card-sm p-4 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-0.5 rounded-full">
              #{competitor.rank}
            </span>
            <h5 className="text-sm font-semibold text-[var(--foreground)]">
              {competitor.name}
            </h5>
          </div>
          {competitor.website_url && (
            <a
              href={competitor.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-[var(--accent)] hover:text-[var(--accent-hover)] flex items-center gap-1 mt-1 transition-colors"
            >
              <Globe size={10} />
              {new URL(competitor.website_url).hostname}
            </a>
          )}
        </div>
        <div className="flex items-center gap-1 text-sm">
          <Star size={12} className="text-yellow-400 fill-yellow-400" />
          <span className="font-medium text-[var(--foreground)]">{competitor.rating.toFixed(1)}</span>
          <span className="text-[var(--muted)] text-xs">({competitor.review_count})</span>
        </div>
      </div>

      {/* Color Palette */}
      {dt.color_palette.length > 0 && (
        <div>
          <SectionLabel label="Paletă Culori" icon={Palette} />
          <div className="flex items-center gap-2 flex-wrap">
            {dt.color_palette.map((color, i) => (
              <div key={`${color}-${i}`} className="flex items-center gap-1.5">
                <div
                  className="color-swatch"
                  style={{ backgroundColor: color }}
                  title={color}
                />
                <span className="text-xs font-mono text-[var(--muted)]">{color}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Structure */}
      <div>
        <SectionLabel label="Structură Site" icon={Layout} />
        <div className="flex flex-wrap gap-1.5">
          {st.sections.map((section) => (
            <span
              key={section}
              className="text-xs bg-[var(--accent)]/10 text-[var(--accent-hover)] px-2 py-0.5 rounded-md font-medium"
            >
              {section}
            </span>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2">
          {[
            { label: "Galerie Before/After", value: st.has_before_after },
            { label: "Formular Programare", value: st.has_booking_form },
            { label: "Prețuri", value: st.has_pricing },
            { label: "Blog", value: st.has_blog },
            { label: "Galerie", value: st.has_gallery },
            { label: "Testimoniale", value: st.has_testimonials },
            { label: "FAQ", value: st.has_faq },
            { label: "Hartă", value: st.has_map },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center gap-1.5 text-xs">
              {value ? (
                <CheckCircle2 size={12} className="text-[var(--success)]" />
              ) : (
                <XCircle size={12} className="text-[var(--muted)]/40" />
              )}
              <span className={value ? "text-[var(--foreground)]" : "text-[var(--muted)]/60"}>
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Copywriting */}
      {(cw.h1_headline || cw.cta_buttons.length > 0) && (
        <div>
          <SectionLabel label="Copywriting" icon={Type} />
          {cw.h1_headline && (
            <div className="mb-2">
              <span className="text-xs text-[var(--muted)] block mb-0.5">Titlu H1:</span>
              <span className="text-sm text-[var(--foreground)] font-medium italic">
                &ldquo;{cw.h1_headline}&rdquo;
              </span>
            </div>
          )}
          {cw.cta_buttons.length > 0 && (
            <div>
              <span className="text-xs text-[var(--muted)] block mb-1">Butoane CTA:</span>
              <div className="flex flex-wrap gap-1.5">
                {cw.cta_buttons.map((cta, i) => (
                  <span
                    key={`${cta}-${i}`}
                    className="text-xs bg-[var(--success)]/10 text-[var(--success)] px-2 py-0.5 rounded-md font-medium flex items-center gap-1"
                  >
                    <MousePointerClick size={10} />
                    {cta}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function StrategyCard({ intelligence, loading }: StrategyCardProps) {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <Loader2 size={20} className="text-[var(--accent)] animate-spin" />
          <span className="text-sm text-[var(--muted)]">Se analizează competitorii...</span>
        </div>
        <div className="space-y-4 animate-pulse">
          <div className="h-4 w-3/4 bg-white/10 rounded" />
          <div className="h-4 w-1/2 bg-white/10 rounded" />
          <div className="h-20 bg-white/10 rounded-lg" />
        </div>
      </div>
    );
  }

  if (!intelligence) {
    return null;
  }

  if (intelligence.analysis_status === "failed") {
    return (
      <div className="glass-card p-6 border-[var(--danger)]/30">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle size={20} className="text-[var(--danger)]" />
          <h3 className="text-lg font-semibold text-[var(--danger)]">Analiză Eșuată</h3>
        </div>
        <p className="text-sm text-[var(--muted)]">
          {intelligence.error_message || "O eroare necunoscută a apărut în timpul analizei."}
        </p>
      </div>
    );
  }

  if (intelligence.analysis_status === "pending" || intelligence.analysis_status === "in_progress") {
    return (
      <div className="glass-card p-6 glow-accent">
        <div className="flex items-center gap-3 mb-2">
          <Loader2 size={20} className="text-[var(--accent)] animate-spin" />
          <h3 className="text-lg font-semibold text-[var(--foreground)]">
            Analiza este în curs...
          </h3>
        </div>
        <p className="text-sm text-[var(--muted)]">
          Se caută competitorii de top și se extrage &quot;Formula Câștigătoare&quot;.
          Acest proces poate dura 1-3 minute.
        </p>
        <div className="mt-4 h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-[var(--accent)] to-purple-500 rounded-full animate-pulse-glow w-2/3" />
        </div>
      </div>
    );
  }

  const { competitors, common_patterns } = intelligence;
  const cp = common_patterns;

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="glass-card p-6 glow-accent">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--accent)] to-purple-600 flex items-center justify-center">
            <Lightbulb size={20} className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--foreground)]">
              Formula Câștigătoare
            </h3>
            <p className="text-xs text-[var(--muted)]">
              Bazat pe analiza a {competitors.length} competitori de top
            </p>
          </div>
        </div>

        {/* Summary text */}
        {cp.summary_ro && (
          <div className="bg-[var(--accent)]/5 border border-[var(--accent)]/20 rounded-xl p-4 mb-4">
            <p className="text-sm text-[var(--foreground)] leading-relaxed">
              {cp.summary_ro}
            </p>
          </div>
        )}

        {/* Pattern Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Dominant Colors */}
          {cp.dominant_colors.length > 0 && (
            <div className="glass-card-sm p-4">
              <SectionLabel label="Culori Dominante" icon={Palette} />
              <div className="flex items-center gap-3 flex-wrap">
                {cp.dominant_colors.map((color, i) => (
                  <div key={`${color}-${i}`} className="flex items-center gap-1.5">
                    <div
                      className="color-swatch"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                    <span className="text-xs font-mono text-[var(--muted)]">{color}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Structure */}
          {cp.recommended_structure.length > 0 && (
            <div className="glass-card-sm p-4">
              <SectionLabel label="Structură Recomandată" icon={Layout} />
              <div className="space-y-1.5">
                {cp.recommended_structure.map((section, i) => (
                  <div key={section} className="flex items-center gap-2 text-sm">
                    <span className="text-xs text-[var(--accent)] font-mono w-4">{i + 1}.</span>
                    <span className="text-[var(--foreground)] capitalize">{section}</span>
                    {i < cp.recommended_structure.length - 1 && (
                      <ArrowRight size={10} className="text-[var(--muted)]/40" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Common CTAs */}
          {cp.common_cta_text.length > 0 && (
            <div className="glass-card-sm p-4">
              <SectionLabel label="Texte CTA Frecvente" icon={MousePointerClick} />
              <div className="flex flex-wrap gap-2">
                {cp.common_cta_text.map((cta, i) => (
                  <span
                    key={`${cta}-${i}`}
                    className="text-xs bg-[var(--success)]/10 text-[var(--success)] px-3 py-1 rounded-lg font-medium"
                  >
                    &ldquo;{cta}&rdquo;
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Messaging Themes */}
          {cp.messaging_themes.length > 0 && (
            <div className="glass-card-sm p-4">
              <SectionLabel label="Teme de Mesagerie" icon={Type} />
              <div className="flex flex-wrap gap-2">
                {cp.messaging_themes.map((theme, i) => (
                  <span
                    key={`${theme}-${i}`}
                    className="text-xs bg-purple-500/10 text-purple-400 px-3 py-1 rounded-lg font-medium"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Individual Competitor Cards */}
      {competitors.length > 0 && (
        <div>
          <h3 className="text-base font-semibold text-[var(--foreground)] mb-4 flex items-center gap-2">
            <Globe size={18} className="text-[var(--accent)]" />
            Analiza Detaliată a Competitorilor
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {competitors.map((comp) => (
              <CompetitorCard key={`${comp.name}-${comp.rank}`} competitor={comp} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
