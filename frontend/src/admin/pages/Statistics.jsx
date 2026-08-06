import { useEffect, useState } from "react";
import { adminApi } from "../api.js";

export default function StatisticsPage() {
  const [stats, setStats] = useState(null);
  const [totals, setTotals] = useState({ characters: 0, questions: 0, learning: 0 });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError(null);
      try {
        const [statistics, characters, questions] = await Promise.all([
          adminApi.getStatistics(),
          adminApi.listCharacters(),
          adminApi.listQuestions(),
        ]);
        if (cancelled) return;

        const charItems = characters.items || [];
        const qItems = questions.items || [];
        const learningCount =
          qItems.reduce((sum, q) => sum + (q.times_asked || 0), 0) +
          charItems.reduce(
            (sum, c) =>
              sum + (c.times_guessed_correctly || 0) + (c.times_guessed_incorrectly || 0),
            0
          );

        setStats(statistics);
        setTotals({
          characters: characters.meta?.total ?? charItems.length,
          questions: questions.meta?.total ?? qItems.length,
          learning: learningCount,
        });
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="admin-panel">
      <header className="admin-panel-head">
        <div>
          <h2>Statistics</h2>
          <p>Snapshot of the knowledge base and play activity.</p>
        </div>
      </header>

      {error && <p className="admin-error">{error}</p>}
      {busy && <p className="admin-muted">Loading statistics…</p>}

      {!busy && !error && (
        <>
          <div className="admin-stat-grid">
            <article className="admin-stat">
              <span className="admin-stat-label">Total characters</span>
              <strong className="admin-stat-value">{totals.characters}</strong>
            </article>
            <article className="admin-stat">
              <span className="admin-stat-label">Total questions</span>
              <strong className="admin-stat-value">{totals.questions}</strong>
            </article>
            <article className="admin-stat">
              <span className="admin-stat-label">Games played</span>
              <strong className="admin-stat-value">{stats?.total_games_played ?? 0}</strong>
            </article>
            <article className="admin-stat">
              <span className="admin-stat-label">Learning count</span>
              <strong className="admin-stat-value">{totals.learning}</strong>
            </article>
          </div>

          <div className="admin-grid">
            <div className="admin-card">
              <h3>Guess accuracy</h3>
              <p className="admin-stat-value sm">
                {Math.round((stats?.guess_accuracy_rate || 0) * 100)}%
              </p>
            </div>
            <div className="admin-card">
              <h3>Most asked questions</h3>
              <ul className="admin-list">
                {(stats?.most_asked_questions || []).slice(0, 5).map((q) => (
                  <li key={q.id}>
                    <span>{q.text}</span>
                    <em>{q.times_asked}</em>
                  </li>
                ))}
                {(stats?.most_asked_questions || []).length === 0 && (
                  <li className="admin-muted">No data yet.</li>
                )}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
