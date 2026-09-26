"use client";

import { motion } from "framer-motion";

/**
 * SplashScreen — a short cricket-themed intro animation shown once, right after
 * a successful login or signup, before the app is revealed.
 *
 * Sequence (~2.2s total):
 *   1. A spinning red cricket ball (with white seam) drops/scales in.
 *   2. The "CRICSHIFT" wordmark reveals letter-by-letter in the brand gradient.
 *   3. A lime tagline fades in.
 *   4. The whole overlay fades out and calls `onDone`.
 *
 * Uses Framer Motion (already a project dependency) and the site's
 * emerald → amber → lime palette to stay on-brand.
 */

interface SplashScreenProps {
  onDone: () => void;
}

const WORD = "CRICSHIFT";

export function SplashScreen({ onDone }: SplashScreenProps) {
  return (
    <motion.div
      className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-[#0b0b0b] overflow-hidden"
      initial={{ opacity: 1 }}
      animate={{ opacity: 1 }}
      // Fade the entire overlay away near the end, then unmount via onDone.
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Ambient stadium-light glows */}
      <motion.div
        className="pointer-events-none absolute -top-1/4 left-1/4 h-[60vh] w-[50vw] -rotate-12 bg-gradient-to-b from-emerald-400/10 to-transparent blur-3xl"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 1, 0.6] }}
        transition={{ duration: 1.6 }}
      />
      <motion.div
        className="pointer-events-none absolute -top-1/4 right-1/4 h-[60vh] w-[50vw] rotate-12 bg-gradient-to-b from-amber-300/10 to-transparent blur-3xl"
        initial={{ opacity: 0 }}
        animate={{ opacity: [0, 1, 0.6] }}
        transition={{ duration: 1.6, delay: 0.15 }}
      />

      {/* Spinning cricket ball */}
      <motion.div
        className="relative mb-8 h-24 w-24"
        initial={{ scale: 0, y: -120, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 14, delay: 0.1 }}
      >
        <motion.div
          className="h-full w-full rounded-full shadow-[0_0_50px_-6px_rgba(0,200,83,0.5)]"
          style={{
            background:
              "radial-gradient(circle at 32% 28%, #ff6b5e 0%, #d1332a 45%, #8f1a14 100%)",
          }}
          // Continuous spin for the intro moment.
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, ease: "linear", duration: 1.1 }}
        >
          {/* Seam */}
          <div className="absolute left-1/2 top-1/2 h-full w-[18%] -translate-x-1/2 -translate-y-1/2">
            <div className="mx-auto h-full w-[3px] rounded-full bg-white/90" />
            {/* stitch marks */}
            <div className="absolute inset-0 flex flex-col justify-around">
              {Array.from({ length: 7 }).map((_, i) => (
                <span key={i} className="mx-auto block h-[2px] w-3 -rotate-12 rounded-full bg-white/80" />
              ))}
            </div>
          </div>
          {/* Glossy highlight */}
          <div className="absolute left-[22%] top-[18%] h-6 w-6 rounded-full bg-white/30 blur-[3px]" />
        </motion.div>
      </motion.div>

      {/* Wordmark — letter by letter */}
      <div className="flex items-center">
        {WORD.split("").map((ch, i) => (
          <motion.span
            key={i}
            className={
              "text-4xl font-black tracking-tight sm:text-5xl " +
              (i < 4 ? "text-white" : "text-[#00c853]")
            }
            initial={{ opacity: 0, y: 20, filter: "blur(6px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            transition={{ duration: 0.4, delay: 0.5 + i * 0.07, ease: "easeOut" }}
          >
            {ch}
          </motion.span>
        ))}
      </div>

      {/* Tagline */}
      <motion.p
        className="mt-4 text-xs font-semibold uppercase tracking-[0.3em] text-white/40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 1.3 }}
      >
        Loading the arena
      </motion.p>

      {/* Progress bar that runs then triggers onDone */}
      <motion.div className="mt-8 h-0.5 w-40 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-[#00c853]"
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: 1.6, delay: 0.5, ease: "easeInOut" }}
          onAnimationComplete={onDone}
        />
      </motion.div>
    </motion.div>
  );
}
