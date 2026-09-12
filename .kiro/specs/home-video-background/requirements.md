# Requirements Document

## Introduction

The home page (`/`) currently shows content over a shared, brand-tinted gradient
background (`.app-bg`, rendered once in the root layout for all pages). This
feature replaces that flat background with a looping full-screen video on the
home page only. All existing home-page content (Navbar, Hero, Stats, Features,
Analytics Showcase, AI Insight, About, BrandMark, Footer) must remain exactly as
it is today — only the backdrop changes.

The user has supplied a source video located on their machine (its filename
contains spaces and emoji). It will be copied into the Next.js `public/` folder
under a clean, ASCII filename (e.g. `home-bg.mp4`) and served as a static asset.

## Glossary

- **Home page**: the route `/`, rendered by `Cricshift-main/src/app/page.tsx`.
- **app-bg**: the shared gradient background element rendered once in the root
  layout (`layout.tsx`) behind every page.
- **Video background layer**: a full-screen `<video>` element placed behind the
  home-page content, showing the supplied clip.
- **Overlay**: a semi-transparent tint placed between the video and the content
  to keep foreground text/cards legible.
- **Poster**: a static image shown before/while the video loads, or as a
  reduced-motion / fallback still.
- **object-fit: cover**: CSS that scales media to fill its box while preserving
  aspect ratio, cropping any overflow (no stretching or letterboxing).

## Requirements

### Requirement 1: Video background on the home page only

**User Story:** As a visitor landing on the home page, I want a cinematic cricket
video playing behind the content, so the landing experience feels premium.

#### Acceptance Criteria
1. WHEN a user opens the home page (`/`) THEN the system SHALL display the supplied
   video as a full-screen background layer behind all page content.
2. WHEN the home page renders THEN the video SHALL autoplay, loop continuously,
   play muted, and play inline (no fullscreen takeover on mobile).
3. WHEN the user navigates to any other route (e.g. `/live`, `/dashboard`,
   `/admin`, `/login`) THEN the video SHALL NOT appear and those pages SHALL keep
   their current background unchanged.
4. WHERE the page is scrolled, the video SHALL cover the entire scrollable home
   page (spanning the full document height, not just the first viewport), with no
   gaps, black bars, or repeated seams.

### Requirement 2: Perfect fit at any screen size

**User Story:** As a user on any device, I want the video to fill the screen
cleanly, so it never looks stretched, letter-boxed, or leaves empty bars.

#### Acceptance Criteria
1. WHEN displayed on any viewport (mobile, tablet, desktop, ultrawide) THEN the
   video SHALL cover the whole background area using `object-fit: cover`
   (crop-to-fill), preserving aspect ratio without distortion.
2. WHEN the window is resized THEN the video SHALL keep filling the background with
   no black bars or gaps.
3. THE video layer SHALL sit strictly behind all content and SHALL NOT intercept
   clicks, hovers, or scrolling (`pointer-events: none`).

### Requirement 3: Content preserved and readable

**User Story:** As a user, I want all existing home sections and text to remain
fully visible and legible over the video.

#### Acceptance Criteria
1. WHEN the home page renders over the video THEN every existing section (Navbar,
   Hero, Stats, Features, Analytics Showcase, AI Insight, About, BrandMark,
   Footer) SHALL remain present, in the same order, with identical content/layout.
2. WHERE bright video frames would reduce readability, the system SHALL place a
   darkening/tint overlay between the video and the content to preserve contrast.
3. THE overlay SHALL preserve the project dark, emerald/gold-accented look
   (it MAY reuse or blend the existing gradient over the video).
4. THE change SHALL be visual only — no home-page data, links, or behaviour altered.

### Requirement 4: Performance

**User Story:** As a user, I want the page to stay fast even with a video
background.

#### Acceptance Criteria
1. THE video SHALL be served as a static asset from the app `public/` folder
   (not fetched from an external service at runtime).
2. WHEN the page loads THEN a poster image or the existing gradient SHALL show
   immediately while the video buffers, avoiding a blank/black flash.
3. THE video SHALL NOT block rendering of home-page content (content is
   interactive regardless of video load state).

### Requirement 5: Accessibility and graceful fallback

**User Story:** As a user with reduced-motion preferences or an unsupported/slow
environment, I want a calm, working page rather than a broken or distracting one.

#### Acceptance Criteria
1. WHEN the system preference is `prefers-reduced-motion: reduce` THEN the video
   SHALL NOT autoplay and a static fallback (poster or existing gradient) SHALL show.
2. IF the browser cannot play the video (unsupported codec, blocked autoplay, or
   load error) THEN the system SHALL fall back to the existing gradient with no
   visible error.
3. THE background video SHALL be decorative — marked so assistive tech ignores it
   (`aria-hidden`) and muted so it never plays audio.

### Requirement 6: Asset handling

**User Story:** As the developer, I want the supplied video usable via a clean URL.

#### Acceptance Criteria
1. THE supplied video file SHALL be copied into `Cricshift-main/public/` under a
   URL-safe ASCII filename (no spaces or emoji), e.g. `home-bg.mp4`.
2. THE app SHALL reference the video by its public path (e.g. `/home-bg.mp4`).
3. IF the file is large enough to harm load time, the design phase SHALL note
   optional compression; otherwise the original MAY be used as-is.

### Requirement 7: Out of scope guardrails

**User Story:** As a stakeholder, I want the change tightly scoped so nothing else
regresses.

#### Acceptance Criteria
1. THE system SHALL NOT change the background of any page other than the home page.
2. THE system SHALL NOT add sound, video controls, or a user-facing play/pause.
3. THE system SHALL NOT require re-encoding/compression (optional only).
4. THE system SHALL NOT alter home-page content, copy, layout, or functionality.


