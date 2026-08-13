import { t } from "../i18n.js";

export default function LearnPage({
  lang,
  wrongGuessName,
  characters,
  busy,
  onPick,
  onHome,
}) {
  return (
    <section className="page learn">
      <p className="kicker">{t(lang, "learning")}</p>
      <h2 className="title">{t(lang, "whoWasIt")}</h2>
      <p className="lede">
        {wrongGuessName
          ? t(lang, "notNameChoose", wrongGuessName)
          : t(lang, "chooseCorrect")}
      </p>

      <div className="char-grid">
        {characters.map((c) => (
          <button
            key={c.id}
            type="button"
            className="btn chip"
            disabled={busy}
            onClick={() => onPick(c.id, c.name)}
          >
            {c.name}
          </button>
        ))}
      </div>

      {!busy && characters.length === 0 && (
        <p className="muted">{t(lang, "noCharacters")}</p>
      )}

      <button type="button" className="btn ghost" disabled={busy} onClick={onHome}>
        {t(lang, "backToHome")}
      </button>
    </section>
  );
}
