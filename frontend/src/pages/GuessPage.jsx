import { t } from "../i18n.js";

export default function GuessPage({ lang, guess, busy, onCorrect, onWrong, onBack }) {
  if (!guess) return null;
  const { character, confidence } = guess;
  const pct = Math.round(confidence * 100);

  return (
    <section className="page guess">
      <div className="game-toolbar">
        <button type="button" className="btn ghost sm" onClick={onBack} disabled={busy}>
          {t(lang, "back")}
        </button>
      </div>
      <p className="kicker">{t(lang, "finalRead")}</p>
      <div className="guess-card">
        <div className="avatar" aria-hidden="true">
          {character.name.charAt(0)}
        </div>
        <h2 className="guess-name">{character.name}</h2>
        <p className="guess-conf">
          {pct}% {t(lang, "confident")}
        </p>
      </div>
      <p className="lede center">{t(lang, "isThisWho")}</p>
      <div className="actions">
        <button type="button" className="btn primary" disabled={busy} onClick={onCorrect}>
          {t(lang, "yesGotIt")}
        </button>
        <button type="button" className="btn ghost" disabled={busy} onClick={onWrong}>
          {t(lang, "noTeachMe")}
        </button>
      </div>
    </section>
  );
}
