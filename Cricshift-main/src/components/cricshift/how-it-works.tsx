"use client";

import { motion } from "framer-motion";
import {
  Database,
  SlidersHorizontal,
  BrainCircuit,
  Activity,
  Gauge,
  LayoutDashboard,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";
import { SectionHeading } from "./section-heading";
import { StaggerGroup, StaggerItem } from "./reveal";
import { Particles } from "./particles";

type Step = {
  n: number;
  icon: LucideIcon;
  title: string;
  desc: string;
};

const steps: Step[] = [
  {
    n: 1,
    icon: Database,
    title: "Collect Ball-by-ball Data",
    desc: "Ingest every delivery from international and franchise matches into a unified schema.",
  },
  {
    n: 2,
    icon: SlidersHorizontal,
    title: "Feature Engineering",
    desc: "Derive context-aware features — venue, phase, bowler type, batter form, pressure state.",
  },
  {
    n: 3,
    icon: BrainCircuit,
    title: "Machine Learning Models",
    desc: "Train gradient-boosted and sequence models on millions of annotated balls.",
  },
  {
    n: 4,
    icon: Activity,
    title: "Momentum Detection Engine",
    desc: "Identify inflection points where probability mass shifted decisively.",
  },
  {
    n: 5,
    icon: Gauge,
    title: "Win Probability Prediction",
    desc: "Recalculate winning chances after every ball with calibrated confidence.",
  },
  {
    n: 6,
    icon: LayoutDashboard,
    title: "Interactive Dashboard",
    desc: "Explore timelines, players, and turning points in a live analyst view.",
  },
];

function StepCircle({
  icon: Icon,
  n,
  size,
}: {
  icon: LucideIcon;
  n: number;
  size: "lg" | "sm";
}) {
  const dimension = size === "lg" ? "h-20 w-20" : "h-16 w-16";
  const iconSize = size === "lg" ? "h-7 w-7" : "h-6 w-6";
  return (
    <div className="relative z-10 shrink-0">
      <div
        className={`flex ${dimension} items-center justify-center rounded-full border border-white/10 bg-[#0b0b0b] p-1.5`}
      >
        <div className="flex h-full w-full items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/25 via-emerald-500/5 to-amber-500/10 text-emerald-300 glow-emerald">
          <Icon className={iconSize} />
        </div>
      </div>
      <div className="absolute -right-1 -top-1 flex h-6 w-6 items-center justify-center rounded-full border border-amber-400/40 bg-[#0b0b0b] text-[11px] font-bold text-amber-300">
        {n}
      </div>
    </div>
  );
}

export function HowItWorks() {
  return (
    <section id="how" className="relative overflow-hidden py-24 sm:py-32">
      {/* Background flourishes */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-grid opacity-[0.14]" />
      <div
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(0,200,83,0.12), transparent 55%), radial-gradient(ellipse at 100% 80%, rgba(255,193,7,0.08), transparent 55%)",
        }}
      />
      <Particles count={16} className="opacity-50" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Pipeline"
          title="How CricShift works"
          subtitle="An end-to-end ML pipeline that turns raw scorecard data into a live, explainable read of the match."
        />

        {/* Desktop horizontal timeline */}
        <div className="relative mt-16 hidden lg:block">
          {/* connecting gradient line */}
          <div className="pointer-events-none absolute inset-x-[8%] top-10 h-0.5 -translate-y-1/2 overflow-hidden rounded-full">
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/60 via-emerald-400/40 to-amber-400/60" />
            <motion.div
              className="absolute inset-y-0 left-0 w-1/5 rounded-full"
              style={{
                background:
                  "linear-gradient(90deg, transparent, rgba(255,255,255,0.95), transparent)",
              }}
              initial={{ x: "-100%" }}
              animate={{ x: "500%" }}
              transition={{ duration: 4.5, repeat: Infinity, ease: "linear" }}
            />
          </div>

          <StaggerGroup
            className="relative grid grid-cols-6 gap-4"
            stagger={0.12}
          >
            {steps.map((s, i) => (
              <StaggerItem key={s.n} className="relative">
                <div className="flex flex-col items-center px-1 text-center">
                  <StepCircle icon={s.icon} n={s.n} size="lg" />
                  <h3 className="mt-5 text-sm font-semibold tracking-tight text-white">
                    {s.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                    {s.desc}
                  </p>
                </div>
                {/* arrow between steps */}
                {i < steps.length - 1 && (
                  <div className="absolute -right-2 top-10 z-20 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full border border-white/10 bg-[#0b0b0b]">
                    <ChevronRight className="h-3 w-3 text-emerald-400/70" />
                  </div>
                )}
              </StaggerItem>
            ))}
          </StaggerGroup>
        </div>

        {/* Mobile / tablet vertical timeline */}
        <div className="relative mt-12 lg:hidden">
          {/* vertical gradient line */}
          <div className="pointer-events-none absolute bottom-2 left-8 top-2 w-0.5 -translate-x-1/2 overflow-hidden rounded-full">
            <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/60 via-emerald-400/40 to-amber-400/60" />
            <motion.div
              className="absolute left-0 top-0 h-1/5 w-full rounded-full"
              style={{
                background:
                  "linear-gradient(180deg, transparent, rgba(255,255,255,0.95), transparent)",
              }}
              initial={{ y: "-100%" }}
              animate={{ y: "500%" }}
              transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
            />
          </div>

          <StaggerGroup
            className="relative flex flex-col gap-7"
            stagger={0.1}
          >
            {steps.map((s) => (
              <StaggerItem key={s.n} className="relative">
                <div className="flex items-start gap-5">
                  <StepCircle icon={s.icon} n={s.n} size="sm" />
                  <div className="flex-1 pt-1">
                    <h3 className="text-base font-semibold tracking-tight text-white">
                      {s.title}
                    </h3>
                    <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                      {s.desc}
                    </p>
                  </div>
                </div>
              </StaggerItem>
            ))}
          </StaggerGroup>
        </div>
      </div>
    </section>
  );
}
