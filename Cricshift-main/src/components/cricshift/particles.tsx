"use client";

import { useMemo } from "react";

// Deterministic PRNG — identical output on server & client (no hydration mismatch).
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Floating particle field — emerald + gold motes drifting upward.
 * Pure CSS animation, no canvas, performant. Deterministic for SSR safety.
 */
export function Particles({
  count = 28,
  className = "",
}: {
  count?: number;
  className?: string;
}) {
  const particles = useMemo(() => {
    // Seed from count so each section's particle field differs but stays stable.
    const rand = mulberry32(count * 99991 + 7);
    return Array.from({ length: count }).map((_, i) => {
      const size = rand() * 3 + 1.5;
      const left = rand() * 100;
      const delay = rand() * 18;
      const duration = rand() * 14 + 16;
      const gold = rand() > 0.6;
      return { i, size, left, delay, duration, gold };
    });
  }, [count]);

  return (
    <div
      className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`}
      aria-hidden
    >
      {particles.map((p) => (
        <span
          key={p.i}
          className="absolute bottom-0 rounded-full"
          style={{
            left: `${p.left}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            background: p.gold ? "#ffc107" : "#00c853",
            boxShadow: `0 0 ${p.size * 3}px ${p.gold ? "rgba(255,193,7,0.8)" : "rgba(0,200,83,0.8)"}`,
            animation: `floatParticle ${p.duration}s linear ${p.delay}s infinite`,
            opacity: 0,
          }}
        />
      ))}
    </div>
  );
}
