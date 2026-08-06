const ANSWERS = [
  { value: "yes", label: "Yes" },
  { value: "probably_yes", label: "Probably" },
  { value: "dont_know", label: "Don't know" },
  { value: "probably_no", label: "Probably not" },
  { value: "no", label: "No" },
];

export default function QuestionPage({
  question,
  questionNumber,
  confidence,
  busy,
  onAnswer,
}) {
  if (!question) return null;

  return (
    <section className="page page-question">
      <header className="meta">
        <span>Q{questionNumber}</span>
        <span className="conf">{Math.round((confidence || 0) * 100)}% sure</span>
      </header>

      <h2 className="question-text">{question.text}</h2>

      <div className="answer-grid">
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
