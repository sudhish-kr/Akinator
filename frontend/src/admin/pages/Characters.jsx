import { useEffect, useMemo, useRef, useState } from "react";
import { adminApi } from "../api.js";
import { mediaUrl } from "../../config.js";

const emptyForm = { name: "", category: "real_person", image_url: "", is_active: true };

export default function CharactersPage({ token }) {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [pendingFile, setPendingFile] = useState(null);
  const fileRef = useRef(null);

  const load = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await adminApi.listCharacters();
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
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.category || "").toLowerCase().includes(q)
    );
  }, [items, search]);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setPendingFile(null);
    if (fileRef.current) fileRef.current.value = "";
  };

  const startEdit = (c) => {
    setEditingId(c.id);
    setPendingFile(null);
    if (fileRef.current) fileRef.current.value = "";
    setForm({
      name: c.name,
      category: c.category,
      image_url: c.image_url || "",
      is_active: c.is_active,
    });
  };

  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const payload = {
      name: form.name.trim(),
      category: form.category.trim(),
      image_url: form.image_url.trim() || null,
      is_active: form.is_active,
    };
    try {
      let id = editingId;
      if (editingId) {
        await adminApi.updateCharacter(token, editingId, payload);
      } else {
        const created = await adminApi.createCharacter(token, payload);
        id = created.id;
      }
      if (pendingFile && id) {
        await adminApi.uploadCharacterImage(token, id, pendingFile);
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!confirm("Deactivate this character?")) return;
    setBusy(true);
    setError(null);
    try {
      await adminApi.deleteCharacter(token, id);
      if (editingId === id) resetForm();
      await load();
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
          <h2>Characters</h2>
          <p>List, search, create, edit, upload images, and deactivate knowledge entries.</p>
        </div>
        <input
          className="admin-search"
          placeholder="Search name or category…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </header>

      {error && <p className="admin-error">{error}</p>}

      <div className="admin-grid">
        <form className="admin-card admin-form" onSubmit={save}>
          <h3>{editingId ? "Edit character" : "Create character"}</h3>
          <div className="admin-image-preview">
            <img src={mediaUrl(form.image_url)} alt="" />
          </div>
          <label>
            Name
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </label>
          <label>
            Category
            <input
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              required
            />
          </label>
          <label>
            Image upload
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={(e) => setPendingFile(e.target.files?.[0] || null)}
            />
          </label>
          <p className="admin-muted">
            JPEG/PNG/WebP/GIF up to 2MB. Stored path is saved on the character.
          </p>
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
                <th />
                <th>Name</th>
                <th>Category</th>
                <th>Active</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className={!c.is_active ? "muted-row" : undefined}>
                  <td>
                    <img className="admin-thumb" src={mediaUrl(c.image_url)} alt="" />
                  </td>
                  <td>{c.name}</td>
                  <td>{c.category}</td>
                  <td>{c.is_active ? "Yes" : "No"}</td>
                  <td className="admin-row-actions">
                    <button type="button" className="admin-link" onClick={() => startEdit(c)}>
                      Edit
                    </button>
                    {c.is_active && (
                      <button type="button" className="admin-link danger" onClick={() => remove(c.id)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5}>{busy ? "Loading…" : "No characters found."}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
