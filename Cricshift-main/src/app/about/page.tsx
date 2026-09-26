"use client";

import { motion } from "framer-motion";
import { PageShell } from "@/components/cricshift/page-shell";
import { Card } from "@/components/cricshift/card";
import { Info, Github, Twitter, BarChart2, Activity } from "lucide-react";

export default function AboutPage() {
  return (
    <PageShell
      eyebrow="About CricShift"
      eyebrowIcon={Info}
      title="The Future of"
      titleAccent="Cricket Analytics"
      subtitle="CricShift is a next-generation platform designed to detect momentum shifts and predict win probabilities in T20 cricket matches using advanced Machine Learning models."
      centered
      maxWidth="4xl"
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid gap-8 md:grid-cols-2"
      >
        <Card hover className="p-8">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/20 text-amber-400">
            <Activity className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Momentum Detection</h3>
          <p className="text-muted-foreground leading-relaxed">
            We move beyond simple run rates. Our LightGBM models analyze pressure index, boundary frequency, and wicket clusters to quantify exactly when match momentum shifts from one team to another.
          </p>
        </Card>

        <Card hover className="p-8">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
            <BarChart2 className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Win Prediction</h3>
          <p className="text-muted-foreground leading-relaxed">
            By training on over 2,000 historical T20 matches, our XGBoost win predictor evaluates the exact match situation—accounting for venue averages, chasing pressure, and remaining batting depth.
          </p>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-8"
      >
        <Card className="p-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Phase 5C Architecture</h2>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Built with a high-performance FastAPI backend for ML inference and a sleek Next.js App Router frontend. We integrate with live sports APIs to bring machine learning insights to live matches as they happen.
          </p>

          <div className="flex justify-center gap-4">
            <a href="https://github.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-white/10 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/20 transition-colors">
              <Github className="h-4 w-4" />
              View Source
            </a>
            <a href="https://twitter.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-emerald-500/10 px-5 py-2.5 text-sm font-medium text-emerald-400 hover:bg-emerald-500/20 transition-colors">
              <Twitter className="h-4 w-4" />
              Follow Updates
            </a>
          </div>
        </Card>
      </motion.div>
    </PageShell>
  );
}
