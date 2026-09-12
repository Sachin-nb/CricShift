import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { CricketBallCursor } from "@/components/cricshift/cricket-ball-cursor";
import { SiteBackground } from "@/components/cricshift/site-background";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CricShift — AI-Powered Cricket Analytics & Momentum Detection",
  description:
    "CricShift detects the moment cricket changed forever. AI-powered momentum shift detection and win probability prediction using machine learning and ball-by-ball analytics.",
  keywords: [
    "CricShift",
    "cricket analytics",
    "AI cricket",
    "momentum shift",
    "win probability",
    "machine learning",
    "sports tech",
    "predictive analytics",
  ],
  authors: [{ name: "CricShift Team" }],
  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },
  openGraph: {
    title: "CricShift — AI-Powered Cricket Analytics",
    description:
      "Detect the moment cricket changed forever. AI-powered momentum shift detection and win probability prediction.",
    siteName: "CricShift",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "CricShift — AI-Powered Cricket Analytics",
    description:
      "Detect the moment cricket changed forever. AI-powered momentum shift detection and win probability prediction.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased text-foreground overflow-x-hidden`}
      >
        {/* Global smooth brand-tinted background rendered once behind all pages.
            Serves as the base / fallback (and stays on the home page behind its video). */}
        <div className="app-bg" aria-hidden="true" />
        {/* Stadium photo backdrop for every page except the home page. */}
        <SiteBackground />
        <Providers>
          {children}
          <Toaster />
          <CricketBallCursor />
        </Providers>
      </body>
    </html>
  );
}
