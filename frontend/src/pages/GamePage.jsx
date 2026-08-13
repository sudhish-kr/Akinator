import { answerLabels, t, translateQuestionText } from "../i18n.js";

export default function GamePage({
  lang,
  question,
  questionNumber,
  confidence,
  busy,
  selectedAnswer,
  canGoPrevious,
  canGoNext,
  showEndConfirm,
  onAnswer,
  onBack,
  onPrevious,
  onNext,
  onEndGameRequest,
  onEndConfirm,
  onEndCancel,
}) {
  if (!question) return null;
  const pct = Math.round((confidence || 0) * 100);
  const reviewing = Boolean(selectedAnswer);
  const answers = answerLabels(lang);
  const questionText = translateQuestionText(question.text, lang);

  return (
    <section className="page game">
      <div className="game-toolbar">
        <button type="button" className="btn ghost sm" onClick={onBack} disabled={busy}>
          {t(lang, "back")}
        </button>
        <div className="game-toolbar-end">
          <button
            type="button"
            className="btn ghost sm"
            onClick={onPrevious}
            disabled={busy || !canGoPrevious}
          >
            {t(lang, "previous")}
          </button>
          {canGoNext && (
            <button type="button" className="btn ghost sm" onClick={onNext} disabled={busy}>
              {t(lang, "next")}
            </button>
          )}
          <button
            type="button"
            className="btn danger-outline sm"
            onClick={onEndGameRequest}
            disabled={busy}
          >
            {t(lang, "endGame")}
          </button>
        </div>
      </div>

      <header className="game-hud">
        <div>
          <span className="hud-label">{t(lang, "question")}</span>
          <strong className="hud-value">{questionNumber}</strong>
        </div>
        <div className="hud-conf">
          <span className="hud-label">{t(lang, "confidence")}</span>
          <div className="bar" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <strong className="hud-value">{pct}%</strong>
        </div>
      </header>

      <h2 className="question">{questionText}</h2>

      {reviewing && (
        <p className="muted selected-hint">{t(lang, "selectedAnswer")}</p>
      )}

      <div className="answers" role="group" aria-label={t(lang, "yourAnswer")}>
        {answers.map((a) => {
          const isSelected = selectedAnswer === a.value;
          return (
            <button
              key={a.value}
              type="button"
              className={`btn answer${isSelected ? " selected" : ""}`}
              disabled={busy || reviewing}
              onClick={() => onAnswer(a.value)}
            >
              {a.label}
            </button>
          );
        })}
      </div>

      {showEndConfirm && (
        <div className="modal-backdrop" role="presentation" onClick={onEndCancel}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="end-game-title"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="end-game-title" className="modal-title">
              {t(lang, "endGameTitle")}
            </h3>
            <div className="modal-actions">
              <button type="button" className="btn primary" onClick={onEndCancel}>
                {t(lang, "continueGame")}
              </button>
              <button type="button" className="btn danger-outline" onClick={onEndConfirm}>
                {t(lang, "confirmEnd")}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
