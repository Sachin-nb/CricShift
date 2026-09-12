import { HomeVideoBackground } from "@/components/cricshift/home-video-background";
import { Navbar } from "@/components/cricshift/navbar";
import { Hero } from "@/components/cricshift/hero";
import { Stats } from "@/components/cricshift/stats";
import { Features } from "@/components/cricshift/features";
import { AnalyticsShowcase } from "@/components/cricshift/analytics-showcase";
import { AiInsight } from "@/components/cricshift/ai-insight";
import { About } from "@/components/cricshift/about";
import { BrandMark } from "@/components/cricshift/brand-mark";
import { Footer } from "@/components/cricshift/footer";

export default function Home() {
  return (
    <div className="relative flex min-h-screen flex-col">
      {/* Viewport-pinned looping video backdrop (home page only). */}
      <HomeVideoBackground />
      {/* Content shield: keeps all existing sections above the background. */}
      <div className="relative z-10 flex flex-1 flex-col">
        <Navbar />
        <main className="flex flex-1 flex-col">
          <Hero />
          <Stats />
          <Features />
          <AnalyticsShowcase />
          <AiInsight />
          <About />
          <BrandMark />
        </main>
        <Footer />
      </div>
    </div>
  );
}
