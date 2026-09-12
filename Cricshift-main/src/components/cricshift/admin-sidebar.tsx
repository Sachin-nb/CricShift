"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAdminStats } from "@/lib/api/admin";
import {
  LayoutDashboard, Activity, Zap, BarChart2, ArrowLeft,
} from "lucide-react";

const routes = [
  { href: "/admin",             label: "Overview",      icon: LayoutDashboard },
  { href: "/admin/matches",     label: "Live Matches",  icon: Activity        },
  { href: "/admin/simulations", label: "Simulations",   icon: Zap             },
  { href: "/admin/analyses",    label: "Analyses",      icon: BarChart2       },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const { data: stats } = useAdminStats();

  const statBubbles = [
    { href: "/admin/matches",     val: stats?.total_live_matches, color: "text-emerald-400" },
    { href: "/admin/simulations", val: stats?.total_simulations,  color: "text-amber-400"   },
    { href: "/admin/analyses",    val: stats?.total_predictions,  color: "text-blue-400"    },
    { href: "/admin/analyses",    val: undefined,                 color: ""                  },
  ];

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-white/10 bg-white/[0.03] backdrop-blur-xl">
      {/* Brand */}
      <div className="flex h-16 items-center gap-3 border-b border-white/10 px-6">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-lg shadow-[0_0_20px_rgba(0,200,83,0.5)]">
          🏏
        </span>
        <h2 className="text-base font-bold tracking-tight text-white">
          Cric<span className="text-gradient-emerald">Shift</span>{" "}
          <span className="text-[11px] font-semibold uppercase tracking-widest text-amber-400/80">
            Admin
          </span>
        </h2>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1.5 overflow-y-auto px-3 py-5">
        {routes.map((route, i) => {
          const isActive = pathname === route.href ||
            (route.href !== "/admin" && pathname.startsWith(route.href));
          const Icon = route.icon;
          const bubble = statBubbles[i];

          return (
            <Link
              key={route.href}
              href={route.href}
              className={`group relative flex items-center justify-between rounded-xl px-3 py-2.5 transition-all ${
                isActive
                  ? "bg-emerald-500/12 text-emerald-300"
                  : "text-zinc-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              {/* Active accent bar */}
              {isActive && (
                <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-gradient-to-b from-emerald-400 to-emerald-600" />
              )}
              <span className="flex items-center gap-3">
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-emerald-400" : ""}`} />
                <span className="text-sm font-medium">{route.label}</span>
              </span>
              {bubble.val !== undefined && (
                <span
                  className={`min-w-[26px] rounded-md border border-white/5 bg-black/30 px-1.5 py-0.5 text-center text-xs font-bold tabular-nums ${bubble.color}`}
                >
                  {bubble.val}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="space-y-2.5 border-t border-white/10 p-3">
        {/* Today quick-stats */}
        {stats && (
          <div className="rounded-xl border border-white/8 bg-white/[0.03] px-3.5 py-3">
            <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
              Today
            </p>
            <div className="grid grid-cols-2 gap-y-1.5 text-xs">
              <span className="text-zinc-400">Matches</span>
              <span className="text-right font-semibold tabular-nums text-emerald-400">
                {stats.live_matches_today}
              </span>
              <span className="text-zinc-400">Predictions</span>
              <span className="text-right font-semibold tabular-nums text-blue-400">
                {stats.predictions_today}
              </span>
              <span className="text-zinc-400">Simulations</span>
              <span className="text-right font-semibold tabular-nums text-amber-400">
                {stats.simulations_today}
              </span>
            </div>
          </div>
        )}

        {/* Engine status */}
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-2.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="flex-1 text-xs font-medium text-emerald-300">Engine Online</span>
        </div>

        {/* Back to app */}
        <Link
          href="/"
          className="flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-zinc-500 transition-colors hover:bg-white/5 hover:text-zinc-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to App
        </Link>
      </div>
    </aside>
  );
}
