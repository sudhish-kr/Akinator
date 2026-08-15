import { useRef, useState } from "react";
import { adminApi } from "../api.js";
import { useI18n } from "../../i18n/index.jsx";

export default function KnowledgePage({ token }) {
  const { t } = useI18n();
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const onExport = async () => {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const data = await adminApi.exportKnowledge(token);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mindguess-knowledge-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setMessage(
        t("admin.exported", {
          chars: data.characters?.length || 0,
          questions: data.questions?.length || 0,
        })
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const onImportFile = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const text = await file.text();
      let payload;
      try {
        payload = JSON.parse(text);
      } catch {
        throw new Error(t("admin.invalidJson"));
      }
      const result = await adminApi.importKnowledge(token, {
        version: payload.version || 1,
        characters: payload.characters || [],
        questions: payload.questions || [],
      });
      setMessage(
        t("admin.imported", {
          chars: result.characters_imported,
          questions: result.questions_imported,
        })
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-panel">
      <header className="admin-panel-head">
        <div>
          <h2>{t("admin.knowledgeTitle")}</h2>
          <p>{t("admin.knowledgeLede")}</p>
        </div>
      </header>

      {error && <p className="admin-error">{error}</p>}
      {message && <p className="admin-success">{message}</p>}

      <div className="admin-grid">
        <div className="admin-card">
          <h3>{t("admin.export")}</h3>
          <p className="admin-muted">{t("admin.exportLede")}</p>
          <button type="button" className="admin-btn primary" disabled={busy} onClick={onExport}>
            {t("admin.downloadJson")}
          </button>
        </div>

        <div className="admin-card">
          <h3>{t("admin.import")}</h3>
          <p className="admin-muted">{t("admin.importLede")}</p>
          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            hidden
            onChange={onImportFile}
          />
          <button
            type="button"
            className="admin-btn ghost"
            disabled={busy}
            onClick={() => fileRef.current?.click()}
          >
            {t("admin.uploadJson")}
          </button>
        </div>
      </div>
    </div>
  );
}
