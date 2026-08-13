/**
 * Client-side question history for Back navigation.
 * Backend has no undo API — Back restores prior UI snapshots only (no fetch).
 */

export function pushHistory(history, snapshot) {
  if (!snapshot?.question?.id) return history;
  return [...history, {
    question: snapshot.question,
    questionNumber: snapshot.questionNumber,
    confidence: snapshot.confidence ?? 0,
  }];
}

export function canGoBack(history) {
  return Array.isArray(history) && history.length > 0;
}

/** Pop last snapshot; returns { history, snapshot } or null if empty. */
export function popHistory(history) {
  if (!canGoBack(history)) return null;
  const next = history.slice(0, -1);
  const snapshot = history[history.length - 1];
  return { history: next, snapshot };
}
