/**
 * Client-side answer trail for Back / edit navigation.
 *
 * The backend has no undo API and only accepts the pending question.
 * Back uses local trail snapshots. Changing an answer restarts a session
 * and replays the kept answers through the existing start/answer APIs.
 */

export function pushTrail(trail, step) {
  if (!step?.question?.id || !step.answer) return trail;
  return [
    ...trail,
    {
      question: step.question,
      questionNumber: step.questionNumber,
      confidence: step.confidence ?? 0,
      answer: step.answer,
    },
  ];
}

export function canGoBack(trail, editIndex) {
  if (!Array.isArray(trail) || trail.length === 0) return false;
  if (editIndex == null) return true;
  return editIndex > 0;
}

/** Move one step back in the trail. Returns next editIndex or null. */
export function backEditIndex(trail, editIndex) {
  if (!canGoBack(trail, editIndex)) return null;
  if (editIndex == null) return trail.length - 1;
  return editIndex - 1;
}

/** Answers to replay when revising trail[editIndex] to newAnswer. */
export function answersForReplay(trail, editIndex, newAnswer) {
  if (!Array.isArray(trail) || editIndex == null || editIndex < 0) return [];
  const kept = trail.slice(0, editIndex).map((s) => s.answer);
  return [...kept, newAnswer];
}

/** @deprecated Prefer pushTrail — kept for older imports/tests. */
export function pushHistory(history, snapshot) {
  return pushTrail(history, snapshot);
}

export function popHistory(history) {
  if (!Array.isArray(history) || history.length === 0) return null;
  const next = history.slice(0, -1);
  const snapshot = history[history.length - 1];
  return { history: next, snapshot };
}
