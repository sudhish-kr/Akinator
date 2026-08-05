async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : "{}",
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  startGame: () => post("/game/start"),
  submitAnswer: (sessionId, questionId, answer) =>
    post("/game/answer", { session_id: sessionId, question_id: questionId, answer }),
  makeGuess: (sessionId) => post("/game/guess", { session_id: sessionId }),
  confirmGuess: (sessionId, correct, actualCharacterId = null) =>
    post("/game/guess/confirm", {
      session_id: sessionId,
      correct,
      actual_character_id: actualCharacterId,
    }),
  getState: async (sessionId) => {
    const res = await fetch(`/game/${sessionId}/state`);
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Request failed: ${res.status}`);
    }
    return res.json();
  },
  listCharacters: async () => {
    const res = await fetch("/characters?page_size=100");
    if (!res.ok) throw new Error("Failed to load characters");
    return res.json();
  },
};
