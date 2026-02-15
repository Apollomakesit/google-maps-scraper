"use client";

import { Search, Zap, BarChart3, Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import clsx from "clsx";

const navItems = [
  { href: "/", label: "Panou Principal", icon: BarChart3 },
  { href: "/leads", label: "Lead-uri", icon: Search },
  { href: "/scrape", label: "Scraping Nou", icon: Zap },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="glass-card sticky top-0 z-50 border-b border-[var(--card-border)] rounded-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[var(--accent)] to-purple-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Zap size={20} className="text-white" />
            </div>
            <div>
              <span className="text-lg font-bold text-[var(--foreground)]">LeadGen</span>
              <span className="text-lg font-light text-[var(--accent)] ml-1">Intelligence</span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                    isActive
                      ? "bg-[var(--accent)]/15 text-[var(--accent-hover)]"
                      : "text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5"
                  )}
                >
                  <Icon size={16} />
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 rounded-lg text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Meniu"
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile Nav */}
        {mobileOpen && (
          <div className="md:hidden pb-4 pt-2 border-t border-[var(--card-border)]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={clsx(
                    "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                    isActive
                      ? "bg-[var(--accent)]/15 text-[var(--accent-hover)]"
                      : "text-[var(--muted)] hover:text-[var(--foreground)] hover:bg-white/5"
                  )}
                >
                  <Icon size={18} />
                  {item.label}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}
