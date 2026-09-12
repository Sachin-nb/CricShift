"use client";

import { cn } from "@/lib/utils";

/**
 * Animated cricket stadium floodlights with beams + drifting fog.
 * Purely decorative (aria-hidden).
 */
export function StadiumLights({
  className,
  flicker = true,
}: {
  className?: string;
  flicker?: boolean;
}) {
  return (
    <div
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
      aria-hidden
    >
      {/* Floodlight pylons (top corners) */}
      <div className="absolute -top-10 left-[6%] sm:left-[12%]">
        <LightPylon flicker={flicker} />
      </div>
      <div className="absolute -top-10 right-[6%] sm:right-[12%]">
        <LightPylon flicker={flicker} />
      </div>

      {/* Light cones / beams */}
      <div className="absolute -top-2 left-[2%] h-[70vh] w-[40vw] -rotate-[18deg] bg-gradient-to-b from-emerald-400/10 via-emerald-400/[0.04] to-transparent blur-2xl" />
      <div className="absolute -top-2 right-[2%] h-[70vh] w-[40vw] rotate-[18deg] bg-gradient-to-b from-amber-300/10 via-amber-300/[0.04] to-transparent blur-2xl" />

      {/* Drifting fog layers */}
      <div
        className="absolute bottom-0 left-0 h-1/2 w-full"
        style={{
          background:
            "radial-gradient(ellipse at 30% 100%, rgba(0,200,83,0.10), transparent 60%), radial-gradient(ellipse at 70% 100%, rgba(255,193,7,0.08), transparent 60%)",
          animation: "fogDrift 18s ease-in-out infinite",
        }}
      />
      <div
        className="absolute bottom-0 left-0 h-1/3 w-full opacity-60"
        style={{
          background:
            "linear-gradient(to top, rgba(11,11,11,0.85), transparent)",
        }}
      />
    </div>
  );
}

function LightPylon({ flicker }: { flicker: boolean }) {
  return (
    <div className="relative flex flex-col items-center">
      {/* light bank */}
      <div
        className={`grid grid-cols-4 gap-1 rounded-md border border-white/10 bg-white/5 p-1.5 ${
          flicker ? "anim-flicker" : ""
        }`}
        style={{
          boxShadow:
            "0 0 30px rgba(255,255,255,0.5), 0 0 80px rgba(0,200,83,0.25)",
        }}
      >
        {Array.from({ length: 8 }).map((_, i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-[2px] bg-white"
            style={{ boxShadow: "0 0 8px rgba(255,255,255,0.9)" }}
          />
        ))}
      </div>
      {/* pylon stem */}
      <div className="h-16 w-1 bg-gradient-to-b from-white/30 to-transparent sm:h-28" />
    </div>
  );
}
