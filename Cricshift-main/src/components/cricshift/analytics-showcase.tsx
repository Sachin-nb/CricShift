"use client";

import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  BarChart3,
  Crown,
  Download,
  Filter,
  Flame,
  Gauge,
  Maximize2,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { SectionHeading } from "./section-heading";
import { Reveal } from "./reveal";
import { type ComponentType } from "react";

/* ----------------------------- Sample data ----------------------------- */

const momentumData = [
  { over: 1, m: 52 },
  { over: 2, m: 49 },
  { over: 3, m: 55 },
  { over: 4, m: 51 },
  { over: 5, m: 58 },
  { over: 6, m: 62 },
  { over: 7, m: 56 },
  { over: 8, m: 48 },
  { over: 9, m: 42 },
  { over: 10, m: 38 },
  { over: 11, m: 41 },
  { over: 12, m: 45 },
  { over: 13, m: 50 },
  { over: 14, m: 54 },
  { over: 15, m: 58 },
  { over: 16, m: 62 },
  { over: 17, m: 78 },
  { over: 18, m: 84 },
  { over: 19, m: 88 },
  { over: 20, m: 91 },
];

const winProbData = [
  { over: 1, ind: 52, aus: 48 },
  { over: 2, m: 49, ind: 49, aus: 51 },
  { over: 3, ind: 55, aus: 45 },
  { over: 4, ind: 53, aus: 47 },
  { over: 5, ind: 58, aus: 42 },
  { over: 6, ind: 61, aus: 39 },
  { over: 7, ind: 56, aus: 44 },
  { over: 8, ind: 49, aus: 51 },
  { over: 9, ind: 44, aus: 56 },
  { over: 10, ind: 40, aus: 60 },
  { over: 11, ind: 42, aus: 58 },
  { over: 12, ind: 45, aus: 55 },
  { over: 13, ind: 49, aus: 51 },
  { over: 14, ind: 52, aus: 48 },
  { over: 15, ind: 55, aus: 45 },
  { over: 16, ind: 42, aus: 58 },
  { over: 17, ind: 71, aus: 29 },
  { over: 18, ind: 78, aus: 22 },
  { over: 19, ind: 83, aus: 17 },
  { over: 20, ind: 88, aus: 12 },
];

const pressureData = [{ name: "pressure", value: 83, fill: "#ffc107" }];

const wormData = [
  { over: 1, ind: 6, aus: 8 },
  { over: 2, ind: 14, aus: 16 },
  { over: 3, ind: 22, aus: 24 },
  { over: 4, ind: 30, aus: 34 },
  { over: 5, ind: 38, aus: 44 },
  { over: 6, ind: 47, aus: 52 },
  { over: 7, ind: 52, aus: 60 },
  { over: 8, ind: 58, aus: 68 },
  { over: 9, ind: 64, aus: 76 },
  { over: 10, ind: 71, aus: 84 },
  { over: 11, ind: 78, aus: 92 },
  { over: 12, ind: 84, aus: 100 },
  { over: 13, ind: 90, aus: 108 },
  { over: 14, ind: 96, aus: 116 },
  { over: 15, ind: 105, aus: 124 },
  { over: 16, ind: 115, aus: 132 },
  { over: 17, ind: 130, aus: 140 },
  { over: 18, ind: 148, aus: 148 },
  { over: 19, ind: 165, aus: 156 },
  { over: 20, ind: 182, aus: 162 },
];

const rrrData = [
  { over: 1, crr: 6.0, rrr: 8.1 },
  { over: 2, crr: 7.0, rrr: 8.1 },
  { over: 3, crr: 7.3, rrr: 8.0 },
  { over: 4, crr: 7.5, rrr: 8.0 },
  { over: 5, crr: 7.6, rrr: 8.0 },
  { over: 6, crr: 7.8, rrr: 8.0 },
  { over: 7, crr: 7.4, rrr: 8.2 },
  { over: 8, crr: 7.2, rrr: 8.5 },
  { over: 9, crr: 7.1, rrr: 8.9 },
  { over: 10, crr: 7.1, rrr: 9.3 },
  { over: 11, crr: 7.0, rrr: 9.8 },
  { over: 12, crr: 7.1, rrr: 10.2 },
  { over: 13, crr: 7.2, rrr: 10.6 },
  { over: 14, crr: 7.3, rrr: 11.0 },
  { over: 15, crr: 7.4, rrr: 11.6 },
  { over: 16, crr: 7.6, rrr: 12.5 },
  { over: 17, crr: 8.2, rrr: 11.0 },
  { over: 18, crr: 8.8, rrr: 9.5 },
  { over: 19, crr: 9.4, rrr: 7.5 },
  { over: 20, crr: 9.1, rrr: 0.0 },
];

const partnershipData = [
  { pair: "Rohit · Gill", runs: 42, wicket: "1" },
  { pair: "Gill · Kohli", runs: 67, wicket: "2" },
  { pair: "Kohli · SKY", runs: 38, wicket: "3" },
  { pair: "SKY · Hardik", runs: 54, wicket: "4" },
  { pair: "Hardik · Pant", runs: 31, wicket: "5" },
];

const playerImpact = [
  { name: "Suryakumar", score: 92, role: "Batter · 68(29)" },
  { name: "Hardik", score: 78, role: "AR · 31(12)" },
  { name: "Bumrah", score: 71, role: "Bowler · 1/24" },
  { name: "Kohli", score: 64, role: "Batter · 47(34)" },
];

type Boundary = { over: number; type: "4" | "6"; highlight?: boolean };
const boundaries: Boundary[] = [
  { over: 1.2, type: "4" },
  { over: 2.5, type: "6" },
  { over: 3.4, type: "4" },
  { over: 5.1, type: "4" },
  { over: 6.3, type: "6" },
  { over: 8.2, type: "4" },
  { over: 9.5, type: "4" },
  { over: 11.4, type: "6" },
  { over: 13.2, type: "4" },
  { over: 14.6, type: "4" },
  { over: 15.3, type: "6" },
  { over: 17.2, type: "6", highlight: true },
  { over: 17.4, type: "4", highlight: true },
  { over: 17.5, type: "4", highlight: true },
  { over: 18.1, type: "6" },
  { over: 19.3, type: "4" },
  { over: 19.6, type: "6" },
];

/* ----------------------------- Tooltip style ----------------------------- */

const darkTooltip = {
  background: "rgba(11,11,11,0.92)",
  border: "1px solid rgba(0,200,83,0.3)",
  borderRadius: 10,
  fontSize: 11,
  color: "#f5f7fa",
  boxShadow: "0 8px 30px -8px rgba(0,0,0,0.8)",
  padding: "8px 10px",
} as const;

const axisTick = { fill: "#6b7280", fontSize: 10 } as const;

/* ----------------------------- Subcomponents ----------------------------- */

function ChartCard({
  title,
  icon: Icon,
  accent,
  badge,
  live,
  className,
  children,
}: {
  title: string;
  icon: ComponentType<{ className?: string }>;
  accent: "emerald" | "gold";
  badge?: string;
  live?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  const accentText = accent === "emerald" ? "text-emerald-400" : "text-amber-400";
  const badgeCls =
    accent === "emerald"
      ? "bg-emerald-500/10 text-emerald-300"
      : "bg-amber-400/10 text-amber-300";
  const hoverGlow =
    accent === "emerald"
      ? "group-hover:opacity-100 bg-emerald-500/[0.06]"
      : "group-hover:opacity-100 bg-amber-400/[0.06]";

  return (
    <motion.div
      whileHover={{ y: -4, transition: { duration: 0.25 } }}
      className={`group relative overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.05] to-transparent p-4 ${className ?? ""}`}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Icon className={`h-3.5 w-3.5 ${accentText}`} />
          <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            {title}
          </span>
          {live && (
            <span className="ml-1 flex items-center gap-1 text-[9px] uppercase tracking-widest text-red-400">
              <span className="relative flex h-1.5 w-1.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500/70" />
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-red-500" />
              </span>
              Live
            </span>
          )}
        </div>
        {badge && (
          <span
            className={`rounded-md px-1.5 py-0.5 font-mono text-[10px] font-bold ${badgeCls}`}
          >
            {badge}
          </span>
        )}
      </div>
      {children}
      <div
        className={`pointer-events-none absolute -inset-px rounded-xl opacity-0 transition-opacity duration-500 ${hoverGlow}`}
      />
    </motion.div>
  );
}

function PlayerImpactRow({
  name,
  role,
  score,
}: {
  name: string;
  role: string;
  score: number;
}) {
  return (
    <motion.div
      whileHover={{ x: 3 }}
      className="rounded-lg border border-white/10 bg-white/[0.03] p-2.5"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-emerald-500/30 to-emerald-500/5 text-[10px] font-bold text-emerald-300">
            {name.charAt(0)}
          </div>
          <div>
            <div className="text-xs font-semibold text-white">{name}</div>
            <div className="text-[10px] text-muted-foreground">{role}</div>
          </div>
        </div>
        <span className="font-mono text-sm font-bold text-emerald-300 text-glow-emerald">
          {score}
        </span>
      </div>
      <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-500"
          initial={{ width: 0 }}
          whileInView={{ width: `${score}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
    </motion.div>
  );
}

function BoundaryTimeline() {
  return (
    <div className="relative">
      <div className="relative h-16">
        {/* axis line */}
        <div className="absolute left-0 right-0 top-1/2 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" />
        {/* over markers */}
        {[1, 5, 10, 15, 20].map((o) => (
          <div
            key={o}
            className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${(o / 20) * 100}%` }}
          >
            <div className="h-2 w-px bg-white/15" />
            <span className="absolute top-3 left-1/2 -translate-x-1/2 whitespace-nowrap text-[9px] text-muted-foreground">
              Ov {o}
            </span>
          </div>
        ))}
        {/* boundary dots */}
        {boundaries.map((b, i) => {
          const left = (b.over / 20) * 100;
          const isFour = b.type === "4";
          return (
            <motion.div
              key={`${b.over}-${i}`}
              className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${left}%` }}
              initial={{ scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{
                delay: 0.4 + i * 0.04,
                type: "spring",
                stiffness: 320,
                damping: 18,
              }}
            >
              <div
                className={`grid h-5 w-5 place-items-center rounded-full text-[9px] font-bold ${
                  isFour
                    ? "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-400/40"
                    : "bg-amber-400/20 text-amber-300 ring-1 ring-amber-400/40"
                } ${b.highlight ? "ring-2 ring-amber-300 glow-gold" : ""}`}
              >
                {b.type}
              </div>
            </motion.div>
          );
        })}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-400" /> 4s
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-400" /> 6s
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-300 ring-2 ring-amber-300/40" />
          Turning Point
        </span>
      </div>
    </div>
  );
}

/* ----------------------------- Main ----------------------------- */

export function AnalyticsShowcase() {
  return (
    <section id="analytics" className="relative overflow-hidden py-24 sm:py-32">
      {/* backdrop */}
      <div className="absolute inset-0 -z-10 bg-grid opacity-30" />
      <div className="absolute inset-x-0 top-0 -z-10 h-[600px] bg-radial-fade" />
      <div className="absolute left-1/2 top-24 -z-10 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-emerald-500/10 blur-[140px]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Analytics Dashboard"
          title={
            <>
              A complete{" "}
              <span className="text-gradient-emerald">match intelligence</span>{" "}
              cockpit
            </>
          }
          subtitle="Visualize every turning point — momentum, win probability, pressure and partnerships — synchronized ball-by-ball."
        />

        <Reveal className="mt-12" delay={0.1}>
          <div className="relative">
            {/* glow behind */}
            <div className="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-br from-emerald-500/20 via-transparent to-amber-400/10 blur-2xl" />

            <div className="glass-strong overflow-hidden rounded-[1.5rem] border border-white/10 p-4 shadow-[0_40px_120px_-30px_rgba(0,0,0,0.9)] sm:p-6">
              {/* Top control bar */}
              <div className="flex flex-col gap-3 border-b border-white/5 pb-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="flex items-center gap-1.5 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-red-400">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500/70" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
                    </span>
                    Live
                  </span>
                  <div className="text-sm font-semibold text-white">
                    IND vs AUS · 2nd T20
                  </div>
                  <span className="hidden text-xs text-muted-foreground md:inline">
                    Wankhede · 2nd Innings
                  </span>
                  <span className="hidden font-mono text-xs text-emerald-300 sm:inline">
                    168/4 (17.3)
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {/* phase chips */}
                  <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.03] p-1">
                    {["PP", "Mid", "Death"].map((p, i) => (
                      <button
                        key={p}
                        className={`rounded-md px-2 py-1 text-[10px] font-semibold uppercase tracking-widest transition-colors ${
                          i === 2
                            ? "bg-amber-400/15 text-amber-300"
                            : "text-muted-foreground hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                  {/* icon controls */}
                  {[
                    { Icon: Filter, label: "Filter" },
                    { Icon: Download, label: "Export" },
                    { Icon: Maximize2, label: "Fullscreen" },
                  ].map(({ Icon, label }) => (
                    <button
                      key={label}
                      aria-label={label}
                      className="grid h-8 w-8 place-items-center rounded-md border border-white/10 bg-white/[0.03] text-muted-foreground transition-colors hover:bg-white/10 hover:text-white"
                    >
                      <Icon className="h-3.5 w-3.5" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Bento grid */}
              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-12">
                {/* Momentum Graph - large */}
                <ChartCard
                  title="Momentum"
                  icon={Activity}
                  accent="emerald"
                  badge="+24"
                  live
                  className="sm:col-span-8"
                >
                  <div className="mb-2 flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      Batting Momentum
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-amber-400" />
                      Shift Point
                    </span>
                  </div>
                  <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={momentumData}
                        margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
                      >
                        <defs>
                          <linearGradient id="momFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#00c853" stopOpacity={0.45} />
                            <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.04)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="over"
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          interval={3}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          width={32}
                        />
                        <Tooltip
                          contentStyle={darkTooltip}
                          labelStyle={{ color: "#9aa6b8" }}
                          labelFormatter={(l) => `Over ${l}`}
                          formatter={(v: number) => [`${v}`, "Momentum"]}
                        />
                        <Area
                          type="monotone"
                          dataKey="m"
                          stroke="#00c853"
                          strokeWidth={2}
                          fill="url(#momFill)"
                          isAnimationActive
                          animationDuration={1200}
                        />
                        <ReferenceDot
                          x={17}
                          y={78}
                          r={6}
                          fill="#ffc107"
                          stroke="#fff"
                          strokeWidth={1.5}
                          isFront
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Pressure Meter */}
                <ChartCard
                  title="Pressure Index"
                  icon={Flame}
                  accent="gold"
                  badge="HIGH"
                  className="sm:col-span-4"
                >
                  <div className="flex h-48 w-full items-center justify-center">
                    <div className="relative h-40 w-40">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadialBarChart
                          data={pressureData}
                          innerRadius="72%"
                          outerRadius="100%"
                          startAngle={220}
                          endAngle={-40}
                        >
                          <PolarAngleAxis
                            type="number"
                            domain={[0, 100]}
                            angleAxisId={0}
                            tick={false}
                          />
                          <RadialBar
                            background={{ fill: "rgba(255,255,255,0.06)" }}
                            dataKey="value"
                            cornerRadius={12}
                            isAnimationActive
                            animationDuration={1200}
                          />
                        </RadialBarChart>
                      </ResponsiveContainer>
                      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                        <span className="font-mono text-4xl font-bold text-amber-300 text-glow-gold">
                          83
                        </span>
                        <span className="mt-0.5 text-[10px] uppercase tracking-widest text-muted-foreground">
                          / 100
                        </span>
                        <span className="mt-1 rounded-full bg-amber-400/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest text-amber-300">
                          Death · 2 wkts
                        </span>
                      </div>
                    </div>
                  </div>
                </ChartCard>

                {/* Win Probability */}
                <ChartCard
                  title="Win Probability"
                  icon={Gauge}
                  accent="emerald"
                  badge="IND 88%"
                  className="sm:col-span-7"
                >
                  <div className="mb-2 flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      India
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-amber-400" />
                      Australia
                    </span>
                  </div>
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={winProbData}
                        margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
                      >
                        <defs>
                          <linearGradient id="indFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#00c853" stopOpacity={0.4} />
                            <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="ausFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#ffc107" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#ffc107" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.04)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="over"
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          interval={3}
                        />
                        <YAxis
                          domain={[0, 100]}
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          width={32}
                          tickFormatter={(v) => `${v}%`}
                        />
                        <Tooltip
                          contentStyle={darkTooltip}
                          labelStyle={{ color: "#9aa6b8" }}
                          labelFormatter={(l) => `Over ${l}`}
                          formatter={(v: number, n: string) => [`${v}%`, n === "ind" ? "India" : "Australia"]}
                        />
                        <Area
                          type="monotone"
                          dataKey="ind"
                          stroke="#00c853"
                          strokeWidth={2}
                          fill="url(#indFill)"
                          isAnimationActive
                          animationDuration={1200}
                        />
                        <Area
                          type="monotone"
                          dataKey="aus"
                          stroke="#ffc107"
                          strokeWidth={2}
                          fill="url(#ausFill)"
                          isAnimationActive
                          animationDuration={1400}
                        />
                        <ReferenceDot
                          x={17}
                          y={71}
                          r={5}
                          fill="#ffc107"
                          stroke="#fff"
                          strokeWidth={1.5}
                          isFront
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Player Impact */}
                <ChartCard
                  title="Player Impact"
                  icon={Crown}
                  accent="gold"
                  badge="Top 4"
                  className="sm:col-span-5"
                >
                  <div className="grid grid-cols-1 gap-2">
                    {playerImpact.map((p) => (
                      <PlayerImpactRow
                        key={p.name}
                        name={p.name}
                        role={p.role}
                        score={p.score}
                      />
                    ))}
                  </div>
                </ChartCard>

                {/* Worm Graph */}
                <ChartCard
                  title="Worm"
                  icon={TrendingUp}
                  accent="emerald"
                  className="sm:col-span-4"
                >
                  <div className="mb-2 flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" /> IND
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-amber-400" /> AUS
                    </span>
                  </div>
                  <div className="h-40 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={wormData}
                        margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.04)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="over"
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          interval={4}
                        />
                        <YAxis
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          width={32}
                        />
                        <Tooltip
                          contentStyle={darkTooltip}
                          labelStyle={{ color: "#9aa6b8" }}
                          labelFormatter={(l) => `Over ${l}`}
                          formatter={(v: number, n: string) => [`${v}`, n === "ind" ? "IND" : "AUS"]}
                        />
                        <Line
                          type="monotone"
                          dataKey="ind"
                          stroke="#00c853"
                          strokeWidth={2}
                          dot={false}
                          isAnimationActive
                          animationDuration={1200}
                        />
                        <Line
                          type="monotone"
                          dataKey="aus"
                          stroke="#ffc107"
                          strokeWidth={2}
                          dot={false}
                          isAnimationActive
                          animationDuration={1400}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* RRR vs CRR */}
                <ChartCard
                  title="Required vs Current RR"
                  icon={Target}
                  accent="gold"
                  className="sm:col-span-4"
                >
                  <div className="mb-2 flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" /> CRR
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-amber-400" /> RRR
                    </span>
                  </div>
                  <div className="h-40 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={rrrData}
                        margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.04)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="over"
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          interval={4}
                        />
                        <YAxis
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          width={32}
                        />
                        <Tooltip
                          contentStyle={darkTooltip}
                          labelStyle={{ color: "#9aa6b8" }}
                          labelFormatter={(l) => `Over ${l}`}
                          formatter={(v: number, n: string) => [v.toFixed(1), n === "crr" ? "CRR" : "RRR"]}
                        />
                        <Line
                          type="monotone"
                          dataKey="crr"
                          stroke="#00c853"
                          strokeWidth={2}
                          dot={false}
                          isAnimationActive
                          animationDuration={1200}
                        />
                        <Line
                          type="monotone"
                          dataKey="rrr"
                          stroke="#ffc107"
                          strokeWidth={2}
                          dot={false}
                          strokeDasharray="4 3"
                          isAnimationActive
                          animationDuration={1400}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Partnerships */}
                <ChartCard
                  title="Partnerships"
                  icon={BarChart3}
                  accent="emerald"
                  className="sm:col-span-4"
                >
                  <div className="h-40 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={partnershipData}
                        margin={{ top: 4, right: 4, bottom: 0, left: -20 }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          stroke="rgba(255,255,255,0.04)"
                          vertical={false}
                        />
                        <XAxis
                          dataKey="wicket"
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          tick={axisTick}
                          axisLine={false}
                          tickLine={false}
                          width={32}
                        />
                        <Tooltip
                          contentStyle={darkTooltip}
                          labelStyle={{ color: "#9aa6b8" }}
                          labelFormatter={(l) => `Wicket ${l}`}
                          formatter={(v: number, _n, p) => [
                            `${v} runs`,
                            p?.payload?.pair ?? "",
                          ]}
                          cursor={{ fill: "rgba(255,255,255,0.04)" }}
                        />
                        <Bar
                          dataKey="runs"
                          radius={[4, 4, 0, 0]}
                          isAnimationActive
                          animationDuration={1200}
                        >
                          {partnershipData.map((entry, idx) => (
                            <Cell
                              key={idx}
                              fill={
                                entry.runs >= 50
                                  ? "#00c853"
                                  : entry.runs >= 40
                                    ? "#1ee065"
                                    : "rgba(0,200,83,0.45)"
                              }
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                {/* Boundary Timeline - full width */}
                <ChartCard
                  title="Boundary Timeline"
                  icon={Zap}
                  accent="gold"
                  badge="17 boundaries"
                  className="sm:col-span-12"
                >
                  <BoundaryTimeline />
                </ChartCard>
              </div>

              {/* Footer status bar */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/5 bg-black/30 px-4 py-2 text-[10px] text-muted-foreground">
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 anim-pulse-glow" />
                    Stream OK · 28ms latency
                  </span>
                  <span className="hidden sm:inline">
                    Model · XGBoost + LightGBM ensemble
                  </span>
                </div>
                <div className="flex items-center gap-3 font-mono">
                  <span className="text-emerald-300">CRR 9.65</span>
                  <span className="text-amber-300">REQ 52 off 15</span>
                  <span>Win Prob 88%</span>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
