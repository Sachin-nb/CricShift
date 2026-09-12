"use client";

import { motion } from "framer-motion";
import {
  Activity,
  Brain,
  Cpu,
  Send,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { SectionHeading } from "./section-heading";
import { Reveal } from "./reveal";
import { Particles } from "./particles";
import { type ComponentType } from "react";

type Accent = "emerald" | "gold";

function InsightChip({
  icon: Icon,
  title,
  value,
  subtitle,
  confidence,
  accent,
  delay,
}: {
  icon: ComponentType<{ className?: string }>;
  title: string;
  value: string;
  subtitle: string;
  confidence: number;
  accent: Accent;
  delay: number;
}) {
  const accentText = accent === "emerald" ? "text-emerald-400" : "text-amber-400";
  const accentValue =
    accent === "emerald" ? "text-emerald-300" : "text-amber-300";
  const accentBorder =
    accent === "emerald" ? "border-emerald-500/20" : "border-amber-400/20";
  const barGradient =
    accent === "emerald"
      ? "from-emerald-400 to-emerald-500"
      : "from-amber-300 to-amber-400";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3 }}
      className={`group relative overflow-hidden rounded-xl border ${accentBorder} bg-white/[0.03] p-4 backdrop-blur-md`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          <Icon className={`h-3.5 w-3.5 ${accentText}`} />
          {title}
        </div>
        <span className={`font-mono text-lg font-bold ${accentValue}`}>
          {value}
        </span>
      </div>
      <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>
      {/* confidence bar */}
      <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-white/10">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${barGradient}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${confidence * 100}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: delay + 0.3, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <div className="mt-1 text-right text-[9px] uppercase tracking-widest text-muted-foreground/70">
        {Math.round(confidence * 100)}% confidence
      </div>
      {/* hover glow */}
      <div
        className={`pointer-events-none absolute -inset-px rounded-xl opacity-0 transition-opacity duration-500 group-hover:opacity-100 ${
          accent === "emerald" ? "bg-emerald-500/[0.06]" : "bg-amber-400/[0.06]"
        }`}
      />
    </motion.div>
  );
}

export function AiInsight() {
  return (
    <section id="ai-insight" className="relative overflow-hidden py-24 sm:py-32">
      {/* backdrop */}
      <div className="absolute inset-0 -z-10 bg-grid opacity-20" />
      <div className="absolute left-1/2 top-1/2 -z-10 h-[500px] w-[760px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-500/10 blur-[140px]" />
      <div className="absolute right-1/4 top-1/3 -z-10 h-[300px] w-[300px] rounded-full bg-amber-400/8 blur-[120px]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Explainable AI"
          title={
            <>
              Your AI{" "}
              <span className="text-gradient-emerald">co-pilot</span> explains
              every shift
            </>
          }
          subtitle="Beyond prediction — CricShift AI narrates the why behind every momentum swing in plain language."
        />

        <Reveal className="mt-12" delay={0.1}>
          <div className="relative">
            {/* outer glow */}
            <div className="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-br from-emerald-500/18 via-transparent to-amber-400/10 blur-2xl" />

            <div className="glass-strong relative overflow-hidden rounded-[1.5rem] border border-white/10 p-6 shadow-[0_40px_120px_-30px_rgba(0,0,0,0.9)] sm:p-8">
              <Particles count={18} className="opacity-60" />

              {/* scan line sweep */}
              <motion.div
                className="pointer-events-none absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-emerald-400/60 to-transparent"
                animate={{ top: ["0%", "100%", "0%"] }}
                transition={{
                  duration: 9,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />

              {/* Header */}
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500/60" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                  </span>
                  <span className="text-[11px] font-semibold uppercase tracking-widest text-emerald-300">
                    CricShift AI · Active
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <Cpu className="h-3 w-3" />
                  <span>Model confidence</span>
                  <span className="font-mono text-emerald-300">0.94</span>
                </div>
              </div>

              {/* Chat row: orb + message bubble */}
              <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                {/* AI Orb */}
                <div className="relative mx-auto h-24 w-24 shrink-0 sm:mx-0">
                  {/* outer rotating dashed ring */}
                  <div className="anim-spin-slow absolute inset-0 rounded-full border border-dashed border-emerald-500/30" />
                  {/* mid rotating ring */}
                  <div
                    className="absolute inset-2 rounded-full border border-amber-400/20"
                    style={{
                      animation: "spinSlow 36s linear infinite reverse",
                    }}
                  />
                  {/* orb core */}
                  <div className="absolute inset-4 grid place-items-center rounded-full bg-gradient-to-br from-emerald-500/30 via-emerald-500/10 to-amber-400/20 anim-pulse-glow glow-emerald">
                    <Brain className="h-7 w-7 text-emerald-300" />
                  </div>
                  {/* orbiting dot */}
                  <motion.div
                    className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(255,193,7,0.8)]"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
                    style={{ transformOrigin: "0 48px" }}
                  />
                </div>

                {/* Message bubble */}
                <div className="relative flex-1">
                  <div className="relative overflow-hidden rounded-2xl rounded-tl-sm border border-emerald-500/30 bg-emerald-500/[0.07] p-4 backdrop-blur-md sm:p-5">
                    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-emerald-300">
                      <Sparkles className="h-3 w-3" />
                      Insight · Over 17
                    </div>
                    <p className="text-sm leading-relaxed text-white sm:text-base">
                      Momentum shifted in{" "}
                      <span className="font-semibold text-amber-300">
                        Over 17
                      </span>{" "}
                      after consecutive boundaries increased the batting
                      side&apos;s expected win probability from{" "}
                      <span className="font-mono text-emerald-300">42%</span> to{" "}
                      <span className="font-mono text-emerald-300">71%</span>.
                    </p>

                    {/* equalizer + analyzing indicator */}
                    <div className="mt-4 flex items-center gap-1.5">
                      {[5, 9, 6, 11, 4, 8, 5].map((h, i) => (
                        <motion.span
                          key={i}
                          className="w-1 rounded-full bg-emerald-400/70"
                          animate={{ height: [h, h * 1.9, h] }}
                          transition={{
                            duration: 0.9,
                            repeat: Infinity,
                            delay: i * 0.08,
                            ease: "easeInOut",
                          }}
                          style={{ height: h }}
                        />
                      ))}
                      <span className="ml-2 text-[10px] uppercase tracking-widest text-muted-foreground">
                        analyzing…
                      </span>
                    </div>
                  </div>

                  {/* connection line from orb to bubble (desktop) */}
                  <div className="absolute -left-5 top-8 hidden h-px w-5 bg-gradient-to-r from-emerald-500/50 to-transparent sm:block" />
                </div>
              </div>

              {/* Follow-up insight chips */}
              <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
                <InsightChip
                  icon={Activity}
                  title="Bowler Pressure"
                  value="88"
                  subtitle="Spiked after 3 consecutive boundaries"
                  confidence={0.88}
                  accent="gold"
                  delay={0.1}
                />
                <InsightChip
                  icon={TrendingUp}
                  title="Boundary Probability"
                  value="64%"
                  subtitle="Predicted for next over"
                  confidence={0.64}
                  accent="emerald"
                  delay={0.2}
                />
                <InsightChip
                  icon={Zap}
                  title="Momentum Velocity"
                  value="+24"
                  subtitle="Largest single-over shift"
                  confidence={0.94}
                  accent="emerald"
                  delay={0.3}
                />
              </div>

              {/* Input bar */}
              <div className="mt-6 flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] p-2 pl-4 backdrop-blur-md transition-colors focus-within:border-emerald-500/30">
                <Sparkles className="h-4 w-4 shrink-0 text-emerald-400/70" />
                <input
                  type="text"
                  placeholder="Ask CricShift AI…"
                  className="flex-1 bg-transparent text-sm text-white placeholder:text-muted-foreground/60 focus:outline-none"
                  aria-label="Ask CricShift AI"
                />
                <span className="hidden text-[10px] uppercase tracking-widest text-muted-foreground sm:inline">
                  ⌘K
                </span>
                <button
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 text-emerald-950 shadow-[0_0_18px_rgba(0,200,83,0.45)] transition-transform hover:scale-105"
                  aria-label="Send"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* footer hint chips */}
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                  Try:
                </span>
                {[
                  "Why did momentum shift?",
                  "Predict next over",
                  "Best bowler for death",
                ].map((q) => (
                  <button
                    key={q}
                    className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-[11px] text-muted-foreground transition-colors hover:border-emerald-500/30 hover:bg-emerald-500/5 hover:text-emerald-300"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
