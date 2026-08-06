import { useI18n } from "../i18n/index.jsx";

export default function LearnPage({ wrongGuessName, characters, busy, onPick, onHome }) {
  const { t } = useI18n();
  return (
    <section className="page learn">
      <p className="kicker">{t("learn.kicker")}</p>
      <h2 className="title">{t("learn.title")}</h2>
      <p className="lede">
        {wrongGuessName
          ? t("learn.ledeWrong", { name: wrongGuessName })
          : t("learn.lede")}
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

      {!busy && characters.length === 0 && <p className="muted">{t("learn.empty")}</p>}

      <button type="button" className="btn ghost" disabled={busy} onClick={onHome}>
        {t("learn.home")}
      </button>
    </section>
  );
}
