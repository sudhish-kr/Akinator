export default function LearnPage({
  wrongGuessName,
  characters,
  busy,
  onPick,
  onSkip,
}) {
  return (
    <section className="page page-learn">
      <h2>Who were you thinking of?</h2>
      <p className="lede">
        {wrongGuessName
          ? `Not ${wrongGuessName}. Pick the correct character so I can learn.`
          : "Pick the correct character so I can learn."}
      </p>

      <div className="character-grid">
        {characters.map((c) => (
          <button
            key={c.id}
            type="button"
            className="btn chip"
            disabled={busy}
            onClick={() => onPick(c.id)}
          >
            {c.name}
          </button>
        ))}
      </div>

      {characters.length === 0 && !busy && (
        <p className="muted">No characters loaded.</p>
      )}

      <button type="button" className="btn secondary" disabled={busy} onClick={onSkip}>
        Skip — play again
      </button>
    </section>
  );
}
