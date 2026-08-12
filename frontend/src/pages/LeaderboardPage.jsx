import { t } from "../i18n.js";

export default function LeaderboardPage({ lang, entries, onBack }) {
  return (
    <section className="page leaderboard">
      <p className="kicker">{t(lang, "leaderboard")}</p>
      <h2 className="title">{t(lang, "leaderboardTitle")}</h2>
      <p className="lede">{t(lang, "leaderboardLede")}</p>

      {entries.length === 0 ? (
        <p className="muted">{t(lang, "leaderboardEmpty")}</p>
      ) : (
        <div className="lb-table-wrap">
          <table className="lb-table">
            <thead>
              <tr>
                <th>{t(lang, "rank")}</th>
                <th>{t(lang, "player")}</th>
                <th>{t(lang, "result")}</th>
                <th>{t(lang, "questionsCol")}</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((row, i) => (
                <tr key={row.id}>
                  <td>{i + 1}</td>
                  <td>{row.name}</td>
                  <td>{row.result}</td>
                  <td>{row.questions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button type="button" className="btn primary" onClick={onBack}>
        {t(lang, "backToGame")}
      </button>
    </section>
  );
}
