"use client";

import { Trophy, Database, Target, Activity, type LucideIcon } from "lucide-react";
import { SectionHeading } from "./section-heading";
import { AnimatedCounter } from "./animated-counter";
import { StaggerGroup, StaggerItem } from "./reveal";
import { Particles } from "./particles";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api/client";

type Stat = {
  icon: LucideIcon;
  value: number;
  suffix: string;
  label: string;
  glow: "emerald" | "gold";
  gradient: string;
  iconWrap: string;
};

/* Fallback values shown while API loads */
const DEFAULTS: Stat[] = [
  {
    icon: Trophy,
    value: 0,
    suffix: "+",
    label: "IPL Teams Tracked",
    glow: "gold",
    gradient: "text-gradient-gold",
    iconWrap:
      "border border-amber-500/30 bg-gradient-to-br from-amber-500/25 to-amber-500/5 text-amber-300",
  },
  {
    icon: Database,
    value: 0,
    suffix: "+",
    label: "Players in Database",
    glow: "emerald",
    gradient: "text-gradient-emerald",
    iconWrap:
      "border border-emerald-500/30 bg-gradient-to-br from-emerald-500/25 to-emerald-500/5 text-emerald-300",
  },
  {
    icon: Target,
    value: 0,
    suffix: "+",
    label: "Venues Analyzed",
    glow: "emerald",
    gradient: "text-gradient-emerald",
    iconWrap:
      "border border-emerald-500/30 bg-gradient-to-br from-emerald-500/25 to-emerald-500/5 text-emerald-300",
  },
  {
    icon: Activity,
    value: 150,
    suffix: "+",
    label: "Momentum Shifts Identified",
    glow: "gold",
    gradient: "text-gradient-gold",
    iconWrap:
      "border border-amber-500/30 bg-gradient-to-br from-amber-500/25 to-amber-500/5 text-amber-300",
  },
];

export function Stats() {
  const [stats, setStats] = useState<Stat[]>(DEFAULTS);

  useEffect(() => {
    /* Fetch real counts from the API on mount */
    async function fetchCounts() {
      try {
        const [players, teams, venues] = await Promise.all([
          apiGet<{ total: number }>("/api/analytics/players", { limit: 1 }),
          apiGet<{ total: number }>("/api/analytics/teams", {}),
          apiGet<{ total: number }>("/api/analytics/venues", {}),
        ]);

        setStats((prev) => [
          { ...prev[0], value: teams.total },
          { ...prev[1], value: players.total },
          { ...prev[2], value: venues.total },
          prev[3], // Momentum shifts — keep static
        ]);
      } catch {
        /* API not reachable — silently keep defaults */
      }
    }
    fetchCounts();
  }, []);

  return (
    <section id="stats" className="relative overflow-hidden py-24 sm:py-32">
      {/* Background flourishes */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-[0.16]" />
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(0,200,83,0.14), transparent 55%), radial-gradient(ellipse at 50% 100%, rgba(255,193,7,0.08), transparent 55%)",
        }}
      />
      <div className="pointer-events-none absolute inset-x-0 bottom-16 -z-10 h-px bg-gradient-to-r from-transparent via-emerald-500/25 to-transparent" />
      <div className="pointer-events-none absolute inset-x-0 top-24 -z-10 h-px bg-gradient-to-r from-transparent via-amber-400/15 to-transparent" />
      <Particles count={14} className="opacity-50" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Snapshot"
          title="By the Numbers"
          subtitle="Every match in our index, every ball, every shift — modeled, verified, and surfaced in real time."
        />

        <StaggerGroup
          className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
          stagger={0.12}
        >
          {stats.map((s) => {
            const Icon = s.icon;
            const isGold = s.glow === "gold";
            return (
              <StaggerItem key={s.label} className="h-full">
                <div className="group relative h-full overflow-hidden rounded-2xl glass-card glass-card-hover p-6 transition-colors duration-500 hover:border-white/15 sm:p-7">
                  <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/25 to-transparent" />
                  <div
                    className="pointer-events-none absolute inset-0 opacity-70 transition-opacity duration-500 group-hover:opacity-100"
                    style={{
                      background: isGold
                        ? "radial-gradient(circle at 100% 0%, rgba(255,193,7,0.18), transparent 55%)"
                        : "radial-gradient(circle at 100% 0%, rgba(0,200,83,0.18), transparent 55%)",
                    }}
                  />
                  <div
                    className={`pointer-events-none absolute inset-x-6 bottom-0 h-px ${isGold ? "bg-amber-400/30" : "bg-emerald-400/30"}`}
                  />

                  <div className="relative z-10 flex h-full flex-col gap-5">
                    <div
                      className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${s.iconWrap}`}
                      style={{
                        boxShadow: isGold
                          ? "0 0 24px -6px rgba(255,193,7,0.6), inset 0 1px 0 rgba(255,255,255,0.08)"
                          : "0 0 24px -6px rgba(0,200,83,0.6), inset 0 1px 0 rgba(255,255,255,0.08)",
                      }}
                    >
                      <Icon className="h-6 w-6" />
                    </div>
                    <div>
                      <div
                        className={`text-4xl font-bold tracking-tight tabular-nums sm:text-5xl ${s.gradient}`}
                      >
                        <AnimatedCounter
                          value={s.value}
                          suffix={s.suffix}
                          duration={2200}
                        />
                      </div>
                      <p className="mt-2 text-sm font-medium text-muted-foreground">
                        {s.label}
                      </p>
                    </div>
                  </div>
                </div>
              </StaggerItem>
            );
          })}
        </StaggerGroup>
      </div>
    </section>
  );
}
