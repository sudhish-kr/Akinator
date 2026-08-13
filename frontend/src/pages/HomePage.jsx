import { t } from "../i18n.js";

export default function HomePage({ lang, onStart, onLeaderboard, onLangChange, busy }) {
  return (
    <section className="page home">
      <div className="home-top">
        <p className="kicker">{t(lang, "kicker")}</p>
        <div className="lang-toggle" role="group" aria-label={t(lang, "language")}>
          <button
            type="button"
            className={`btn sm lang-btn${lang === "en" ? " active" : ""}`}
            onClick={() => onLangChange("en")}
            aria-pressed={lang === "en"}
          >
            {t(lang, "english")}
          </button>
          <button
            type="button"
            className={`btn sm lang-btn${lang === "hi" ? " active" : ""}`}
            onClick={() => onLangChange("hi")}
            aria-pressed={lang === "hi"}
          >
            {t(lang, "hindi")}
          </button>
        </div>
      </div>
      <h1 className="brand">
        Mind<span>Guess</span>
      </h1>
      <p className="lede">{t(lang, "lede")}</p>
      <div className="home-actions">
        <button type="button" className="btn primary lg" onClick={onStart} disabled={busy}>
          {busy ? t(lang, "connecting") : t(lang, "startGame")}
        </button>
        <button type="button" className="btn ghost" onClick={onLeaderboard} disabled={busy}>
          {t(lang, "leaderboard")}
        </button>
      </div>
      <a className="admin-entry" href="#/admin">
        {t(lang, "adminDashboard")}
      </a>
    </section>
  );
}
