"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect } from "react";
import { Play, ArrowRight, Sparkles } from "lucide-react";
import { StadiumLights } from "./stadium-lights";
import { Particles } from "./particles";
import { HeroDashboard } from "./hero-dashboard";
import Link from "next/link";

export function Hero() {
  // Mouse parallax
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const sx = useSpring(mx, { stiffness: 60, damping: 20 });
  const sy = useSpring(my, { stiffness: 60, damping: 20 });

  const dashX = useTransform(sx, [-0.5, 0.5], [12, -12]);
  const dashY = useTransform(sy, [-0.5, 0.5], [8, -8]);
  const textX = useTransform(sx, [-0.5, 0.5], [6, -6]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mx.set(e.clientX / window.innerWidth - 0.5);
      my.set(e.clientY / window.innerHeight - 0.5);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [mx, my]);

  return (
    <section
      id="home"
      className="relative flex min-h-screen w-full flex-col items-center justify-center overflow-hidden pt-28 pb-16"
    >
      {/* Decorative light accents only — the home video background shows through.
          The previous opaque base + sky gradients were removed so the video is
          visible behind the hero (from the very top of the page). */}
      <StadiumLights />
      <Particles count={26} />

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col items-center px-4 text-center sm:px-6 lg:px-8">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-muted-foreground backdrop-blur-md"
        >
          <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
          AI-Powered Cricket Intelligence
          <span className="h-1 w-1 rounded-full bg-emerald-400 anim-pulse-glow" />
        </motion.div>

        {/* Headline */}
        <motion.h1
          style={{ x: textX }}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="max-w-4xl text-balance text-4xl font-bold leading-[1.05] tracking-tight text-white sm:text-6xl md:text-7xl"
        >
          Detect the Moment{" "}
          <span className="text-gradient-emerald">Cricket</span> Changed{" "}
          <span className="text-gradient-gold">Forever.</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.25 }}
          className="mt-6 max-w-2xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg"
        >
          AI-powered momentum shift detection and win probability prediction
          using machine learning and ball-by-ball analytics.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-9 flex flex-col items-center gap-3 sm:flex-row"
        >
          <Link
            href="/live"
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-3.5 text-sm font-semibold text-emerald-950 shadow-[0_0_30px_rgba(0,200,83,0.45)] transition-transform hover:scale-[1.04]"
          >
            <span className="relative flex h-2.5 w-2.5 mr-1">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-900 opacity-75"></span>
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-950"></span>
            </span>
            Live Matches
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="/historical"
            className="group inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur-md transition-colors hover:bg-white/10"
          >
            Historical Analysis
          </Link>
        </motion.div>

        {/* Dashboard mockup */}
        <motion.div
          style={{ x: dashX, y: dashY }}
          className="mt-14 w-full max-w-4xl"
        >
          <HeroDashboard />
        </motion.div>
      </div>


    </section>
  );
}
