/** FastAPI origin. Never fall back to the Vite page origin (e.g. :5173/:5174). */
const DEFAULT_API_BASE_URL = "https://mindguess-yebm.onrender.com";

const viteEnv =
  typeof import.meta !== "undefined" && import.meta.env ? import.meta.env : {};

export const API_BASE_URL = String(
  viteEnv.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/$/, "");

export const DEFAULT_CHARACTER_IMAGE = "/media/characters/default.svg";

/** Build absolute request URL from a path starting with `/`. */
export function apiUrl(path) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

/** Resolve a stored media path (or fall back to the default placeholder). */
export function mediaUrl(path) {
  if (!path) return apiUrl(DEFAULT_CHARACTER_IMAGE);
  if (/^https?:\/\//i.test(path)) return path;
  return apiUrl(path.startsWith("/") ? path : `/${path}`);
}
