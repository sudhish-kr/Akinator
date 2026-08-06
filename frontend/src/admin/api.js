import { apiUrl } from "../config.js";

const TOKEN_KEY = "mg_admin_token";
const USER_KEY = "mg_admin_user";

async function request(method, path, { body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(apiUrl(path), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const message =
      typeof detail.detail === "string"
        ? detail.detail
        : detail.detail
          ? JSON.stringify(detail.detail)
          : `Request failed: ${res.status}`;
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const adminAuth = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  getUser: () => {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || "null");
    } catch {
      return null;
    }
  },
  saveSession: (data) => {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

/** Authenticated admin API client (existing endpoints only). */
export const adminApi = {
  login: (email, password) =>
    request("POST", "/auth/login", { body: { email, password } }),

  logout: async (token) => {
    try {
      await request("POST", "/auth/logout", { token, body: {} });
    } finally {
      adminAuth.clear();
    }
  },

  listCharacters: (params = {}) => {
    const q = new URLSearchParams({ page: "1", page_size: "100", ...params });
    return request("GET", `/characters?${q}`);
  },

  createCharacter: (token, body) =>
    request("POST", "/admin/characters", { token, body }),

  updateCharacter: (token, id, body) =>
    request("PATCH", `/admin/characters/${id}`, { token, body }),

  /** Soft-delete via existing PATCH (is_active=false). */
  deleteCharacter: (token, id) =>
    request("PATCH", `/admin/characters/${id}`, { token, body: { is_active: false } }),

  listQuestions: (params = {}) => {
    const q = new URLSearchParams({ page: "1", page_size: "100", ...params });
    return request("GET", `/questions?${q}`);
  },

  createQuestion: (token, body) =>
    request("POST", "/admin/questions", { token, body }),

  updateQuestion: (token, id, body) =>
    request("PATCH", `/admin/questions/${id}`, { token, body }),

  /** Soft-delete via existing PATCH (is_active=false). */
  deleteQuestion: (token, id) =>
    request("PATCH", `/admin/questions/${id}`, { token, body: { is_active: false } }),

  getStatistics: () => request("GET", "/statistics"),
};
