import { useEffect, useRef, useState } from "react";
import { mediaUrl } from "../config.js";
import { useI18n } from "../i18n/index.jsx";
import Mascot from "../components/Mascot.jsx";
import { beatMs, prefersReducedMotion } from "../guessBeat.js";

export default function GuessPage({ guess, busy, onCorrect, onWrong }) {
  const { t, tq } = useI18n();
  const [phase, setPhase] = useState("focus");
  const [mood, setMood] = useState("excited");
  const [messageKey, setMessageKey] = useState("mascot.excited");
  const lockedRef = useRef(false);
  const timers = useRef([]);

  useEffect(() => {
    const reduced = prefersReducedMotion();
    const id = window.setTimeout(() => setPhase("reveal"), beatMs("focus", reduced));
    timers.current.push(id);
    return () => {
      timers.current.forEach((timer) => clearTimeout(timer));
      timers.current = [];
    };
  }, []);

  if (!guess) return null;
  const { character, confidence, confidence_percent, top_candidates, influential_questions } =
    guess;
  const pct =
    typeof confidence_percent === "number"
      ? Math.round(confidence_percent)
      : Math.round((confidence || 0) * 100);
  const candidates = Array.isArray(top_candidates) ? top_candidates.slice(0, 5) : [];
  const influencers = Array.isArray(influential_questions)
    ? influential_questions.slice(0, 5)
    : [];
  const imageSrc = mediaUrl(character.image_url);
  const locked =
    busy || lockedRef.current || phase === "focus" || phase === "celebrate" || phase === "miss";
  const revealed = phase !== "focus";

  const handleCorrect = () => {
    if (lockedRef.current || busy) return;
    lockedRef.current = true;
    setPhase("celebrate");
    setMood("happy");
    setMessageKey("mascot.correct");
    const reduced = prefersReducedMotion();
    const id = window.setTimeout(() => onCorrect(), beatMs("celebrate", reduced));
    timers.current.push(id);
  };

  const handleWrong = () => {
    if (lockedRef.current || busy) return;
    lockedRef.current = true;
    setPhase("miss");
    setMood("surprised");
    setMessageKey("mascot.wrong");
    const reduced = prefersReducedMotion();
    const id = window.setTimeout(() => onWrong(), beatMs("miss", reduced));
    timers.current.push(id);
  };

  return (
    <section className={`page guess guess-stage is-${phase}`}>
      <div className="guess-mascot-wrap">
        <Mascot state={mood} t={t} compact messageKey={messageKey} />
      </div>
      <p className="kicker">{t("guess.kicker")}</p>
      <div className={`guess-card${revealed ? " guess-card-reveal" : " is-hidden"}`}>
        <img className="guess-photo" src={imageSrc} alt={character.name} />
        <h2 className="guess-name">{character.name}</h2>
        <p className="guess-conf">{t("guess.confident", { pct })}</p>
      </div>

      {revealed && (
        <>
          <p className="lede center guess-why">{t("guess.summary", { name: character.name })}</p>

          {influencers.length > 0 && (
            <div className="explain-block">
              <h3 className="explain-title">{t("guess.influencers")}</h3>
              <ol className="explain-list">
                {influencers.map((row) => (
                  <li key={row.id}>
                    <span className="explain-q">{tq(row.text)}</span>
                    <span className="explain-meta">
                      {t(`answers.${row.answer}`, {}) ||
                        String(row.answer || "").replace(/_/g, " ")}{" "}
                      · {t("guess.impact", { pts: (row.influence * 100).toFixed(1) })}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {candidates.length > 0 && (
            <div className="explain-block">
              <h3 className="explain-title">{t("guess.candidates")}</h3>
              <ol className="explain-list">
                {candidates.map((row) => (
                  <li key={row.id}>
                    <span className="explain-q">{row.name}</span>
                    <span className="explain-meta">{Math.round(row.probability * 100)}%</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          <p className="lede center">{t("guess.confirm")}</p>
          <div className="actions">
            <button type="button" className="btn primary" disabled={locked} onClick={handleCorrect}>
              {t("guess.yes")}
            </button>
            <button type="button" className="btn ghost" disabled={locked} onClick={handleWrong}>
              {t("guess.no")}
            </button>
          </div>
        </>
      )}
    </section>
  );
}
