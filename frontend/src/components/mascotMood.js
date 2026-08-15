/**
 * Lightweight mascot mood controller — frontend-only.
 * Reacts to busy/listening/confidence/answers without extra API calls.
 */

const VALID = new Set([
  "idle",
  "thinking",
  "listening",
  "happy",
  "confused",
  "excited",
  "surprised",
  "sad",
  "curious",
]);

const GAZE = {
  yes: { x: 3.2, y: -1.2 },
  probably_yes: { x: 2.4, y: -0.4 },
  dont_know: { x: 0, y: 0 },
  probably_no: { x: -2.2, y: 0.2 },
  no: { x: -3.0, y: 1.0 },
  question: { x: 4.5, y: -0.6 },
  center: { x: 0, y: 0 },
};

const REACTION_MS = 520;
const CURIOUS_MS = 480;
const HIGH_CONF = 0.42;
const LOW_CONF = 0.06;

export function classifyQuestionCue(text = "") {
  const t = String(text).toLowerCase();
  if (/(from |country|india|japan|europe|usa|united|asia|australia)/.test(t)) {
    return "country";
  }
  if (/(sport|athlete|cricket|tennis|football|soccer|basketball|boxing)/.test(t)) {
    return "sports";
  }
  if (/(real person|alive|woman|man|famous|fictional|made-up)/.test(t)) {
    return "identity";
  }
  return "default";
}

export function messageKeyForState(state, { answer, cue, confidence } = {}) {
  if (state === "thinking") {
    return answer === "dont_know" ? "mascot.thinkingSoft" : "mascot.thinking";
  }
  if (state === "curious") {
    if (cue === "country") return "mascot.curiousCountry";
    if (cue === "sports") return "mascot.curiousSports";
    if (cue === "identity") return "mascot.curiousIdentity";
    return "mascot.curious";
  }
  if (state === "happy") {
    return answer === "yes" ? "mascot.happyYes" : "mascot.happy";
  }
  if (state === "confused") {
    return answer === "no" || answer === "probably_no" ? "mascot.narrowing" : "mascot.confused";
  }
  if (state === "excited") {
    if (confidence != null && confidence >= HIGH_CONF) return "mascot.highConfidence";
    return "mascot.excited";
  }
  if (state === "listening") return "mascot.listening";
  if (state === "surprised") return "mascot.wrong";
  if (state === "sad") return "mascot.sad";
  if (state === "idle") {
    if (confidence != null && confidence < LOW_CONF) return "mascot.lowConfidence";
    return "mascot.idle";
  }
  return `mascot.${state}`;
}

export function reactionAfterAnswer(answer) {
  switch (answer) {
    case "yes":
      return "happy";
    case "probably_yes":
      return "curious";
    case "dont_know":
      return "listening";
    case "probably_no":
      return "confused";
    case "no":
      return "confused";
    default:
      return "idle";
  }
}

export function reactionMessageKey(answer) {
  switch (answer) {
    case "yes":
      return "mascot.happyYes";
    case "no":
    case "probably_no":
      return "mascot.narrowing";
    case "probably_yes":
      return "mascot.probably";
    case "dont_know":
      return "mascot.dontKnow";
    default:
      return "mascot.idle";
  }
}

/**
 * Pure helper used by GamePage — keeps timers outside when possible.
 */
export function resolveBaseMood({ busy, listening, confidence, override }) {
  if (override && VALID.has(override)) return override;
  if (busy) return "thinking";
  if (listening) return "listening";
  if (typeof confidence === "number" && confidence >= HIGH_CONF) return "excited";
  return "idle";
}

export { GAZE, REACTION_MS, CURIOUS_MS, HIGH_CONF, LOW_CONF, VALID };
