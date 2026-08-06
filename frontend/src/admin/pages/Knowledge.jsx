import { useRef, useState } from "react";
import { adminApi } from "../api.js";

export default function KnowledgePage({ token }) {
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
        `Exported ${data.characters?.length || 0} characters and ${data.questions?.length || 0} questions.`
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
        throw new Error("Invalid JSON file");
      }
      const result = await adminApi.importKnowledge(token, {
        version: payload.version || 1,
        characters: payload.characters || [],
        questions: payload.questions || [],
      });
      setMessage(
        `Imported ${result.characters_imported} characters and ${result.questions_imported} questions.`
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
          <h2>Knowledge import / export</h2>
          <p>Download or upload characters and questions as JSON. Imports reject duplicates.</p>
        </div>
      </header>

      {error && <p className="admin-error">{error}</p>}
      {message && <p className="admin-success">{message}</p>}

      <div className="admin-grid">
        <div className="admin-card">
          <h3>Export</h3>
          <p className="admin-muted">All characters and questions as a JSON file.</p>
          <button type="button" className="admin-btn primary" disabled={busy} onClick={onExport}>
            Download JSON
          </button>
        </div>

        <div className="admin-card">
          <h3>Import</h3>
          <p className="admin-muted">
            Validates payload shape, rejects duplicate names/texts, and rolls back on failure.
          </p>
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
            Upload JSON
          </button>
        </div>
      </div>
    </div>
  );
}
