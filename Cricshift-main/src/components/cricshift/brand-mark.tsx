"use client";

import { motion } from "framer-motion";
import { Reveal } from "./reveal";

/**
 * BrandMark
 * ---------
 * Closing brand statement: a massive uppercase "CRICSHIFT" wordmark rendered
 * with a dark vertical gradient (embossed / letterpress effect) on pure black —
 * mirroring the reference style. Sits at the very end of the landing page as a
 * dramatic full-bleed sign-off, with a subtle emerald radial glow behind it to
 * tie into the site palette and a small brand mark echoing the reference icon.
 */
export function BrandMark() {
  return (
    <section
      id="brandmark"
      className="relative flex min-h-[70vh] w-full items-center justify-center overflow-hidden py-24"
      aria-label="CricShift"
    >
      {/* Faint emerald radial glow for cohesion with the site (very subtle) */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 55%, rgba(0,200,83,0.10), transparent 70%)",
        }}
      />
      {/* Subtle grid texture, barely visible */}
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.15]" />

      <Reveal className="relative z-10 w-full px-4 text-center" y={40}>
        {/* Eyebrow line */}
        <span className="mb-6 inline-flex items-center gap-2 text-xs font-medium uppercase tracking-[0.4em] text-muted-foreground">
          <span className="h-px w-8 bg-gradient-to-r from-transparent to-emerald-500/60" />
          The Moment Starts Here
          <span className="h-px w-8 bg-gradient-to-l from-transparent to-emerald-500/60" />
        </span>

        {/* Massive embossed wordmark — dark vertical gradient on black */}
        <motion.h2
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          className="select-none text-center font-sans font-black uppercase leading-none tracking-tight"
          style={{
            fontSize: "clamp(3.5rem, 19vw, 18rem)",
            // Dark vertical gradient → embossed / letterpress effect on black.
            // Top of letters ~ near-black, bottom slightly lighter charcoal.
            backgroundImage:
              "linear-gradient(180deg, #0a0a0a 0%, #161616 45%, #2a2a2a 75%, #3a3a3a 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            WebkitTextFillColor: "transparent",
            color: "transparent",
            // Soft outer glow so the letters are legible against pure black.
            filter: "drop-shadow(0 2px 30px rgba(0,200,83,0.08))",
            WebkitTextStroke: "1px rgba(255,255,255,0.04)",
          }}
        >
          CRICSHIFT
        </motion.h2>

        {/* Small brand mark echoing the reference circular icon */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mt-10 flex items-center justify-center gap-3"
        >
          <span className="relative grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 text-lg shadow-[0_0_24px_rgba(0,200,83,0.5)]">
            <span className="drop-shadow">🏏</span>
            <span className="absolute inset-0 rounded-full border border-emerald-300/30 anim-pulse-glow" />
          </span>
          <span className="text-sm font-medium uppercase tracking-[0.3em] text-muted-foreground">
            AI Cricket Intelligence
          </span>
        </motion.div>
      </Reveal>

      {/* Top hairline divider */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-500/25 to-transparent" />
    </section>
  );
}
