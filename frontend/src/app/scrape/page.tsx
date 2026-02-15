"use client";

import { useRouter } from "next/navigation";
import { Zap, ArrowLeft } from "lucide-react";
import Link from "next/link";
import ScrapeForm from "@/components/ScrapeForm";

export default function ScrapePage() {
  const router = useRouter();

  function handleJobComplete() {
    // Navigate to leads page after job completes
    setTimeout(() => {
      router.push("/leads");
    }, 2000);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--foreground)] flex items-center gap-3">
            <Zap size={28} className="text-[var(--accent)]" />
            Scraping Nou
          </h1>
          <p className="text-sm text-[var(--muted)] mt-1">
            Lansează o sesiune nouă de descoperire lead-uri
          </p>
        </div>
        <Link
          href="/leads"
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <ArrowLeft size={14} />
          Înapoi la Lead-uri
        </Link>
      </div>

      <div className="max-w-xl">
        <ScrapeForm onJobComplete={handleJobComplete} />
      </div>

      {/* Instructions */}
      <div className="glass-card p-6 max-w-xl">
        <h3 className="text-sm font-semibold text-[var(--foreground)] mb-3">
          Cum funcționează?
        </h3>
        <ol className="space-y-3 text-sm text-[var(--muted)]">
          <li className="flex items-start gap-3">
            <span className="text-xs font-bold text-[var(--accent)] bg-[var(--accent)]/10 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              1
            </span>
            <span>
              <strong className="text-[var(--foreground)]">Selectează locația și nișa</strong> - Alege orașul și tipul de afacere pe care vrei să le cauți.
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-xs font-bold text-[var(--accent)] bg-[var(--accent)]/10 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              2
            </span>
            <span>
              <strong className="text-[var(--foreground)]">Scraping automat</strong> - Sistemul caută pe Google Maps afaceri care nu au site web sau al căror site returnează eroare 404.
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-xs font-bold text-[var(--accent)] bg-[var(--accent)]/10 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              3
            </span>
            <span>
              <strong className="text-[var(--foreground)]">Filtrare inteligentă</strong> - Se păstrează doar afacerile cu recenzii și informații de contact (telefon sau email).
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="text-xs font-bold text-[var(--accent)] bg-[var(--accent)]/10 w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              4
            </span>
            <span>
              <strong className="text-[var(--foreground)]">Clasificare pe nivele</strong> - Lead-urile sunt clasificate automat: Tier 1 (urgență), Tier 2 (vizual), Tier 3 (altele).
            </span>
          </li>
        </ol>
      </div>
    </div>
  );
}
