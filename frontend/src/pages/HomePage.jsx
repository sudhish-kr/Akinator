import { useCallback, useEffect, useRef, useState } from "react";
import { useI18n } from "../i18n/index.jsx";
import HomeBackgroundBalls from "../components/HomeBackgroundBalls.jsx";

function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

export default function HomePage({ onStart, busy }) {
  const { t } = useI18n();
  const stageRef = useRef(null);
  const rafRef = useRef(0);
  const startingRef = useRef(false);
  const [startHover, setStartHover] = useState(false);
  const [burst, setBurst] = useState(false);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    setReduced(prefersReducedMotion());
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener?.("change", onChange);
    return () => mq.removeEventListener?.("change", onChange);
  }, []);

  useEffect(() => {
    if (!busy) startingRef.current = false;
  }, [busy]);

  const onPointerMove = useCallback(
    (event) => {
      if (reduced || !stageRef.current) return;
      const el = stageRef.current;
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const rect = el.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        el.style.setProperty("--px", String(Math.max(-0.5, Math.min(0.5, x))));
        el.style.setProperty("--py", String(Math.max(-0.5, Math.min(0.5, y))));
      });
    },
    [reduced]
  );

  const onPointerLeave = useCallback(() => {
    if (!stageRef.current) return;
    stageRef.current.style.setProperty("--px", "0");
    stageRef.current.style.setProperty("--py", "0");
  }, []);

  const handleStart = () => {
    if (busy || startingRef.current) return;
    startingRef.current = true;
    setBurst(true);
    onStart();
    window.setTimeout(() => setBurst(false), reduced ? 200 : 700);
  };

  return (
    <section
      ref={stageRef}
      className={`page home home-world${busy ? " is-starting" : ""}${burst ? " is-burst" : ""}`}
      onPointerMove={onPointerMove}
      onPointerLeave={onPointerLeave}
      style={{ "--px": 0, "--py": 0 }}
    >
      <HomeBackgroundBalls burst={burst} startHover={startHover} />

      <div className="home-content">
        <p className="kicker">{t("home.kicker")}</p>
        <h1 className="brand">
          Mind<span>Guess</span>
        </h1>
        <p className="lede home-lede">{t("home.lede")}</p>
        <button
          type="button"
          className="btn primary lg home-start"
          onClick={handleStart}
          disabled={busy}
          onMouseEnter={() => setStartHover(true)}
          onMouseLeave={() => setStartHover(false)}
          onFocus={() => setStartHover(true)}
          onBlur={() => setStartHover(false)}
        >
          {busy ? t("home.connecting") : t("home.start")}
        </button>
        <a className="admin-entry" href="#/admin">
          {t("home.admin")}
        </a>
      </div>
    </section>
  );
}
