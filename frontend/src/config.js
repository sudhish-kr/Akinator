/** API origin from Vite env (no trailing slash). Empty = same-origin. */
export const API_BASE_URL = String(import.meta.env.VITE_API_BASE_URL || "").replace(
  /\/$/,
  ""
);

/** Build absolute request URL from a path starting with `/`. */
export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}
