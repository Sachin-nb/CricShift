"use client";

import { usePathname } from "next/navigation";

/**
 * SiteBackground
 *
 * Renders the stadium photo backdrop on every route EXCEPT the home page (`/`),
 * which has its own looping video background (handled by HomeVideoBackground).
 *
 * - Fixed to the viewport, sits behind all content, and never intercepts
 *   pointer / scroll events (decorative only).
 * - A dark tint overlay keeps existing text, cards, and controls fully legible.
 * - On the home page this renders nothing so the video background is untouched.
 */
export function SiteBackground() {
  const pathname = usePathname();

  // Home page keeps its dedicated video background — do not render here.
  if (pathname === "/") return null;

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-[1] overflow-hidden"
    >
      {/* Stadium photo */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/stadium-bg.jpg')" }}
      />
      {/* Dark brand-tinted overlay for legibility over the bright photo. */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/70 to-black/85" />
      {/* Subtle lime brand wash to match the rest of the app. */}
      <div className="absolute inset-0 bg-[radial-gradient(1200px_600px_at_50%_-10%,rgba(200,240,0,0.08),transparent_60%)]" />
    </div>
  );
}
