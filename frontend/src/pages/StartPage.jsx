export default function StartPage({ onStart, busy }) {
  return (
    <section className="page page-start">
      <h1 className="brand">
        Mind<span>Guess</span>
      </h1>
      <p className="lede">Think of a character. Answer honestly. I will find them.</p>
      <button type="button" className="btn primary" onClick={onStart} disabled={busy}>
        {busy ? "Starting…" : "Start game"}
      </button>
    </section>
  );
}
