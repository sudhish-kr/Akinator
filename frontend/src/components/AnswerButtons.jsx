const ICONS = {
  yes: "✓",
  probably_yes: "~",
  dont_know: "?",
  probably_no: "≈",
  no: "✕",
};

export default function AnswerButtons({
  answers,
  busy,
  disabled,
  selectedAnswer = null,
  onAnswer,
  onAnswerHover,
  onAnswerLeave,
  ariaLabel,
  enterKey,
}) {
  return (
    <div
      key={enterKey}
      className="answers answers-grid answers-enter"
      role="group"
      aria-label={ariaLabel}
      onMouseLeave={onAnswerLeave}
    >
      {answers.map((a) => {
        const selected = selectedAnswer === a.value;
        return (
          <button
            key={a.value}
            type="button"
            className={`btn answer answer-${a.value}${selected ? " is-selected" : ""}`}
            disabled={busy || disabled}
            aria-pressed={selected}
            onClick={() => onAnswer(a.value)}
            onMouseEnter={() => onAnswerHover?.(a.value)}
            onFocus={() => onAnswerHover?.(a.value)}
            onBlur={onAnswerLeave}
          >
            <span className="answer-icon" aria-hidden="true">
              {ICONS[a.value] || "·"}
            </span>
            <span className="answer-label">{a.label}</span>
          </button>
        );
      })}
    </div>
  );
}
