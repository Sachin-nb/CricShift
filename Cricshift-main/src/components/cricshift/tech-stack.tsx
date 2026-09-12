"use client";

import { SectionHeading } from "./section-heading";
import { GlowCard } from "./glow-card";
import { StaggerGroup, StaggerItem } from "./reveal";

type Category = "ml" | "data" | "web" | "infra";

type Tech = {
  name: string;
  role: string;
  category: Category;
  badge: string;
};

const techs: Tech[] = [
  { name: "Python", role: "Core ML language", category: "ml", badge: "🐍" },
  { name: "Scikit-Learn", role: "Classical ML models", category: "ml", badge: "SK" },
  { name: "XGBoost", role: "Gradient boosting", category: "ml", badge: "XG" },
  { name: "LightGBM", role: "Fast gradient boosting", category: "ml", badge: "LG" },
  { name: "Pandas", role: "Data wrangling", category: "data", badge: "PD" },
  { name: "NumPy", role: "Numerical compute", category: "data", badge: "NP" },
  { name: "FastAPI", role: "Prediction API", category: "infra", badge: "⚡" },
  { name: "React", role: "Dashboard UI", category: "web", badge: "⚛" },
  { name: "Tailwind CSS", role: "Styling system", category: "web", badge: "TW" },
  { name: "Chart.js", role: "Data visualization", category: "web", badge: "📊" },
  { name: "Docker", role: "Containerization", category: "infra", badge: "🐳" },
  { name: "SQLite", role: "Match database", category: "data", badge: "DB" },
];

type CategoryStyle = {
  glow: "emerald" | "gold" | "none";
  ring: string;
  tile: string;
  text: string;
  label: string;
  labelCls: string;
};

const categoryStyle: Record<Category, CategoryStyle> = {
  ml: {
    glow: "emerald",
    ring: "ring-emerald-500/30",
    tile: "from-emerald-500/30 to-emerald-500/5",
    text: "text-emerald-300",
    label: "ML",
    labelCls: "bg-emerald-500/10 text-emerald-300 border-emerald-500/20",
  },
  data: {
    glow: "gold",
    ring: "ring-amber-400/30",
    tile: "from-amber-400/30 to-amber-400/5",
    text: "text-amber-300",
    label: "DATA",
    labelCls: "bg-amber-400/10 text-amber-300 border-amber-400/20",
  },
  web: {
    glow: "none",
    ring: "ring-white/20",
    tile: "from-white/20 to-white/5",
    text: "text-white",
    label: "WEB",
    labelCls: "bg-white/10 text-white border-white/15",
  },
  infra: {
    glow: "none",
    ring: "ring-slate-300/20",
    tile: "from-slate-300/20 to-slate-300/5",
    text: "text-slate-200",
    label: "INFRA",
    labelCls: "bg-slate-300/10 text-slate-200 border-slate-300/20",
  },
};

const categoryLegend: { label: string; cls: string }[] = [
  { label: "Machine Learning", cls: "bg-emerald-400" },
  { label: "Data", cls: "bg-amber-400" },
  { label: "Web", cls: "bg-white" },
  { label: "Infra", cls: "bg-slate-300" },
];

export function TechStack() {
  return (
    <section id="technology" className="relative overflow-hidden py-24 sm:py-32">
      {/* backdrop */}
      <div className="absolute inset-0 -z-10 bg-grid opacity-30" />
      <div className="absolute inset-x-0 top-0 -z-10 h-[420px] bg-radial-fade" />
      <div className="absolute left-1/2 top-20 -z-10 h-[360px] w-[760px] -translate-x-1/2 rounded-full bg-emerald-500/8 blur-[140px]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Built With"
          title={
            <>
              A modern{" "}
              <span className="text-gradient-emerald">ML &amp; web</span> stack
            </>
          }
          subtitle="Engineered for low-latency predictions, reproducible training, and a buttery-smooth analytics UI."
        />

        {/* Category legend */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          {categoryLegend.map((c) => (
            <span
              key={c.label}
              className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-muted-foreground"
            >
              <span className={`h-2 w-2 rounded-full ${c.cls}`} />
              {c.label}
            </span>
          ))}
        </div>

        <StaggerGroup
          className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-5 lg:grid-cols-6"
          stagger={0.06}
        >
          {techs.map((tech) => {
            const style = categoryStyle[tech.category];
            return (
              <StaggerItem key={tech.name} className="h-full">
                <GlowCard glow={style.glow} className="h-full p-5">
                  <div className="flex h-full flex-col items-center gap-3 text-center">
                    {/* icon tile */}
                    <div
                      className={`relative grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br ${style.tile} text-xl font-bold ${style.text} ring-1 ${style.ring}`}
                    >
                      <span className="text-xl leading-none">{tech.badge}</span>
                      {/* corner sheen */}
                      <div className="pointer-events-none absolute inset-0 rounded-xl bg-gradient-to-br from-white/15 to-transparent" />
                    </div>
                    {/* name + role */}
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-white">
                        {tech.name}
                      </div>
                      <div className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                        {tech.role}
                      </div>
                    </div>
                    {/* category label */}
                    <span
                      className={`rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest ${style.labelCls}`}
                    >
                      {style.label}
                    </span>
                  </div>
                </GlowCard>
              </StaggerItem>
            );
          })}
        </StaggerGroup>

        {/* footer note */}
        <div className="mx-auto mt-10 max-w-2xl text-center text-xs text-muted-foreground">
          <span className="text-emerald-300">4 layers</span> · 12 technologies ·
          one unified pipeline — from raw ball-by-ball CSVs to live AI insights
          in under 200ms.
        </div>
      </div>
    </section>
  );
}
