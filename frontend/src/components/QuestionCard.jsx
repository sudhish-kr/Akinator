import ConfidenceBar from "./ConfidenceBar.jsx";
import AnswerButtons from "./AnswerButtons.jsx";

export default function QuestionCard({
  t,
  questionNumber,
  confidence,
  questionText,
  questionKey,
  busy,
  editingPrevious = false,
  navDirection = "forward",
  selectedAnswer = null,
  answers,
  onAnswer,
  onAnswerHover,
  onAnswerLeave,
  voiceOn,
  canSpeak,
  canListen,
  listening,
  voiceNote,
  onSpeakAgain,
  onStartListening,
  introWaiting = false,
  introReady = true,
  children,
}) {
  return (
    <article
      className={`question-card${busy ? " is-thinking" : ""}${introWaiting ? " is-intro-waiting" : ""}${introReady && !introWaiting ? " is-intro-ready" : ""}`}
    >
      <header className="question-card-hud">
        <div className="question-meta">
          <span className="hud-label">{t("game.question")}</span>
          <strong className="hud-value">{questionNumber}</strong>
        </div>
        <ConfidenceBar confidence={confidence} label={t("game.confidence")} />
      </header>

      {(voiceOn || voiceNote) && (
        <div className="voice-panel">
          {voiceOn && canSpeak && (
            <button type="button" className="btn ghost voice-mini" disabled={busy} onClick={onSpeakAgain}>
              {t("game.speak")}
            </button>
          )}
          {voiceOn && canListen && (
            <button
              type="button"
              className={`btn primary voice-mic ${listening ? "listening" : ""}`}
              disabled={busy || listening}
              onClick={onStartListening}
            >
              {listening ? t("game.listening") : t("game.listen")}
            </button>
          )}
          {voiceOn && <p className="voice-hint">{t("game.voiceHint")}</p>}
          {voiceNote && <p className="voice-note">{voiceNote}</p>}
        </div>
      )}

      <div
        key={questionKey}
        className={`question-stage${navDirection === "back" ? " is-nav-back" : " is-nav-forward"}`}
      >
        <h2 className="question">{questionText}</h2>
        {busy && <p className="thinking-feedback">{t("game.thinking")}</p>}
      </div>

      {editingPrevious && (
        <p className="editing-note" role="status">
          {t("game.editingPrevious")}
        </p>
      )}

      <AnswerButtons
        answers={answers}
        busy={busy}
        selectedAnswer={selectedAnswer}
        onAnswer={onAnswer}
        onAnswerHover={onAnswerHover}
        onAnswerLeave={onAnswerLeave}
        ariaLabel={t("game.answersAria")}
        enterKey={questionKey}
      />

      {children}
    </article>
  );
}
