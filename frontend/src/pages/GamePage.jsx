import { useI18n } from "../i18n/index.jsx";

export default function GamePage({ question, questionNumber, confidence, busy, onAnswer }) {
  const { t, tq } = useI18n();
  if (!question) return null;
  const pct = Math.round((confidence || 0) * 100);

  const answers = [
    { value: "yes", label: t("game.yes") },
    { value: "probably_yes", label: t("game.probablyYes") },
    { value: "dont_know", label: t("game.dontKnow") },
    { value: "probably_no", label: t("game.probablyNo") },
    { value: "no", label: t("game.no") },
  ];

  return (
    <section className="page game">
      <header className="game-hud">
        <div>
          <span className="hud-label">{t("game.question")}</span>
          <strong className="hud-value">{questionNumber}</strong>
        </div>
        <div className="hud-conf">
          <span className="hud-label">{t("game.confidence")}</span>
          <div className="bar" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <strong className="hud-value">{pct}%</strong>
        </div>
      </header>

      <h2 className="question">{tq(question.text)}</h2>

      <div className="answers" role="group" aria-label={t("game.answersAria")}>
        {answers.map((a) => (
          <button
            key={a.value}
            type="button"
            className="btn answer"
            disabled={busy}
            onClick={() => onAnswer(a.value)}
          >
            {a.label}
          </button>
        ))}
      </div>
    </section>
  );
}
