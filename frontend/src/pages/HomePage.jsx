export default function HomePage({ onStart, busy }) {
  return (
    <section className="page home">
      <p className="kicker">20 questions · Bayesian mind</p>
      <h1 className="brand">
        Mind<span>Guess</span>
      </h1>
      <p className="lede">
        Think of a character. Answer each question. I will narrow the field until
        only one remains.
      </p>
      <button type="button" className="btn primary lg" onClick={onStart} disabled={busy}>
        {busy ? "Connecting…" : "Start game"}
      </button>
    </section>
  );
}
