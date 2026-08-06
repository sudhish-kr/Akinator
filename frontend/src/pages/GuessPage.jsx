import { mediaUrl } from "../config.js";

export default function GuessPage({ guess, busy, onCorrect, onWrong }) {
  if (!guess) return null;
  const { character, confidence, confidence_percent, summary, top_candidates, influential_questions } =
    guess;
  const pct =
    typeof confidence_percent === "number"
      ? Math.round(confidence_percent)
      : Math.round((confidence || 0) * 100);
  const candidates = Array.isArray(top_candidates) ? top_candidates.slice(0, 5) : [];
  const influencers = Array.isArray(influential_questions)
    ? influential_questions.slice(0, 5)
    : [];
  const imageSrc = mediaUrl(character.image_url);

  return (
    <section className="page guess">
      <p className="kicker">Final read</p>
      <div className="guess-card">
        <img className="guess-photo" src={imageSrc} alt={character.name} />
        <h2 className="guess-name">{character.name}</h2>
        <p className="guess-conf">{pct}% confident</p>
      </div>

      {summary && <p className="lede center guess-why">{summary}</p>}

      {influencers.length > 0 && (
        <div className="explain-block">
          <h3 className="explain-title">Most influential answers</h3>
          <ol className="explain-list">
            {influencers.map((row) => (
              <li key={row.id}>
                <span className="explain-q">{row.text}</span>
                <span className="explain-meta">
                  {String(row.answer || "").replace(/_/g, " ")} · impact{" "}
                  {(row.influence * 100).toFixed(1)} pts
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {candidates.length > 0 && (
        <div className="explain-block">
          <h3 className="explain-title">Top candidates</h3>
          <ol className="explain-list">
            {candidates.map((row) => (
              <li key={row.id}>
                <span className="explain-q">{row.name}</span>
                <span className="explain-meta">{Math.round(row.probability * 100)}%</span>
              </li>
            ))}
          </ol>
        </div>
      )}

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
