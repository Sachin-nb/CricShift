"use client";

import { Brain, Sparkles, Zap, GraduationCap, Activity } from "lucide-react";
import { SectionHeading } from "./section-heading";
import { GlowCard } from "./glow-card";
import { Reveal, StaggerGroup, StaggerItem } from "./reveal";
import { Particles } from "./particles";
import { HowItWorks } from "./how-it-works";
import { TechStack } from "./tech-stack";

/**
 * About
 * -----
 * A semantic grouping of the project's "about" content:
 *   1. What is CricShift? — a premium intro block introducing the platform.
 *   2. How CricShift Works — the end-to-end ML pipeline.
 *   3. Technology Stack — the tools the project is built with.
 *
 * The wrapper carries id="about" (the navbar target). The two existing
 * sections (HowItWorks id="how", TechStack id="technology") are rendered
 * inside; nested <section> elements are valid HTML5 and keep their own
 * visual treatment intact.
 */
export function About() {
  return (
    <section id="about" className="relative">
      <WhatIsCricShift />
      <HowItWorks />
      <TechStack />
    </section>
  );
}

/* ---------------- What is CricShift? ---------------- */
function WhatIsCricShift() {
  const pillars = [
    {
      icon: Brain,
      title: "Machine-Learning Core",
      glow: "emerald" as const,
      desc: "Gradient-boosted models (XGBoost, LightGBM) trained on 300,000+ ball-by-ball events detect momentum shifts with 95% prediction accuracy.",
    },
    {
      icon: Sparkles,
      title: "Explainable by Design",
      glow: "gold" as const,
      desc: "Every prediction ships with SHAP-based feature attribution — you always know WHY the model forecasted a shift, not just that it did.",
    },
    {
      icon: Zap,
      title: "Real-Time Intelligence",
      glow: "emerald" as const,
      desc: "Ball-by-ball updates to momentum, pressure index, and win probability — a live cockpit that reads every delivery as it happens.",
    },
    {
      icon: GraduationCap,
      title: "Research-Driven",
      glow: "gold" as const,
      desc: "Born as a university research project bridging explainable AI, predictive modeling, and broadcast-grade sports visualization.",
    },
  ];

  return (
    <div className="relative overflow-hidden py-24 sm:py-32">
      {/* atmosphere */}
      <div className="absolute inset-0 -z-10 bg-grid opacity-40" />
      <div className="absolute inset-0 -z-10 bg-radial-fade" />
      <div
        className="pointer-events-none absolute -top-20 right-0 -z-10 h-[28rem] w-[28rem] rounded-full opacity-30 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, rgba(255,193,7,0.18), transparent 70%)",
        }}
      />
      <Particles count={16} />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="About CricShift"
          title={
            <>
              What is <span className="text-gradient-emerald">CricShift</span>?
            </>
          }
          subtitle="An AI-powered cricket analytics platform that detects the exact moments a match's momentum shifts — and predicts win probability after every ball."
        />

        {/* Intro paragraph */}
        <Reveal className="mx-auto mt-8 max-w-3xl text-center" delay={0.1}>
          <p className="text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
            CricShift turns raw ball-by-ball scorecard data into a live,
            explainable read of the game. Using machine learning models trained
            on hundreds of thousands of deliveries, it pinpoints{" "}
            <span className="font-semibold text-emerald-300">
              where a match changed
            </span>
            , quantifies pressure in real time, and forecasts each side's
            winning chances — so you don't just see what happened, you{" "}
            <span className="font-semibold text-amber-300">
              understand why it changed
            </span>
            .
          </p>
        </Reveal>

        {/* Pillar cards */}
        <StaggerGroup
          className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4"
          stagger={0.1}
        >
          {pillars.map((p) => (
            <StaggerItem key={p.title}>
              <GlowCard glow={p.glow} className="h-full">
                <div className="flex h-full flex-col gap-4">
                  <span
                    className={`grid h-12 w-12 place-items-center rounded-xl ${
                      p.glow === "emerald"
                        ? "bg-gradient-to-br from-emerald-400/20 to-emerald-600/10 text-emerald-300"
                        : "bg-gradient-to-br from-amber-400/20 to-amber-600/10 text-amber-300"
                    } border ${
                      p.glow === "emerald"
                        ? "border-emerald-500/30"
                        : "border-amber-400/30"
                    }`}
                  >
                    <p.icon className="h-6 w-6" />
                  </span>
                  <h3 className="text-lg font-bold text-white">{p.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {p.desc}
                  </p>
                </div>
              </GlowCard>
            </StaggerItem>
          ))}
        </StaggerGroup>

        {/* Tagline strip */}
        <Reveal className="mt-14" delay={0.2}>
          <div className="glass-card flex flex-col items-center gap-4 rounded-2xl px-6 py-8 text-center sm:flex-row sm:justify-center sm:gap-6 sm:text-left">
            <Activity className="h-8 w-8 shrink-0 text-emerald-400 anim-pulse-glow" />
            <p className="max-w-2xl text-balance text-base font-medium text-white sm:text-lg">
              Detect the moment cricket changed forever —{" "}
              <span className="text-gradient-gold">
                ball by ball, over by over, shift by shift.
              </span>
            </p>
          </div>
        </Reveal>
      </div>
    </div>
  );
}
