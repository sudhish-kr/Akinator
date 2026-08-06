import { useEffect, useMemo, useState } from "react";
import { adminApi } from "../api.js";

const emptyForm = { text: "", category: "", is_active: true };

export default function QuestionsPage({ token }) {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);

  const load = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await adminApi.listQuestions();
      setItems(data.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (item) =>
        item.text.toLowerCase().includes(q) ||
        (item.category || "").toLowerCase().includes(q)
    );
  }, [items, search]);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const startEdit = (item) => {
    setEditingId(item.id);
    setForm({
      text: item.text,
      category: item.category || "",
      is_active: item.is_active,
    });
  };

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const payload = {
      text: form.text.trim(),
      category: form.category.trim() || null,
      is_active: form.is_active,
    };
    try {
      if (editingId) {
        await adminApi.updateQuestion(token, editingId, payload);
      } else {
        await adminApi.createQuestion(token, payload);
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!confirm("Deactivate this question?")) return;
    setBusy(true);
    setError(null);
    try {
      await adminApi.deleteQuestion(token, id);
      if (editingId === id) resetForm();
      await load();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="admin-panel">
      <header className="admin-panel-head">
        <div>
          <h2>Questions</h2>
          <p>Curate the question bank used by the guessing engine.</p>
        </div>
        <input
          className="admin-search"
          placeholder="Search question text…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </header>

      {error && <p className="admin-error">{error}</p>}

      <div className="admin-grid">
        <form className="admin-card admin-form" onSubmit={save}>
          <h3>{editingId ? "Edit question" : "Create question"}</h3>
          <label>
            Text
            <textarea
              rows={3}
              value={form.text}
              onChange={(e) => setForm({ ...form, text: e.target.value })}
              required
              minLength={5}
            />
          </label>
          <label>
            Category
            <input
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            />
          </label>
          <label className="admin-check">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            />
            Active
          </label>
          <div className="admin-actions">
            <button type="submit" className="admin-btn primary" disabled={busy}>
              {editingId ? "Save changes" : "Create"}
            </button>
            {editingId && (
              <button type="button" className="admin-btn ghost" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="admin-card admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Question</th>
                <th>Asked</th>
                <th>Active</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((q) => (
                <tr key={q.id} className={!q.is_active ? "muted-row" : undefined}>
                  <td>
                    <div className="admin-q-text">{q.text}</div>
                    {q.category && <span className="admin-tag">{q.category}</span>}
                  </td>
                  <td>{q.times_asked}</td>
                  <td>{q.is_active ? "Yes" : "No"}</td>
                  <td className="admin-row-actions">
                    <button type="button" className="admin-link" onClick={() => startEdit(q)}>
                      Edit
                    </button>
                    {q.is_active && (
                      <button type="button" className="admin-link danger" onClick={() => remove(q.id)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4}>{busy ? "Loading…" : "No questions found."}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
