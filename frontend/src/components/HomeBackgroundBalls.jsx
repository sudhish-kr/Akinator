/**
 * Decorative MindGuess orbs for the home world.
 * Lightweight CSS float + subtle pointer parallax (no canvas/libs).
 * Desktop: proximity burst + respawn via rAF + refs (no per-move React state).
 */
import { useEffect, useRef } from "react";
import {
  ARRIVE_MS,
  BURST_MS,
  collectKeepOutRects,
  jitterSize,
  nextBallSpec,
  pickSpawnPercent,
  proximityRadius,
  shouldActivate,
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

function applySpec(el, spec) {
  if (!el) return;
  el.style.setProperty("--ball-x", `${spec.x}%`);
  el.style.setProperty("--ball-y", `${spec.y}%`);
  el.style.setProperty("--ball-nx", String(spec.x));
  el.style.setProperty("--ball-ny", String(spec.y));
  el.style.setProperty("--ball-size", `${spec.size}px`);
  el.style.setProperty("--ball-duration", `${spec.duration}s`);
  el.style.setProperty("--ball-amp", `${spec.amp}px`);
  el.style.setProperty("--ball-delay", `${spec.delay}s`);
  el.style.setProperty("--ball-opacity", String(spec.opacity));
}

function addRipple(el) {
  el.querySelectorAll(".home-ball-pop").forEach((node) => node.remove());
  const wrap = document.createElement("span");
  wrap.className = "home-ball-pop";
  const ring = document.createElement("span");
  ring.className = "home-ball-ring";
  wrap.appendChild(ring);
  for (let i = 0; i < 5; i += 1) {
    const speck = document.createElement("span");
    speck.className = "home-ball-speck";
    speck.style.setProperty("--speck-i", String(i));
    wrap.appendChild(speck);
  }
  el.appendChild(wrap);
  return wrap;
}

function restartFloat(el) {
  const core = el?.querySelector(".home-ball-core");
  if (!core) return;
  core.style.animation = "none";
  void core.offsetWidth;
  core.style.animation = "";
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
      size: ball.size,
      depth: ball.depth,
      duration: ball.duration,
      amp: ball.amp,
      delay: ball.delay,
      baseSize: ball.size,
      baseDuration: ball.duration,
      baseAmp: ball.amp,
      radius: proximityRadius(ball.size),
      inside: false,
      popping: false,
      gen: 0,
      cooldownUntil: 0,
      timers: [],
    }));

    let raf = 0;
    let pending = null;
    let lastMouse = null;
    const pendingTimers = [];

    const clearTimers = (item) => {
      item.timers.forEach((id) => clearTimeout(id));
      item.timers = [];
    };

    const respawn = (item) => {
      const rect = root.getBoundingClientRect();
      const size = jitterSize(item.baseSize);
      const spec = nextBallSpec(item, {
        ...pickSpawnPercent({
          rootRect: rect,
          mouse: lastMouse,
          avoidRects: collectKeepOutRects(root),
          size,
        }),
        size,
      });
      applySpec(item.el, spec);
      item.x = spec.x;
      item.y = spec.y;
      item.size = spec.size;
      item.duration = spec.duration;
      item.amp = spec.amp;
      item.delay = spec.delay;
      item.radius = spec.radius;
      item.inside = false;
      item.popping = false;
      item.cooldownUntil = performance.now() + ARRIVE_MS + 80;
      item.el.classList.remove("is-popping");
      item.el.querySelectorAll(".home-ball-pop").forEach((node) => node.remove());
      restartFloat(item.el);
      item.el.classList.add("is-arriving");
      const arriveId = setTimeout(() => item.el?.classList.remove("is-arriving"), ARRIVE_MS);
      pendingTimers.push(arriveId);
      item.timers.push(arriveId);
    };

    const popBall = (item) => {
      if (!item.el || item.popping || burstRef.current || reducedMotion()) return;
      item.popping = true;
      item.inside = true;
      item.gen += 1;
      const gen = item.gen;
      clearTimers(item);
      addRipple(item.el);
      item.el.classList.add("is-popping");
      item.el.classList.remove("is-arriving", "is-reacting", "is-tinted", "is-watching");

      const id = setTimeout(() => {
        if (item.gen !== gen || !item.el) return;
        respawn(item);
      }, BURST_MS);
      pendingTimers.push(id);
      item.timers.push(id);
    };

    const tick = () => {
      raf = 0;
      const ev = pending;
      pending = null;
      if (!ev || burstRef.current) return;

      const rect = root.getBoundingClientRect();
      if (rect.width < 8 || rect.height < 8) return;

      const now = performance.now();

      for (const item of runtime) {
        if (!item.el || item.popping) continue;
        if (item.el.offsetWidth === 0 || now < item.cooldownUntil) {
          item.inside = false;
          continue;
        }

        const cx = rect.left + (item.x / 100) * rect.width;
        const cy = rect.top + (item.y / 100) * rect.height;
        const dx = ev.clientX - cx;
        const dy = ev.clientY - cy;
        const dist = Math.hypot(dx, dy);
        const inside = item.inside
          ? dist <= item.radius * LEAVE_HYSTERESIS
          : dist <= item.radius;

        if (
          shouldActivate({
            inside,
            wasInside: item.inside,
            now,
            cooldownUntil: item.cooldownUntil,
          })
        ) {
          item.inside = true;
          popBall(item);
          continue;
        }
        item.inside = inside;
      }
    };

    const onMove = (event) => {
      if (event.pointerType && event.pointerType !== "mouse") return;
      lastMouse = { clientX: event.clientX, clientY: event.clientY };
      pending = lastMouse;
      if (!raf) raf = requestAnimationFrame(tick);
    };

    const onLeave = () => {
      pending = null;
      runtime.forEach((item) => {
        if (!item.popping) item.inside = false;
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
          item.el.classList.remove("is-popping", "is-arriving");
          item.el.querySelectorAll(".home-ball-pop").forEach((node) => node.remove());
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
