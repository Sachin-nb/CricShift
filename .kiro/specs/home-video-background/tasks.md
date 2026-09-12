# Implementation Plan

- [x] 1. Copy the source video into the app public folder as a clean asset
  - Copy the user-supplied video from its Downloads path to
    `Cricshift-main/public/home-bg.mp4` (URL-safe ASCII name) using a terminal
    `Copy-Item` command.
  - Verify the file exists at `Cricshift-main/public/home-bg.mp4` and report its
    size (to decide whether the optional compression note applies).
  - _Requirements: 6.1, 6.2, 6.3, 4.1_

- [x] 2. Create the HomeVideoBackground client component
  - Add `Cricshift-main/src/components/cricshift/home-video-background.tsx` with
    the `"use client"` directive.
  - Render an absolutely-positioned `<video>` layer (`absolute inset-0 h-full
    w-full object-cover -z-... /z-0`, `pointer-events-none`, `aria-hidden`,
    `tabIndex={-1}`) with `autoPlay muted loop playsInline preload="auto"` and a
    `<source src="/home-bg.mp4" type="video/mp4" />`.
  - Render a brand-tinted dark gradient overlay sibling above the video
    (`pointer-events-none`) for legibility.
  - _Requirements: 1.1, 1.2, 2.1, 2.3, 3.2, 3.3, 5.3_

- [x] 2.1 Add reduced-motion, autoplay, and error fallback logic
  - On mount detect `prefers-reduced-motion: reduce`; when set, do not play/render
    the video so the existing `.app-bg` gradient shows.
  - Set `muted` imperatively on the ref and attempt `video.play()`; on promise
    rejection (autoplay blocked) mark failed and hide the video.
  - Add `onError` on the video/source to mark failed and hide the video.
  - When failed or reduced-motion, render nothing (gradient fallback), keeping the
    page fully functional.
  - _Requirements: 4.2, 4.3, 5.1, 5.2_

- [x] 3. Wire the background into the home page only
  - Edit `Cricshift-main/src/app/page.tsx`: import `HomeVideoBackground`, add
    `isolate` to the existing wrapper `div`, render `<HomeVideoBackground />` as
    its first child, and wrap the existing Navbar/main/Footer in a
    `relative z-10` container so content stays above the background.
  - Do NOT modify any section component (Navbar, Hero, Stats, Features,
    AnalyticsShowcase, AiInsight, About, BrandMark, Footer) — content, order, and
    layout remain identical.
  - Confirm no other route/page is touched (background stays unchanged elsewhere).
  - _Requirements: 1.1, 1.3, 1.4, 2.3, 3.1, 3.4_

- [x] 4. Verify build and behaviour
  - Run `cd "d:\cricket-analytics (2)\Cricshift-main"; npx tsc --noEmit` and
    resolve any type errors introduced by the change (expect 0 errors).
  - Manually QA the home page: video autoplays muted, loops, covers the full
    scrollable page with no seams; all sections present and readable; clicks,
    links, hover, and scroll work; resize shows no black bars.
  - Confirm other routes (`/live`, `/dashboard`, `/admin`, `/login`) keep their
    current background; confirm reduced-motion and error fallbacks show the
    gradient with a functional page.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.1, 3.4, 4.3, 5.1, 5.2_

