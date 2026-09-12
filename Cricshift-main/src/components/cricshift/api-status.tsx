"use client";

import { useHealth } from "@/lib/api/hooks";
import { AlertCircle, WifiOff, Activity } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function ApiStatus() {
  const { data, isError, isLoading } = useHealth();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Activity className="h-3 w-3 animate-pulse" />
        <span>Connecting…</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center gap-2 text-xs text-red-400">
        <WifiOff className="h-3 w-3" />
        <span>API Unavailable — Start the FastAPI backend</span>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-2 text-xs cursor-default">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500/60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <span className="text-emerald-300">API Connected</span>
            {!data.models_loaded && (
              <span className="flex items-center gap-1 text-amber-400">
                <AlertCircle className="h-3 w-3" />
                Models loading
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent
          side="bottom"
          className="bg-black/90 border-white/10"
        >
          <div className="space-y-1 text-xs">
            <div className="font-semibold text-white">{data.service}</div>
            {Object.entries(data.model_status).map(([name, ok]) => (
              <div key={name} className="flex items-center gap-2">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`}
                />
                <span className="text-muted-foreground">{name}</span>
              </div>
            ))}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
