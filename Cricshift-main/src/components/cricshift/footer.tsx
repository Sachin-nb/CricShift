"use client";

import {
  ArrowRight,
  Github,
  Linkedin,
  Mail,
  FileText,
} from "lucide-react";
import { Reveal } from "./reveal";

const QUICK_LINKS: { label: string; href: string }[] = [
  { label: "Home", href: "#home" },
  { label: "Features", href: "#features" },
  { label: "Analytics", href: "#analytics" },
  { label: "About", href: "#about" },
  { label: "Contact", href: "#contact" },
];

const RESOURCES: { label: string; href: string }[] = [
  { label: "Research Paper", href: "#" },
  { label: "Documentation", href: "#" },
  { label: "GitHub", href: "#" },
];

const SOCIALS: { label: string; href: string; icon: typeof Github }[] = [
  { label: "GitHub", href: "#", icon: Github },
  { label: "LinkedIn", href: "#", icon: Linkedin },
  { label: "Email", href: "mailto:crickshift@research.dev", icon: Mail },
  { label: "Paper", href: "#", icon: FileText },
];

export function Footer() {
  return (
    <footer
      id="contact"
      className="relative mt-auto overflow-hidden border-t border-white/5 bg-black/50 backdrop-blur-sm"
    >
      {/* Top gradient hairline */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />

      {/* Background flourish: faint grid + pitch-line at bottom */}
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.18]" />
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-40"
        style={{
          background:
            "radial-gradient(ellipse 80% 100% at 50% 100%, rgba(0,200,83,0.10), transparent 70%)",
        }}
      />
      {/* Pitch line decoration */}
      <div
        className="pointer-events-none absolute bottom-0 left-1/2 h-24 w-[80%] -translate-x-1/2 opacity-[0.12]"
        style={{
          background:
            "linear-gradient(180deg, transparent, rgba(0,200,83,0.18))",
          clipPath: "polygon(40% 0, 60% 0, 92% 100%, 8% 100%)",
        }}
      />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* CTA band */}
        <Reveal y={24}>
          <div className="glass-strong relative -mt-px overflow-hidden rounded-2xl px-6 py-8 sm:px-10 sm:py-10 md:px-14">
            {/* glow accents */}
            <div
              className="pointer-events-none absolute -left-20 -top-20 h-64 w-64 rounded-full"
              style={{
                background:
                  "radial-gradient(circle, rgba(0,200,83,0.22), transparent 70%)",
              }}
            />
            <div
              className="pointer-events-none absolute -bottom-24 -right-16 h-64 w-64 rounded-full"
              style={{
                background:
                  "radial-gradient(circle, rgba(255,193,7,0.18), transparent 70%)",
              }}
            />

            <div className="relative flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
              <div className="max-w-2xl">
                <p className="text-xs font-medium uppercase tracking-[0.22em] text-emerald-300/90">
                  See it in action
                </p>
                <h3 className="mt-3 text-balance text-2xl font-bold leading-tight text-white sm:text-3xl md:text-4xl">
                  Ready to see the moment the{" "}
                  <span className="text-gradient-emerald">match changed?</span>
                </h3>
              </div>
              <a
                href="#analytics"
                className="group inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-emerald-400 to-emerald-600 px-7 text-sm font-semibold text-black shadow-[0_0_30px_-6px_rgba(0,200,83,0.55)] transition-all duration-300 hover:from-emerald-300 hover:to-emerald-500 hover:shadow-[0_0_44px_-4px_rgba(0,200,83,0.7)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#070707]"
              >
                Explore Demo
                <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
              </a>
            </div>
          </div>
        </Reveal>

        {/* Main footer grid */}
        <div className="grid grid-cols-2 gap-10 py-14 sm:gap-8 lg:grid-cols-4 lg:py-20">
          {/* Column 1 — Brand */}
          <div className="col-span-2 sm:col-span-2 lg:col-span-1">
            <a href="#home" className="inline-flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-lg shadow-[0_0_22px_-4px_rgba(0,200,83,0.6)]">
                🏏
              </span>
              <span className="text-lg font-bold tracking-tight text-white">
                Cric<span className="text-gradient-emerald">Shift</span>
              </span>
            </a>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              AI-powered momentum shift detection &amp; win probability
              prediction for the next generation of cricket analysis.
            </p>
            <div className="mt-5 flex items-center gap-2">
              {SOCIALS.map((s) => (
                <a
                  key={s.label}
                  href={s.href}
                  aria-label={s.label}
                  className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-muted-foreground transition-all duration-300 hover:-translate-y-0.5 hover:border-emerald-500/40 hover:text-emerald-300"
                >
                  <s.icon className="h-[18px] w-[18px]" strokeWidth={1.75} />
                </a>
              ))}
            </div>
          </div>

          {/* Column 2 — Quick Links */}
          <nav aria-label="Quick Links" className="flex flex-col gap-3">
            <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-white/80">
              Quick Links
            </h4>
            <ul className="flex flex-col gap-1">
              {QUICK_LINKS.map((l) => (
                <li key={l.label}>
                  <a
                    href={l.href}
                    className="inline-flex min-h-[28px] items-center text-sm text-muted-foreground transition-colors duration-200 hover:text-emerald-300"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          {/* Column 3 — Resources */}
          <nav aria-label="Resources" className="flex flex-col gap-3">
            <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-white/80">
              Resources
            </h4>
            <ul className="flex flex-col gap-1">
              {RESOURCES.map((l) => (
                <li key={l.label}>
                  <a
                    href={l.href}
                    className="inline-flex min-h-[28px] items-center text-sm text-muted-foreground transition-colors duration-200 hover:text-amber-300"
                  >
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          {/* Column 4 — Contact */}
          <div className="col-span-2 flex flex-col gap-3 sm:col-span-2 lg:col-span-1">
            <h4 className="text-xs font-semibold uppercase tracking-[0.2em] text-white/80">
              Contact
            </h4>
            <ul className="flex flex-col gap-2">
              <li>
                <a
                  href="mailto:crickshift@research.dev"
                  className="inline-flex min-h-[28px] items-center gap-2 text-sm text-muted-foreground transition-colors duration-200 hover:text-emerald-300"
                >
                  <Mail className="h-4 w-4 text-emerald-400/80" strokeWidth={1.75} />
                  crickshift@research.dev
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="inline-flex min-h-[28px] items-center gap-2 text-sm text-muted-foreground transition-colors duration-200 hover:text-emerald-300"
                >
                  <Linkedin className="h-4 w-4 text-emerald-400/80" strokeWidth={1.75} />
                  LinkedIn
                </a>
              </li>
            </ul>
            <p className="mt-3 text-[11px] leading-relaxed text-muted-foreground/70">
              Made with{" "}
              <span className="text-emerald-400">ML</span> &amp;{" "}
              <span className="text-amber-400">cricket love</span> ✦
            </p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col items-center justify-between gap-4 border-t border-white/[0.06] py-6 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © 2025 CricShift. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a
              href="#"
              className="inline-flex min-h-[28px] items-center text-xs text-muted-foreground transition-colors duration-200 hover:text-emerald-300"
            >
              Privacy
            </a>
            <a
              href="#"
              className="inline-flex min-h-[28px] items-center text-xs text-muted-foreground transition-colors duration-200 hover:text-emerald-300"
            >
              Terms
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
