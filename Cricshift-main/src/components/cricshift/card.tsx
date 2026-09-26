"use client";

import { type ReactNode, type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

/**
 * Card — the single glass-card recipe for the whole app.
 *
 * Replaces the ad-hoc card styles that drifted across pages
 * (`.glass-card`, `border border-white/10 bg-white/5`,
 * `bg-black/45 backdrop-blur-md`, …) with one consistent surface.
 *
 * Usage:
 *   <Card>…</Card>              // standard glass panel
 *   <Card hover>…</Card>        // adds the interactive lift on hover
 *   <Card className="p-8">…</Card>  // override/extend padding etc.
 */

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Add the interactive hover-lift (for clickable / linked cards). */
  hover?: boolean;
  children: ReactNode;
}

export function Card({ hover = false, className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "glass-card rounded-2xl p-5 sm:p-6",
        hover && "glass-card-hover cursor-pointer",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
