"use client";

import { useEffect } from "react";

/** Gala palette — metal gold + division planes, not party-rainbow. */
const PALETTE = [
  "#f0d078",
  "#d4a84b",
  "#e8c56a",
  "#3d9b7a",
  "#5b7fb5",
  "#f4f1ea",
];

const DURATION_MS = 5000;

function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Celebration burst for season browse surfaces (home, year hub, awards catalogue).
 * Plays on every visit / reload of those pages. Skipped when reduced motion is on.
 */
export function ConfettiSplash() {
  useEffect(() => {
    if (prefersReducedMotion()) return;

    const root = document.createElement("div");
    root.setAttribute("aria-hidden", "true");
    root.dataset.confettiSplash = "1";
    root.style.cssText = [
      "position:fixed",
      "inset:0",
      "z-index:9999",
      "pointer-events:none",
      "overflow:hidden",
    ].join(";");

    const style = document.createElement("style");
    style.textContent = `
      @keyframes awards-confetti-burst {
        0% {
          transform: translate(-50%, -50%) scale(0.35) rotate(0deg);
          opacity: 0;
        }
        8% {
          opacity: 1;
        }
        18% {
          transform: translate(var(--tx), var(--ty)) scale(1) rotate(var(--spin-mid));
          opacity: 1;
        }
        100% {
          transform: translate(var(--tx-end), var(--ty-end)) scale(0.85) rotate(var(--spin-end));
          opacity: 0;
        }
      }
    `;
    root.appendChild(style);

    const count = Math.min(100, Math.max(64, Math.floor(window.innerWidth / 14)));
    const originX = window.innerWidth * 0.5;
    const originY = window.innerHeight * 0.38;

    for (let i = 0; i < count; i += 1) {
      const piece = document.createElement("span");
      const angle = Math.random() * Math.PI * 2;
      const dist = 80 + Math.random() * Math.min(window.innerWidth, window.innerHeight) * 0.42;
      const tx = Math.cos(angle) * dist;
      const ty = Math.sin(angle) * dist * 0.75 - 40;
      const txEnd = tx * (1.15 + Math.random() * 0.45);
      const tyEnd = ty + 180 + Math.random() * 220;
      const delay = Math.random() * 0.2;
      const duration = 2.8 + Math.random() * 1.6;
      const w = 8 + Math.random() * 12;
      const h = 12 + Math.random() * 18;
      const spinMid = `${(Math.random() > 0.5 ? 1 : -1) * (90 + Math.random() * 180)}deg`;
      const spinEnd = `${(Math.random() > 0.5 ? 1 : -1) * (280 + Math.random() * 420)}deg`;

      piece.style.cssText = [
        "position:absolute",
        `left:${originX}px`,
        `top:${originY}px`,
        `width:${w}px`,
        `height:${h}px`,
        `background:${PALETTE[i % PALETTE.length]}`,
        "border-radius:1px",
        `box-shadow:0 0 10px color-mix(in srgb, ${PALETTE[i % PALETTE.length]} 55%, transparent)`,
        `--tx:${tx.toFixed(1)}px`,
        `--ty:${ty.toFixed(1)}px`,
        `--tx-end:${txEnd.toFixed(1)}px`,
        `--ty-end:${tyEnd.toFixed(1)}px`,
        `--spin-mid:${spinMid}`,
        `--spin-end:${spinEnd}`,
        `animation:awards-confetti-burst ${duration}s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s both`,
        "will-change:transform,opacity",
      ].join(";");
      root.appendChild(piece);
    }

    document.body.appendChild(root);

    const timer = window.setTimeout(() => {
      root.remove();
    }, DURATION_MS);

    return () => {
      window.clearTimeout(timer);
      root.remove();
    };
  }, []);

  return null;
}
