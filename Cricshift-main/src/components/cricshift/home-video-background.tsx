"use client";

import { useEffect, useRef, useState } from "react";

/**
 * HomeVideoBackground
 *
 * Fixed, viewport-pinned, looping, muted video backdrop for the home page ONLY.
 * - Uses `fixed inset-0` so the video stays pinned to the viewport as the page
 *   scrolls (cinematic backdrop), rather than scrolling away with the content.
 * - Mounted only by the home page, so it unmounts on navigation to other routes.
 * - Sits strictly behind content and never intercepts pointer / scroll events.
 * - Respects `prefers-reduced-motion` and silently falls back to the global
 *   `.app-bg` gradient on reduced-motion, blocked autoplay, or load error.
 *
 * Decorative only: aria-hidden + muted, so assistive tech ignores it and it
 * never emits audio.
 */
export function HomeVideoBackground() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  // Start hidden; only reveal once we know motion is allowed AND the browser
  // actually begins playing. This prevents any black flash before load.
  const [show, setShow] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    // Respect reduced-motion: do not play or reveal the video.
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (prefersReduced) {
      setFailed(true);
      return;
    }

    const video = videoRef.current;
    if (!video) return;

    // Ensure muted for autoplay policies across browsers.
    video.muted = true;

    const handlePlaying = () => setShow(true);
    const handleError = () => setFailed(true);

    video.addEventListener("playing", handlePlaying);
    video.addEventListener("error", handleError);

    // Attempt playback; if autoplay is blocked, fall back silently.
    const attempt = video.play();
    if (attempt && typeof attempt.then === "function") {
      attempt.catch(() => setFailed(true));
    }

    return () => {
      video.removeEventListener("playing", handlePlaying);
      video.removeEventListener("error", handleError);
    };
  }, []);

  // On reduced-motion / error / blocked autoplay, render nothing so the global
  // `.app-bg` gradient (rendered once in layout.tsx) shows through.
  if (failed) return null;

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      <video
        ref={videoRef}
        className={`h-full w-full object-cover transition-opacity duration-700 ${
          show ? "opacity-100" : "opacity-0"
        }`}
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
        tabIndex={-1}
        onError={() => setFailed(true)}
      >
        <source src="/home-bg.mp4" type="video/mp4" />
      </video>

      {/* Brand-tinted dark overlay for legibility over bright video frames. */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-black/75 via-black/60 to-black/85" />
      {/* Subtle emerald/lime brand wash to match the rest of the app. */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(1200px_600px_at_50%_-10%,rgba(0,200,83,0.10),transparent_60%)]" />
    </div>
  );
}
