import { useEffect, useState } from "react";
import { adminAuth, adminApi } from "./api.js";
import AdminLogin from "./pages/Login.jsx";
import CharactersPage from "./pages/Characters.jsx";
import QuestionsPage from "./pages/Questions.jsx";
import StatisticsPage from "./pages/Statistics.jsx";

const TABS = [
  { id: "stats", label: "Statistics" },
  { id: "characters", label: "Characters" },
  { id: "questions", label: "Questions" },
];

export default function AdminApp() {
  const [token, setToken] = useState(() => adminAuth.getToken());
  const [user, setUser] = useState(() => adminAuth.getUser());
  const [tab, setTab] = useState("stats");

  useEffect(() => {
    if (user && user.role !== "admin") {
      adminAuth.clear();
      setToken(null);
      setUser(null);
    }
  }, [user]);

  const onLogin = (data) => {
    setToken(data.access_token);
    setUser(data.user);
    setTab("stats");
  };

  const onLogout = async () => {
    await adminApi.logout(token);
    setToken(null);
    setUser(null);
  };

  if (!token || !user) {
    return <AdminLogin onSuccess={onLogin} />;
  }

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <span className="admin-brand-mark">MG</span>
          <div>
            <strong>MindGuess</strong>
            <small>Knowledge admin</small>
          </div>
        </div>

        <nav className="admin-nav">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={tab === t.id ? "active" : undefined}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-foot">
          <p className="admin-user">{user.username}</p>
          <button type="button" className="admin-btn ghost block" onClick={onLogout}>
            Log out
          </button>
          <a className="admin-back" href="#/">
            ← Game client
          </a>
        </div>
      </aside>

      <main className="admin-main">
        {tab === "stats" && <StatisticsPage />}
        {tab === "characters" && <CharactersPage token={token} />}
        {tab === "questions" && <QuestionsPage token={token} />}
      </main>
    </div>
  );
}
