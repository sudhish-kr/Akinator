export default function LearnPage({ wrongGuessName, characters, busy, onPick, onHome }) {
  return (
    <section className="page learn">
      <p className="kicker">Learning</p>
      <h2 className="title">Who was it?</h2>
      <p className="lede">
        {wrongGuessName
          ? `Not ${wrongGuessName}. Choose the correct character so I can update my model.`
          : "Choose the correct character so I can update my model."}
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

      {!busy && characters.length === 0 && (
        <p className="muted">No active characters available.</p>
      )}

      <button type="button" className="btn ghost" disabled={busy} onClick={onHome}>
        Back to home
      </button>
    </section>
  );
}
