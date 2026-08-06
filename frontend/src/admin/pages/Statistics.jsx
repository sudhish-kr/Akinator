import { useEffect, useMemo, useState } from "react";
import { adminApi } from "../api.js";

function pct(rate) {
  return `${Math.round((rate || 0) * 100)}%`;
}

function BarChart({ points }) {
  const max = Math.max(1, ...points.map((p) => p.games));
  const width = 640;
  const height = 180;
  const padX = 12;
  const padY = 16;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const gap = 4;
  const barW = Math.max(6, (innerW - gap * (points.length - 1)) / points.length);

  return (
    <svg
      className="admin-chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Daily games over the last 14 days"
    >
      <line
        x1={padX}
        y1={height - padY}
        x2={width - padX}
        y2={height - padY}
        className="admin-chart-axis"
      />
      {points.map((p, i) => {
        const h = (p.games / max) * innerH;
        const x = padX + i * (barW + gap);
        const y = height - padY - h;
        return (
          <g key={p.date}>
            <rect
              x={x}
              y={y}
              width={barW}
              height={Math.max(h, p.games > 0 ? 2 : 0)}
              rx="3"
              className="admin-chart-bar"
            >
              <title>{`${p.date}: ${p.games} games`}</title>
            </rect>
            {i % 2 === 0 && (
              <text x={x + barW / 2} y={height - 2} textAnchor="middle" className="admin-chart-label">
                {p.date.slice(5)}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function RankBars({ items, valueKey, labelKey }) {
  const max = Math.max(1, ...items.map((item) => item[valueKey] || 0));
  if (!items.length) {
    return <p className="admin-muted">No data yet.</p>;
  }
  return (
    <ul className="admin-rank">
      {items.map((item) => (
        <li key={item.id}>
          <div className="admin-rank-meta">
            <span>{item[labelKey]}</span>
            <em>{item[valueKey]}</em>
          </div>
          <div className="admin-rank-track" aria-hidden="true">
            <span style={{ width: `${((item[valueKey] || 0) / max) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function StatisticsPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setBusy(true);
      setError(null);
      try {
        const statistics = await adminApi.getStatistics();
        if (!cancelled) setStats(statistics);
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

  const daily = useMemo(() => stats?.daily_activity || [], [stats]);

  return (
    <div className="admin-panel">
      <header className="admin-panel-head">
        <div>
          <h2>Analytics</h2>
          <p>Games, learning outcomes, and question demand from live statistics.</p>
        </div>
      </header>

      {error && <p className="admin-error">{error}</p>}
      {busy && <p className="admin-muted">Loading analytics…</p>}

      {!busy && !error && stats && (
        <>
          <div className="admin-stat-grid analytics">
            <article className="admin-stat">
              <span className="admin-stat-label">Total games</span>
              <strong className="admin-stat-value">{stats.total_games_played ?? 0}</strong>
            </article>
            <article className="admin-stat">
              <span className="admin-stat-label">Win rate</span>
              <strong className="admin-stat-value">{pct(stats.guess_accuracy_rate)}</strong>
            </article>
            <article className="admin-stat">
              <span className="admin-stat-label">Learning rate</span>
              <strong className="admin-stat-value">{pct(stats.learning_rate)}</strong>
            </article>
            <article className="admin-stat">
              <span className="admin-stat-label">Avg questions / game</span>
              <strong className="admin-stat-value">
                {(stats.average_questions_per_game ?? 0).toFixed(1)}
              </strong>
            </article>
          </div>

          <div className="admin-card admin-chart-card">
            <h3>Daily activity</h3>
            <p className="admin-muted">Games started per day (last 14 days)</p>
            <BarChart points={daily} />
          </div>

          <div className="admin-grid analytics-grid">
            <div className="admin-card">
              <h3>Most asked questions</h3>
              <RankBars
                items={(stats.most_asked_questions || []).slice(0, 8)}
                valueKey="times_asked"
                labelKey="text"
              />
            </div>
            <div className="admin-card">
              <h3>Most guessed characters</h3>
              <RankBars
                items={(stats.most_guessed_characters || []).slice(0, 8)}
                valueKey="times_guessed"
                labelKey="name"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
