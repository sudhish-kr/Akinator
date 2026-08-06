import { useState } from "react";
import { adminApi, adminAuth } from "../api.js";

export default function AdminLogin({ onSuccess }) {
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
        throw new Error("Admin role required");
      }
      adminAuth.saveSession(data);
      onSuccess(data);
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="admin-login">
      <div className="admin-login-card">
        <p className="admin-kicker">Knowledge console</p>
        <h1>Admin sign in</h1>
        <p className="admin-lede">Manage characters, questions, and learning stats.</p>
        <form onSubmit={submit} className="admin-form">
          <label>
            Email
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Password
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
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <a className="admin-back" href="#/">
          ← Back to game
        </a>
      </div>
    </section>
  );
}
