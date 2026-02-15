"use client";

import { Users, UserPlus, BarChart3, Brain, Star, TrendingUp } from "lucide-react";
import type { DashboardStats } from "@/lib/types";

interface StatCardsProps {
  stats: DashboardStats | null;
  loading: boolean;
}

export default function StatCards({ stats, loading }: StatCardsProps) {
  const cards = [
    {
      label: "Total Lead-uri",
      value: stats?.total_leads ?? 0,
      icon: Users,
      color: "from-indigo-500 to-purple-600",
      glow: "glow-accent",
    },
    {
      label: "Lead-uri Noi",
      value: stats?.new_leads ?? 0,
      icon: UserPlus,
      color: "from-emerald-500 to-teal-600",
      glow: "glow-success",
    },
    {
      label: "Analizate",
      value: stats?.analyzed_leads ?? 0,
      icon: Brain,
      color: "from-amber-500 to-orange-600",
      glow: "glow-warning",
    },
    {
      label: "Analize Complete",
      value: stats?.total_analyses ?? 0,
      icon: BarChart3,
      color: "from-cyan-500 to-blue-600",
      glow: "glow-accent",
    },
    {
      label: "Rating Mediu",
      value: stats?.avg_rating ? `${stats.avg_rating}★` : "0★",
      icon: Star,
      color: "from-yellow-500 to-amber-600",
      glow: "glow-warning",
    },
    {
      label: "Nișe Active",
      value: stats?.leads_by_niche ? Object.keys(stats.leads_by_niche).length : 0,
      icon: TrendingUp,
      color: "from-pink-500 to-rose-600",
      glow: "glow-accent",
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass-card p-5 animate-pulse">
            <div className="h-4 w-20 bg-white/10 rounded mb-3" />
            <div className="h-8 w-16 bg-white/10 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.label} className={`glass-card p-5 ${card.glow} transition-transform hover:scale-[1.02]`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-[var(--muted)] uppercase tracking-wider">
                {card.label}
              </span>
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <Icon size={16} className="text-white" />
              </div>
            </div>
            <div className="text-2xl font-bold text-[var(--foreground)]">
              {card.value}
            </div>
          </div>
        );
      })}
    </div>
  );
}
