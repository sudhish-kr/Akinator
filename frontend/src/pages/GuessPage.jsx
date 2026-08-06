export default function GuessPage({ guess, busy, onCorrect, onWrong }) {
  if (!guess) return null;
  const { character, confidence } = guess;

  return (
    <section className="page page-guess">
      <p className="eyebrow">My guess</p>
      <h2 className="guess-name">{character.name}</h2>
      <p className="conf-line">{Math.round(confidence * 100)}% confidence</p>
      <p className="prompt">Am I right?</p>
      <div className="row">
        <button type="button" className="btn primary" disabled={busy} onClick={onCorrect}>
          Yes
        </button>
        <button type="button" className="btn secondary" disabled={busy} onClick={onWrong}>
          No — teach me
        </button>
      </div>
    </section>
  );
}
