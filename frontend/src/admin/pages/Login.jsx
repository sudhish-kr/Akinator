import { useState } from "react";
import { adminApi, adminAuth } from "../api.js";
import { LanguageSwitch, useI18n } from "../../i18n/index.jsx";

export default function AdminLogin({ onSuccess }) {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const data = await adminApi.login(email.trim(), password);
      if (data.user?.role !== "admin") {
        throw new Error(t("admin.adminRequired"));
      }
      adminAuth.saveSession(data);
      onSuccess(data);
    } catch (err) {
      setError(err.message || t("admin.loginFailed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="admin-login">
      <div className="admin-login-card">
        <LanguageSwitch className="lang-switch-admin" />
        <p className="admin-kicker">{t("admin.loginKicker")}</p>
        <h1>{t("admin.loginTitle")}</h1>
        <p className="admin-lede">{t("admin.loginLede")}</p>
        <form onSubmit={submit} className="admin-form">
          <label>
            {t("admin.email")}
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            {t("admin.password")}
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </label>
          {error && <p className="admin-error">{error}</p>}
          <button type="submit" className="admin-btn primary" disabled={busy}>
            {busy ? t("admin.signingIn") : t("admin.signIn")}
          </button>
        </form>
        <a className="admin-back" href="#/">
          {t("admin.backToGame")}
        </a>
      </div>
    </section>
  );
}
