const ANSWERS = [
  { value: "yes", label: "Yes" },
  { value: "probably_yes", label: "Probably" },
  { value: "dont_know", label: "Don't know" },
  { value: "probably_no", label: "Probably not" },
  { value: "no", label: "No" },
];

export default function GamePage({ question, questionNumber, confidence, busy, onAnswer }) {
  if (!question) return null;
  const pct = Math.round((confidence || 0) * 100);

  return (
    <section className="page game">
      <header className="game-hud">
        <div>
          <span className="hud-label">Question</span>
          <strong className="hud-value">{questionNumber}</strong>
        </div>
        <div className="hud-conf">
          <span className="hud-label">Confidence</span>
          <div className="bar" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <strong className="hud-value">{pct}%</strong>
        </div>
      </header>

      <h2 className="question">{question.text}</h2>

      <div className="answers" role="group" aria-label="Your answer">
        {ANSWERS.map((a) => (
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
