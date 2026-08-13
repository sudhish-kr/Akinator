/** FastAPI origin. Never fall back to the Vite page origin (e.g. :5173/:5174). */
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const API_BASE_URL = String(
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

/** Build absolute request URL from a path starting with `/`. */
export function apiUrl(path) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}
