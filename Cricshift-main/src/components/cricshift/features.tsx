"use client";

import {
  TrendingUp,
  Gauge,
  Flame,
  Users,
  Brain,
  GitCommitVertical,
  ArrowRight,
  type LucideIcon,
} from "lucide-react";
import { SectionHeading } from "./section-heading";
import { GlowCard } from "./glow-card";
import { StaggerGroup, StaggerItem } from "./reveal";
import { Particles } from "./particles";

type Feature = {
  icon: LucideIcon;
  title: string;
  description: string;
  glow: "emerald" | "gold";
};

const features: Feature[] = [
  {
    icon: TrendingUp,
    title: "Momentum Shift Detection",
    description: "AI detects exactly where a match changed.",
    glow: "emerald",
  },
  {
    icon: Gauge,
    title: "Win Probability",
    description: "Predicts winning chances after every ball.",
    glow: "emerald",
  },
  {
    icon: Flame,
    title: "Pressure Index",
    description: "Measures pressure in real time.",
    glow: "gold",
  },
  {
    icon: Users,
    title: "Player Impact Analysis",
    description: "Ranks players by momentum contribution.",
    glow: "gold",
  },
  {
    icon: Brain,
    title: "Explainable AI",
    description: "Shows WHY the model made each prediction.",
    glow: "emerald",
  },
  {
    icon: GitCommitVertical,
    title: "Interactive Match Timeline",
    description: "Visualize every turning point.",
    glow: "emerald",
  },
];

function iconWrapClass(glow: "emerald" | "gold") {
  return glow === "gold"
    ? "border border-amber-500/30 bg-gradient-to-br from-amber-500/25 to-amber-500/5 text-amber-300"
    : "border border-emerald-500/30 bg-gradient-to-br from-emerald-500/25 to-emerald-500/5 text-emerald-300";
}

function iconGlow(glow: "emerald" | "gold") {
  return glow === "gold"
    ? "0 0 24px -6px rgba(255,193,7,0.6), inset 0 1px 0 rgba(255,255,255,0.08)"
    : "0 0 24px -6px rgba(0,200,83,0.6), inset 0 1px 0 rgba(255,255,255,0.08)";
}

export function Features() {
  return (
    <section id="features" className="relative overflow-hidden py-24 sm:py-32">
      {/* Background flourishes */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-[0.14]" />
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(0,200,83,0.14), transparent 55%)",
        }}
      />
      <Particles count={18} className="opacity-50" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Capabilities"
          title="Everything you need to read the game"
          subtitle="CricShift fuses momentum tracking, win-probability modeling, and a live pressure index into one explainable layer of cricket intelligence."
        />

        <StaggerGroup
          className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3"
          stagger={0.1}
        >
          {features.map((f) => {
            const Icon = f.icon;
            const isGold = f.glow === "gold";
            return (
              <StaggerItem key={f.title} className="h-full">
                <GlowCard glow={f.glow} className="h-full p-6 sm:p-7">
                  <div className="flex h-full flex-col gap-5">
                    <div
                      className={`inline-flex h-12 w-12 items-center justify-center rounded-xl ${iconWrapClass(f.glow)}`}
                      style={{ boxShadow: iconGlow(f.glow) }}
                    >
                      <Icon className="h-6 w-6" />
                    </div>
                    <div className="flex flex-1 flex-col gap-2">
                      <h3 className="text-lg font-semibold tracking-tight text-white">
                        {f.title}
                      </h3>
                      <p className="text-sm leading-relaxed text-muted-foreground">
                        {f.description}
                      </p>
                    </div>
                    <div
                      className={`flex translate-y-1 items-center gap-1.5 text-xs font-medium opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100 ${isGold ? "text-amber-300" : "text-emerald-300"}`}
                    >
                      <span>Learn more</span>
                      <ArrowRight className="h-3.5 w-3.5 transition-transform duration-300 group-hover:translate-x-1" />
                    </div>
                  </div>
                </GlowCard>
              </StaggerItem>
            );
          })}
        </StaggerGroup>
      </div>
    </section>
  );
}
