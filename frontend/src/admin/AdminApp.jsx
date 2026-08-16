import { useEffect, useState } from "react";
import { adminAuth, adminApi } from "./api.js";
import "./admin.css";
import { LanguageSwitch, useI18n } from "../i18n/index.jsx";
import AdminLogin from "./pages/Login.jsx";
import CharactersPage from "./pages/Characters.jsx";
import QuestionsPage from "./pages/Questions.jsx";
import StatisticsPage from "./pages/Statistics.jsx";
import KnowledgePage from "./pages/Knowledge.jsx";

export default function AdminApp() {
  const { t } = useI18n();
  const [token, setToken] = useState(() => adminAuth.getToken());
  const [user, setUser] = useState(() => adminAuth.getUser());
  const [tab, setTab] = useState("stats");

  const tabs = [
    { id: "stats", label: t("admin.tabAnalytics") },
    { id: "characters", label: t("admin.tabCharacters") },
    { id: "questions", label: t("admin.tabQuestions") },
    { id: "knowledge", label: t("admin.tabKnowledge") },
  ];

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
            <strong>{t("admin.brand")}</strong>
            <small>{t("admin.brandSub")}</small>
          </div>
        </div>

        <LanguageSwitch className="lang-switch-admin" />

        <nav className="admin-nav">
          {tabs.map((item) => (
            <button
              key={item.id}
              type="button"
              className={tab === item.id ? "active" : undefined}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-foot">
          <p className="admin-user">{user.username}</p>
          <button type="button" className="admin-btn ghost block" onClick={onLogout}>
            {t("admin.logout")}
          </button>
          <a className="admin-back" href="#/">
            {t("admin.backGame")}
          </a>
        </div>
      </aside>

      <main className="admin-main">
        {tab === "stats" && <StatisticsPage />}
        {tab === "characters" && <CharactersPage token={token} />}
        {tab === "questions" && <QuestionsPage token={token} />}
        {tab === "knowledge" && <KnowledgePage token={token} />}
      </main>
    </div>
  );
}
