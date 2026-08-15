/**
 * Decorative MindGuess orbs for the home world.
 * Lightweight CSS float + subtle pointer parallax (no canvas/libs).
 * Desktop: proximity reactions via rAF + refs (no per-move React state).
 */
import { useEffect, useRef } from "react";
import {
  lookOffset,
  pickBallColor,
  pickBallMood,
  proximityRadius,
  shouldActivate,
  staggerDelay,
} from "./homeBallInteract.js";

const BALLS = [
  { id: "b1", size: 72, x: 8, y: 18, depth: 0.9, delay: 0, duration: 7.2, amp: 14, parallax: 18 },
  { id: "b2", size: 44, x: 78, y: 14, depth: 1.2, delay: -1.4, duration: 5.8, amp: 10, parallax: 28 },
  { id: "b3", size: 96, x: 86, y: 58, depth: 0.55, delay: -2.2, duration: 9.1, amp: 16, parallax: 12 },
  { id: "b4", size: 36, x: 14, y: 68, depth: 1.4, delay: -0.6, duration: 4.9, amp: 12, parallax: 32 },
  { id: "b5", size: 58, x: 70, y: 78, depth: 0.75, delay: -3.1, duration: 6.6, amp: 11, parallax: 22 },
  { id: "b6", size: 28, x: 42, y: 12, depth: 1.6, delay: -1.8, duration: 5.2, amp: 9, parallax: 36 },
  { id: "b7", size: 64, x: 4, y: 42, depth: 0.7, delay: -2.7, duration: 8.4, amp: 13, parallax: 16 },
  { id: "b8", size: 40, x: 92, y: 34, depth: 1.1, delay: -0.9, duration: 6.1, amp: 10, parallax: 26 },
  { id: "b9", size: 22, x: 55, y: 86, depth: 1.5, delay: -3.5, duration: 4.4, amp: 8, parallax: 40 },
  { id: "b10", size: 50, x: 28, y: 82, depth: 0.85, delay: -1.1, duration: 7.7, amp: 12, parallax: 20 },
];

const COOLDOWN_MS = 850;
const REACT_MS = 560;
const TINT_HOLD_MS = 920;
const LEAVE_HYSTERESIS = 1.12;

function finePointer() {
  try {
    return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  } catch {
    return false;
  }
}

function reducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export default function HomeBackgroundBalls({ burst = false, startHover = false }) {
  const rootRef = useRef(null);
  const burstRef = useRef(burst);
  burstRef.current = burst;

  useEffect(() => {
    if (!finePointer()) return undefined;

    const root = rootRef.current;
    if (!root) return undefined;

    const nodes = Array.from(root.querySelectorAll(".home-ball"));
    const runtime = BALLS.map((ball, i) => ({
      el: nodes[i],
      x: ball.x,
      y: ball.y,
      radius: proximityRadius(ball.size),
      inside: false,
      cooldownUntil: 0,
      lastColor: null,
      lastMood: null,
      timers: [],
    }));

    let raf = 0;
    let pending = null;
    const pendingTimers = [];

    const clearTimers = (item) => {
      item.timers.forEach((id) => clearTimeout(id));
      item.timers = [];
    };

    const restoreTint = (item) => {
      if (!item.el) return;
      item.el.classList.remove("is-tinted", "is-mood-happy", "is-mood-excited", "is-mood-curious");
      item.el.style.removeProperty("--ball-tint");
    };

    const activate = (item, look, delay) => {
      const run = () => {
        if (!item.el || burstRef.current || !item.inside) return;
        const color = pickBallColor(item.lastColor);
        const mood = pickBallMood(item.lastMood);
        item.lastColor = color.id;
        item.lastMood = mood;
        item.cooldownUntil = performance.now() + COOLDOWN_MS;
        const reduced = reducedMotion();
        const lookX = reduced ? 0 : look.x;
        const lookY = reduced ? 0 : look.y;

        item.el.style.setProperty("--ball-tint", color.tint);
        item.el.style.setProperty("--look-x", `${lookX}px`);
        item.el.style.setProperty("--look-y", `${lookY}px`);
        item.el.classList.add("is-tinted", `is-mood-${mood}`);
        if (!reduced) item.el.classList.add("is-reacting");

        clearTimers(item);
        if (!reduced) {
          item.timers.push(
            setTimeout(() => item.el?.classList.remove("is-reacting"), REACT_MS)
          );
        }
        item.timers.push(setTimeout(() => restoreTint(item), reduced ? 520 : TINT_HOLD_MS));
      };

      if (delay) {
        const id = setTimeout(run, delay);
        pendingTimers.push(id);
        item.timers.push(id);
      } else {
        run();
      }
    };

    const tick = () => {
      raf = 0;
      const ev = pending;
      pending = null;
      if (!ev || burstRef.current) return;

      const rect = root.getBoundingClientRect();
      if (rect.width < 8 || rect.height < 8) return;

      let frameIndex = 0;
      const now = performance.now();

      for (const item of runtime) {
        if (!item.el) continue;
        if (item.el.offsetWidth === 0) {
          item.inside = false;
          continue;
        }

        const cx = rect.left + (item.x / 100) * rect.width;
        const cy = rect.top + (item.y / 100) * rect.height;
        const dx = ev.clientX - cx;
        const dy = ev.clientY - cy;
        const inside = item.inside
          ? Math.hypot(dx, dy) <= item.radius * LEAVE_HYSTERESIS
          : Math.hypot(dx, dy) <= item.radius;

        const look = lookOffset(dx, dy, item.radius);
        if (inside && !reducedMotion()) {
          item.el.style.setProperty("--look-x", `${look.x}px`);
          item.el.style.setProperty("--look-y", `${look.y}px`);
          item.el.classList.add("is-watching");
        } else if (!inside) {
          item.el.classList.remove("is-watching");
        }

        if (
          shouldActivate({
            inside,
            wasInside: item.inside,
            now,
            cooldownUntil: item.cooldownUntil,
          })
        ) {
          item.inside = true;
          activate(item, look, staggerDelay(frameIndex));
          frameIndex += 1;
        }
        item.inside = inside;
      }
    };

    const onMove = (event) => {
      if (event.pointerType && event.pointerType !== "mouse") return;
      pending = { clientX: event.clientX, clientY: event.clientY };
      if (!raf) raf = requestAnimationFrame(tick);
    };

    const onLeave = () => {
      pending = null;
      runtime.forEach((item) => {
        item.inside = false;
      });
    };

    const stage = root.parentElement;
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("blur", onLeave);
    stage?.addEventListener("pointerleave", onLeave);

    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("blur", onLeave);
      stage?.removeEventListener("pointerleave", onLeave);
      if (raf) cancelAnimationFrame(raf);
      pendingTimers.forEach((id) => clearTimeout(id));
      runtime.forEach((item) => {
        clearTimers(item);
        if (item.el) {
          item.el.classList.remove("is-reacting", "is-tinted", "is-watching", "is-mood-happy", "is-mood-excited", "is-mood-curious");
          item.el.style.removeProperty("--ball-tint");
        }
      });
    };
  }, []);

  return (
    <div
      ref={rootRef}
      className={`home-balls${burst ? " is-burst" : ""}${startHover ? " is-start-hover" : ""}`}
      aria-hidden="true"
    >
      {BALLS.map((ball) => (
        <span
          key={ball.id}
          className={`home-ball home-ball--${ball.id}`}
          style={{
            "--ball-size": `${ball.size}px`,
            "--ball-x": `${ball.x}%`,
            "--ball-y": `${ball.y}%`,
            "--ball-nx": ball.x,
            "--ball-ny": ball.y,
            "--ball-depth": ball.depth,
            "--ball-delay": `${ball.delay}s`,
            "--ball-duration": `${ball.duration}s`,
            "--ball-amp": `${ball.amp}px`,
            "--ball-parallax": ball.parallax,
          }}
        >
          <span className="home-ball-bounce">
            <span className="home-ball-core">
              <span className="home-ball-tint" />
              <span className="home-ball-shine" />
              <span className="home-ball-eye home-ball-eye-l" />
              <span className="home-ball-eye home-ball-eye-r" />
              <span className="home-ball-mouth" />
            </span>
          </span>
        </span>
      ))}
    </div>
  );
}
