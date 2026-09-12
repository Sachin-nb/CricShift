"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

export function GlowCard({
  children,
  className,
  glow = "emerald",
  hover = true,
}: {
  children: ReactNode;
  className?: string;
  glow?: "emerald" | "gold" | "none";
  hover?: boolean;
}) {
  const glowColor =
    glow === "emerald"
      ? "rgba(0,200,83,0.16)"
      : glow === "gold"
        ? "rgba(255,193,7,0.16)"
        : "rgba(255,255,255,0.06)";

  return (
    <motion.div
      whileHover={
        hover
          ? { y: -6, transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] } }
          : undefined
      }
      className={cn(
        "group relative overflow-hidden rounded-2xl glass-card p-6",
        className,
      )}
    >
      {/* hover glow */}
      <div
        className="pointer-events-none absolute -inset-px rounded-2xl opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{
          background: `radial-gradient(600px circle at var(--mx,50%) var(--my,0%), ${glowColor}, transparent 40%)`,
        }}
      />
      {/* top hairline */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
