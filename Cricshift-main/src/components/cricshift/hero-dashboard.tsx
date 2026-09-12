"use client";

import { motion } from "framer-motion";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  YAxis,
  Tooltip,
} from "recharts";
import { useEffect, useState } from "react";
import { Activity, Gauge, Flame, Sparkles, TrendingUp, Zap } from "lucide-react";

/* Deterministic seed curve — identical on server & client (no hydration mismatch) */
function seedCurve() {
  const pts = 20;
  const arr: { i: number; v: number }[] = [];
  let v = 52;
  for (let i = 0; i < pts; i++) {
    const dip = i >= 8 && i <= 11 ? -6 : 0;
    const rally = i >= 12 && i <= 16 ? 4 : 0;
    // fixed pseudo-noise derived from index (deterministic)
    const noise = ((i * 37) % 9) - 4;
    v = v + dip + rally + noise;
    v = Math.max(28, Math.min(82, v));
    arr.push({ i, v: Math.round(v) });
  }
  arr[pts - 1] = { i: pts - 1, v: 74 };
  return arr;
}

/* Build a smooth win-probability curve that shifts over time (client-only) */
function buildCurve() {
  const pts = 20;
  const arr: { i: number; v: number }[] = [];
  let v = 52;
  for (let i = 0; i < pts; i++) {
    // dip mid-game then rally — the "momentum shift"
    const dip = i >= 8 && i <= 11 ? -6 : 0;
    const rally = i >= 12 && i <= 16 ? 4 : 0;
    v = v + dip + rally + (Math.random() * 4 - 2);
    v = Math.max(28, Math.min(82, v));
    arr.push({ i, v: Math.round(v) });
  }
  arr[pts - 1] = { i: pts - 1, v: 74 };
  return arr;
}

export function HeroDashboard() {
  const [data, setData] = useState(seedCurve);
  const [score, setScore] = useState(168);
  const [over, setOver] = useState(17.3);
  const [momentum, setMomentum] = useState(71);

  useEffect(() => {
    const t = setInterval(() => {
      setData(buildCurve());
      setScore((s) => s + Math.floor(Math.random() * 3));
      setOver((o) => {
        const balls = Math.round((o % 1) * 10) + 1;
        if (balls >= 6) return Math.floor(o) + 1;
        return Math.floor(o) + balls / 10;
      });
      setMomentum((m) => Math.max(48, Math.min(94, m + (Math.random() * 8 - 4))));
    }, 2800);
    return () => clearInterval(t);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 40, rotateX: 12 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ duration: 1, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="relative w-full"
      style={{ perspective: 1200 }}
    >
      {/* glow behind */}
      <div className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-br from-emerald-500/20 via-transparent to-amber-400/10 blur-2xl" />

      <div className="glass-strong overflow-hidden rounded-[1.5rem] border border-white/10 p-4 shadow-[0_40px_120px_-30px_rgba(0,0,0,0.9)] sm:p-5">
        {/* top bar */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 items-center justify-center">
              <span className="absolute h-2.5 w-2.5 animate-ping rounded-full bg-red-500/60" />
              <span className="h-2 w-2 rounded-full bg-red-500" />
            </span>
            <span className="text-xs font-semibold uppercase tracking-widest text-red-400">
              Live
            </span>
            <span className="text-xs text-muted-foreground">2nd Innings · T20</span>
          </div>
          <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
            CricShift AI
          </span>
        </div>

        {/* score + metric grid */}
        <div className="grid grid-cols-12 gap-3">
          {/* Live score */}
          <div className="col-span-12 rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-transparent p-4 sm:col-span-5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] uppercase tracking-widest text-muted-foreground">
                Live Score
              </span>
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-2 flex items-end gap-2">
              <span className="font-mono text-4xl font-bold tracking-tight text-white">
                {score}
              </span>
              <span className="mb-1 text-sm text-muted-foreground">/4</span>
            </div>
            <div className="mt-1 font-mono text-sm text-emerald-300">
              Overs {over.toFixed(1)}
            </div>
            <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
              <span>
                Req.{" "}
                <span className="font-semibold text-white">52 off 15</span>
              </span>
              <span className="h-3 w-px bg-white/10" />
              <span>
                CRR{" "}
                <span className="font-semibold text-white">9.65</span>
              </span>
            </div>
          </div>

          {/* Momentum meter */}
          <div className="col-span-6 rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-transparent p-4 sm:col-span-3">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-muted-foreground">
              <Activity className="h-3.5 w-3.5 text-emerald-400" /> Momentum
            </div>
            <div className="mt-3 text-3xl font-bold text-emerald-300 text-glow-emerald">
              {Math.round(momentum)}
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-emerald-500"
                animate={{ width: `${momentum}%` }}
                transition={{ duration: 0.8 }}
              />
            </div>
            <div className="mt-1 text-[10px] text-muted-foreground">
              Batting side ↑
            </div>
          </div>

          {/* Pressure index */}
          <div className="col-span-6 rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-transparent p-4 sm:col-span-4">
            <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-muted-foreground">
              <Flame className="h-3.5 w-3.5 text-amber-400" /> Pressure Index
            </div>
            <div className="mt-3 flex items-center gap-3">
              <GaugeRing value={83} />
              <div className="text-xs leading-relaxed text-muted-foreground">
                <div className="text-white">High</div>
                <div>Death over · 2 wkts</div>
              </div>
            </div>
          </div>

          {/* Win probability chart */}
          <div className="col-span-12 rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-transparent p-4 sm:col-span-7">
            <div className="mb-2 flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-muted-foreground">
                <Gauge className="h-3.5 w-3.5 text-emerald-400" /> Win Probability
              </div>
              <span className="font-mono text-sm font-semibold text-emerald-300">
                74%
              </span>
            </div>
            <div className="h-24 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="wpFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#00c853" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <YAxis domain={[0, 100]} hide />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(11,11,11,0.9)",
                      border: "1px solid rgba(0,200,83,0.3)",
                      borderRadius: 8,
                      fontSize: 11,
                    }}
                    labelStyle={{ color: "#9aa6b8" }}
                    formatter={(val: number) => [`${val}%`, "Win Prob"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="v"
                    stroke="#00c853"
                    strokeWidth={2}
                    fill="url(#wpFill)"
                    isAnimationActive
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Key turning point + AI insights */}
          <div className="col-span-12 grid grid-cols-1 gap-3 sm:col-span-5 sm:grid-cols-1">
            <div className="rounded-xl border border-amber-400/20 bg-amber-400/[0.06] p-4">
              <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-amber-300">
                <Zap className="h-3.5 w-3.5" /> Key Turning Point
              </div>
              <div className="mt-1.5 text-sm font-semibold text-white">
                Over 17.2 — 6, 4, 4
              </div>
              <div className="text-xs text-muted-foreground">
                Win prob jumped 42% → 71%
              </div>
            </div>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] p-4">
              <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-emerald-300">
                <Sparkles className="h-3.5 w-3.5" /> AI Insight
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                Momentum shifted after consecutive boundaries. Model confidence{" "}
                <span className="font-semibold text-emerald-300">0.94</span>.
              </p>
            </div>
          </div>
        </div>

        {/* footer ticker */}
        <div className="mt-3 overflow-hidden rounded-lg border border-white/5 bg-black/40">
          <div className="flex w-max anim-ticker gap-8 px-4 py-1.5 text-[10px] text-muted-foreground">
            {Array.from({ length: 2 }).map((_, k) => (
              <div key={k} className="flex shrink-0 gap-8">
                <span>● IND 168/4 (17.3)</span>
                <span className="text-emerald-400">▲ MOMENTUM +24</span>
                <span>Pressure 83 HIGH</span>
                <span className="text-amber-400">◆ Turning pt Ov 17.2</span>
                <span>Win Prob 74%</span>
                <span className="text-emerald-400">▲ CRR 9.65</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function GaugeRing({ value }: { value: number }) {
  const r = 18;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <div className="relative h-12 w-12">
      <svg className="h-12 w-12 -rotate-90" viewBox="0 0 48 48">
        <circle
          cx="24"
          cy="24"
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="4"
        />
        <circle
          cx="24"
          cy="24"
          r={r}
          fill="none"
          stroke="#ffc107"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ filter: "drop-shadow(0 0 4px rgba(255,193,7,0.6))" }}
        />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-xs font-bold text-amber-300">
        {value}
      </span>
    </div>
  );
}
