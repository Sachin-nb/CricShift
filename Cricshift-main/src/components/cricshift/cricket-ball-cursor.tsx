"use client";

import { useEffect, useRef } from "react";

/**
 * CricketBallCursor
 * ------------------
 * Replaces the native mouse cursor with a realistic 3D red leather cricket ball.
 *
 * Implementation notes (HTML/CSS/vanilla JS, no external libraries):
 * - The ball is rendered with layered CSS radial-gradients (glossy red body, fixed
 *   top-left highlight, bottom-right shading) + a raised white stitched seam band.
 * - A requestAnimationFrame loop eases the ball toward the mouse for a premium,
 *   slightly-trailing feel and drives a rolling/spinning animation by accumulating
 *   a rotation angle from cursor movement (only the seam rotates — lighting stays
 *   fixed to the world, which is what sells the realistic 3D roll).
 * - Hover over interactive elements (a, button, inputs, [role=button], .group,
 *   [data-cursor=hover]) enlarges the ball ~1.2×.
 * - Clicking briefly compresses the ball to 0.9× and spawns a gold ripple at the
 *   click point.
 * - pointer-events:none on the root means it never interferes with clicks, hover,
 *   or text selection. The native cursor is hidden globally via a class on <html>.
 * - Desktop-only: the element is always rendered but stays off-screen/transparent
 *   until a fine pointer is detected and the first mousemove occurs. On touch /
 *   coarse-pointer devices the effect returns early and nothing is shown.
 * - 60 FPS via rAF + transform/translate3d (GPU-accelerated, no layout thrash).
 */
export function CricketBallCursor() {
  const rootRef = useRef<HTMLDivElement>(null);
  const seamRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only activate on precise-pointer (desktop) devices.
    const finePointer =
      window.matchMedia("(pointer: fine)").matches &&
      !window.matchMedia("(any-pointer: coarse)").matches;
    if (!finePointer) return;

    const root = rootRef.current;
    const seam = seamRef.current;
    if (!root || !seam) return;

    document.documentElement.classList.add("has-custom-cursor");

    // --- State (kept in plain vars for the rAF loop — no React re-renders) ---
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let curX = mouseX;
    let curY = mouseY;
    let prevX = curX;
    let prevY = curY;
    let roll = 0; // accumulated seam rotation in degrees
    let raf = 0;
    let visible = false;

    // --- Listeners ---
    const onMove = (e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (!visible) {
        visible = true;
        root.classList.add("cbc-visible");
        // Snap to cursor on first move so the ball doesn't fly in from center.
        curX = prevX = mouseX;
        curY = prevY = mouseY;
      }
    };

    // Detect hovering interactive elements for the 1.2× enlarge.
    const onOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      const interactive = !!target?.closest(
        "a, button, [role='button'], input, textarea, select, label, summary, .group, [data-cursor='hover']",
      );
      root.classList.toggle("cbc-hover", interactive);
    };

    // Click: compress + ripple.
    const onDown = (e: MouseEvent) => {
      root.classList.add("cbc-click");
      spawnRipple(e.clientX, e.clientY);
    };
    const onUp = () => {
      root.classList.remove("cbc-click");
    };

    // Spawn a gold impact ripple at the click point.
    const spawnRipple = (x: number, y: number) => {
      const r = document.createElement("div");
      r.className = "cbc-ripple";
      r.style.left = `${x}px`;
      r.style.top = `${y}px`;
      document.body.appendChild(r);
      // Remove after the animation finishes.
      r.addEventListener("animationend", () => r.remove(), { once: true });
      // Fallback cleanup in case the event doesn't fire.
      window.setTimeout(() => r.remove(), 700);
    };

    // --- Animation loop (60 FPS, eased follow + rolling seam) ---
    const loop = () => {
      // Ease the ball toward the mouse (lerp). 0.2 ≈ smooth premium trailing.
      curX += (mouseX - curX) * 0.2;
      curY += (mouseY - curY) * 0.2;

      // Movement since last frame → drives the rolling spin.
      const dx = curX - prevX;
      const dy = curY - prevY;
      prevX = curX;
      prevY = curY;

      // Accumulate roll. Horizontal motion dominates the visual "roll" of a ball;
      // a smaller vertical contribution keeps diagonal motion believable.
      // Moving right / down rolls clockwise (positive CSS rotation).
      roll += dx * 2.2 + dy * 0.6;

      // Position the root (centered via negative margin in CSS).
      root.style.transform = `translate3d(${curX}px, ${curY}px, 0)`;
      // Spin only the seam — lighting on the ball stays world-fixed.
      seam.style.transform = `translateY(-50%) rotate(${roll}deg)`;

      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    window.addEventListener("mousemove", onMove, { passive: true });
    window.addEventListener("mouseover", onOver, { passive: true });
    window.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseover", onOver);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      document.documentElement.classList.remove("has-custom-cursor");
    };
  }, []);

  // Always rendered; stays off-screen + transparent until the effect activates it
  // on a fine-pointer device (so SSR markup is identical to first client render).
  return (
    <div ref={rootRef} className="cbc-root" aria-hidden="true">
      <div className="cbc-inner">
        <div className="cbc-shadow" />
        <div className="cbc-ball">
          <div ref={seamRef} className="cbc-seam" />
        </div>
      </div>
    </div>
  );
}
