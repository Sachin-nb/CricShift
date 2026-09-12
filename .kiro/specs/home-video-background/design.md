# Design Document

## Overview

This feature adds a looping, muted video background to the home page (`/`) only,
while preserving every existing section and the app's dark emerald/gold look. The
video must cover the **entire scrollable home document** (not just the first
viewport) and must never intercept clicks or scrolling.

The implementation introduces a single, self-contained client component,
`HomeVideoBackground`, rendered as the first child of the home page wrapper. It
renders an absolutely-positioned `<video>` layer that spans the full height of the
home page, plus a tint overlay for legibility. It degrades gracefully to the
existing global `.app-bg` gradient when the video cannot play (reduced motion,
autoplay blocked, load error, or unsupported codec).

No other page is touched. The global `.app-bg` (rendered once in `layout.tsx`,
`position: fixed`, `z-index: -1`) stays in place and naturally serves as the
fallback backdrop for the home page whenever the video is hidden.

### Goals
- Full-scrollable-page video backdrop on `/` only.
- Zero change to home content, layout, links, or behaviour.
- Readable foreground via a tint overlay.
- Graceful, silent fallback to the existing gradient.

### Non-Goals
- No changes to any route other than `/`.
- No sound, controls, or user-facing play/pause.
- Mandatory video re-encoding (optional note only).

## Architecture

### Current state
- `layout.tsx` renders `<div className="app-bg" aria-hidden />` once, behind all
  pages. `.app-bg` is `position: fixed; inset: 0; z-index: -1` in `globals.css`.
- `page.tsx` is a Server Component: `<div className="relative flex min-h-screen
  flex-col">` wrapping Navbar, `<main>` (Hero, Stats, Features, AnalyticsShowcase,
  AiInsight, About, BrandMark), and Footer. The wrapper is transparent.

### Change
- Add `HomeVideoBackground` (a Client Component, `"use client"`) because it needs
  `useState`/`useRef`/`useEffect` for reduced-motion detection and error/fallback
  handling. `page.tsx` remains a Server Component and simply renders the client
  child as its first element — a Server Component may render a Client Component,
  so the page does not need to become a client component.
- The home wrapper already has `position: relative`, so an absolutely-positioned
  background child anchors to it. To cover the **full scrollable page**, the video
  layer uses `position: absolute; inset: 0; height: 100%` against the wrapper,
  and the wrapper's natural content height defines the scroll height. This
  satisfies Requirement 1.4 (spans full document height, not just first viewport).

### Stacking / interaction model
- Wrapper: `position: relative` (unchanged) + add `isolation: isolate` via a
  utility so the background's negative/zero z-index stays scoped to the home tree.
- Video layer: `position: absolute; inset: 0; z-index: 0; pointer-events: none`.
- Tint overlay: sibling above the video, `z-index: 0`, also `pointer-events: none`.
- Content (Navbar/main/Footer): given `position: relative; z-index: 10` wrapper
  context so it always sits above the background. Existing content markup and
  classes are otherwise unchanged.

### Diagram

```
<div class="relative isolate flex min-h-screen flex-col">   (home wrapper)
  <HomeVideoBackground />        (absolute, inset-0, z-0, pointer-events-none)
     |- <video> object-cover, full height, autoplay muted loop playsInline
     |- <div> tint overlay (gradient/dark), pointer-events-none
  <div class="relative z-10 flex flex-1 flex-col">   (content shield)
     <Navbar/> <main>...sections...</main> <Footer/>
  </div>
</div>
```

## Components and Interfaces

### `HomeVideoBackground` (new client component)
Path: `Cricshift-main/src/components/cricshift/home-video-background.tsx`

Responsibilities:
- Render the `<video>` background and tint overlay.
- Decide whether the video should play (respect `prefers-reduced-motion`).
- Hide the video (fall back to gradient) on error or blocked autoplay.

Props: none (self-contained). Internal state only.

Key attributes on the `<video>`:
- `autoPlay muted loop playsInline` — required for silent inline autoplay
  (Requirement 1.2, 5.3). `muted` is set both as attribute and imperatively on
  the ref to maximise autoplay success across browsers.
- `preload="auto"`, `poster="/home-bg-poster.jpg"` if a poster exists, else omit.
- `aria-hidden="true"` (Requirement 5.3) and `tabIndex={-1}`.
- `className` with `object-cover h-full w-full` (Requirement 2.1).
- Source: `<source src="/home-bg.mp4" type="video/mp4" />` (Requirement 6.2).

Behaviour:
- On mount, read `window.matchMedia('(prefers-reduced-motion: reduce)')`.
  - If reduced motion is preferred -> do NOT render/play the video; render nothing
    (or just the poster still), letting `.app-bg` show through (Requirement 5.1).
- Attach `onError` on `<video>`/`<source>` -> set `failed=true` -> unmount the
  video so the gradient shows (Requirement 5.2).
- Attempt `video.play()` in an effect; if the returned promise rejects (autoplay
  blocked) -> set `failed=true` (fall back silently) (Requirement 5.2).
- When not failed and motion allowed, render video + overlay.

Rendering states:
| State | Renders |
|-------|---------|
| Motion allowed, video OK | `<video>` + tint overlay |
| Reduced motion | nothing (gradient shows) or static poster |
| Error / autoplay blocked | nothing (gradient shows) |

### `page.tsx` (edited)
- Add `import { HomeVideoBackground } from "@/components/cricshift/home-video-background";`
- Add `isolate` to the wrapper className.
- Render `<HomeVideoBackground />` as the first child.
- Wrap the existing Navbar/main/Footer in a `relative z-10` container so content
  stays above the background. Section components themselves are NOT modified.

Resulting structure (content unchanged, only wrapped):
```tsx
<div className="relative isolate flex min-h-screen flex-col">
  <HomeVideoBackground />
  <div className="relative z-10 flex flex-1 flex-col">
    <Navbar />
    <main className="flex flex-1 flex-col"> ...same sections... </main>
    <Footer />
  </div>
</div>
```

### Styling approach
- Use Tailwind utility classes already used across the app (object-cover, inset-0,
  absolute, pointer-events-none, z-0/z-10, h-full, w-full).
- Tint overlay: a dark gradient consistent with the brand, e.g.
  `bg-gradient-to-b from-background/70 via-background/60 to-background/80`, tuned
  during implementation for contrast (Requirement 3.2, 3.3). `pointer-events-none`.
- No change to `globals.css` is required; `.app-bg` remains the fallback. A small
  optional addition may be made only if a non-Tailwind rule proves necessary.

## Data Models

None. This is a purely presentational, client-side feature with no data,
props, or persistence.

## Asset Handling

- Source video (user machine, name has spaces + emoji) is copied to
  `Cricshift-main/public/home-bg.mp4` (URL-safe ASCII) during implementation via a
  terminal `Copy-Item` (Requirement 6.1). Served at `/home-bg.mp4` (Requirement 6.2).
- Optional: an poster frame `public/home-bg-poster.jpg` for instant first paint
  (Requirement 4.2). If not produced, the `.app-bg` gradient covers the pre-play
  moment, which also satisfies "no blank/black flash".
- Optional compression note (Requirement 6.3): if `home-bg.mp4` is large (e.g.
  > ~15-20 MB) it may be transcoded to a smaller web-optimised MP4/H.264; not
  mandatory. File size will be checked after copy.

## Error Handling

- **Autoplay blocked**: `video.play()` promise rejects -> mark failed -> gradient
  fallback, no error surfaced to the user (Requirement 5.2).
- **Load/codec error**: `<video onError>` -> mark failed -> gradient fallback.
- **Reduced motion**: never start playback; show gradient/poster (Requirement 5.1).
- **Missing file**: behaves as a load error -> gradient fallback; page remains
  fully functional (Requirement 4.3).
- Content is never gated on the video: the home sections render and are
  interactive regardless of video state (Requirement 4.3, 2.3).

## Testing Strategy

Because this is a visual/client-only change in a Next.js app, verification is
primarily type-check + manual visual QA:

1. **Type check / build**: `cd "d:\cricket-analytics (2)\Cricshift-main"; npx tsc --noEmit`
   -> expect 0 errors. Optionally `npm run build` for the home route.
2. **Home page manual QA** (`/`):
   - Video autoplays, is muted, loops, and covers the full scrollable page while
     scrolling top-to-bottom (no seams/gaps) (Req 1, 2).
   - All sections present, in order, unchanged; text/cards readable over video
     (Req 3).
   - Clicks, links, hover, and scroll all work (video does not block) (Req 2.3).
   - Resize browser (narrow mobile -> ultrawide): no black bars (Req 2.2).
3. **Other routes** (`/live`, `/dashboard`, `/admin`, `/login`): background
   unchanged, no video (Req 1.3).
4. **Reduced motion**: enable OS "reduce motion" -> no video, gradient shows (Req 5.1).
5. **Fallback**: temporarily point to a missing file / simulate error -> gradient
   shows, page still works (Req 5.2).


## Correctness Properties

These invariants must hold for any correct implementation:

### Property 1: Home-only presence
The video background element exists in the DOM for `/` and for no other route.

**Validates: Requirements 1.1, 1.3**

### Property 2: Behind everything
The video and overlay always have a lower stacking order than all home content;
content is never visually obscured by the background.

**Validates: Requirements 2.3, 3.1**

### Property 3: Non-interactive background
The video and overlay never receive pointer or keyboard interaction
(`pointer-events: none`, `tabIndex = -1`, `aria-hidden`). Every pre-existing
interactive element remains reachable and functional.

**Validates: Requirements 2.3, 3.4, 5.3**

### Property 4: Full coverage
At every viewport size and scroll position within the home page, the visible
background is fully covered by video (when playing) or the gradient fallback —
never a black bar, gap, or seam.

**Validates: Requirements 1.4, 2.1, 2.2**

### Property 5: Content invariance
The set, order, content, and layout of home sections are identical before and
after the change; only the backdrop differs.

**Validates: Requirements 3.1, 3.4**

### Property 6: Silent muted playback
When the video plays it is always muted and loops; it never emits audio and never
stops on its own.

**Validates: Requirements 1.2, 5.3**

### Property 7: Graceful degradation
If reduced motion is preferred, or playback is blocked, or the source errors, the
video is absent and the existing gradient shows, with no visible error and a fully
functional page.

**Validates: Requirements 4.3, 5.1, 5.2**

### Property 8: Static local asset
The video is loaded only from the app own `public/` path (`/home-bg.mp4`), never
from an external runtime source.

**Validates: Requirements 4.1, 6.1, 6.2**

## Design Decisions and Rationale

- **Separate client component vs. making page.tsx a client component**: keeping a
  small `HomeVideoBackground` client component lets `page.tsx` stay a Server
  Component, minimising the client bundle and keeping the change isolated.
- **Absolute (full-page) vs. fixed (viewport-pinned)**: the user explicitly chose
  "cover the whole scrollable page", so the video layer spans the full document
  height via `absolute inset-0 h-full` inside the relative wrapper, rather than
  `position: fixed`.
- **Reuse existing `.app-bg` as fallback**: avoids new fallback styling and
  guarantees visual consistency with the rest of the app when the video is hidden.
- **Tint overlay with Tailwind tokens**: keeps brand consistency and readability
  without touching section components (Req 3).
- **Copy to `public/home-bg.mp4`**: the original filename has spaces + emoji that
  break URLs; a clean static asset path is required (Req 6).



