export default function GuessPage({ guess, busy, onCorrect, onWrong }) {
  if (!guess) return null;
  const { character, confidence } = guess;
  const pct = Math.round(confidence * 100);

  return (
    <section className="page guess">
      <p className="kicker">Final read</p>
      <div className="guess-card">
        <div className="avatar" aria-hidden="true">
          {character.name.charAt(0)}
        </div>
        <h2 className="guess-name">{character.name}</h2>
        <p className="guess-conf">{pct}% confident</p>
      </div>
      <p className="lede center">Is this who you were thinking of?</p>
      <div className="actions">
        <button type="button" className="btn primary" disabled={busy} onClick={onCorrect}>
          Yes — you got it
        </button>
        <button type="button" className="btn ghost" disabled={busy} onClick={onWrong}>
          No — teach me
        </button>
      </div>
    </section>
  );
}
