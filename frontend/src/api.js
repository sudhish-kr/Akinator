async function request(method, path, body) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) options.body = JSON.stringify(body);
  const res = await fetch(path, options);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const message =
      typeof detail.detail === "string"
        ? detail.detail
        : detail.detail
          ? JSON.stringify(detail.detail)
          : `Request failed: ${res.status}`;
    throw new Error(message);
  }
  if (res.status === 204) return null;
  return res.json();
}

/** Game API — only the documented game endpoints. */
export const api = {
  startGame: () => request("POST", "/game/start"),

  submitAnswer: (sessionId, questionId, answer) =>
    request("POST", "/game/answer", {
      session_id: sessionId,
      question_id: questionId,
      answer,
    }),

  getState: (sessionId) => request("GET", `/game/state/${sessionId}`),

  getGuess: (sessionId) => request("GET", `/game/guess/${sessionId}`),

  learn: (sessionId, characterId, { wrongGuess = false } = {}) =>
    request("POST", "/game/learn", {
      session_id: sessionId,
      character_id: characterId,
      wrong_guess: wrongGuess,
    }),

  /** Character list for the Learn page picker (existing public API). */
  listCharacters: () => request("GET", "/characters?is_active=true&page_size=100"),
};
