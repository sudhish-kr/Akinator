/** Browser speech helpers — no backend. */

export function speechRecognitionSupported() {
  return typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function ttsSupported() {
  return typeof window !== "undefined" && !!window.speechSynthesis;
}

export function speechLocale(lang) {
  return lang === "hi" ? "hi-IN" : "en-US";
}

export function speakText(text, { lang = "en", rate = 1 } = {}) {
  if (!ttsSupported() || !text) return Promise.resolve();
  return new Promise((resolve) => {
    const synth = window.speechSynthesis;
    synth.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = speechLocale(lang);
    utter.rate = rate;
    utter.onend = () => resolve();
    utter.onerror = () => resolve();
    synth.speak(utter);
  });
}

export function stopSpeaking() {
  if (ttsSupported()) window.speechSynthesis.cancel();
}

/**
 * Map free-form speech to an answer enum value, or null if unrecognized.
 */
export function parseSpeechAnswer(transcript, lang = "en") {
  const raw = String(transcript || "").trim().toLowerCase();
  if (!raw) return null;

  const hi = lang === "hi";
  const compact = raw.replace(/[.,!?]/g, " ").replace(/\s+/g, " ").trim();

  const has = (...parts) => parts.some((p) => compact.includes(p));

  if (
    has("don't know", "dont know", "do not know", "not sure", "no idea", "skip", "unknown") ||
    (hi && has("पता नहीं", "मालूम नहीं", "नहीं पता", "पता नही"))
  ) {
    return "dont_know";
  }

  if (
    has("probably not", "probably no", "maybe not", "unlikely") ||
    (hi && has("शायद नहीं", "शायद नही"))
  ) {
    return "probably_no";
  }

  if (
    has("probably yes", "probably", "maybe yes", "likely") ||
    (hi && has("शायद हाँ", "शायद हां", "शायद"))
  ) {
    // bare "शायद" / "probably" → probably_yes when not already "probably not"
    if (has("probably not", "probably no") || (hi && has("शायद नहीं", "शायद नही"))) {
      return "probably_no";
    }
    return "probably_yes";
  }

  // Exact-ish yes/no — prefer whole-word-ish checks
  if (
    /^(yes|yeah|yep|yup|correct|true)$/i.test(compact) ||
    has(" yes") ||
    compact.startsWith("yes ") ||
    (hi && (has("हाँ", "हां", "जी हाँ", "जी हां") || compact === "जी"))
  ) {
    return "yes";
  }

  if (
    /^(no|nope|nah|false)$/i.test(compact) ||
    has(" no") ||
    compact.startsWith("no ") ||
    (hi && has("नहीं", "नही", "ना"))
  ) {
    return "no";
  }

  return null;
}

export function createRecognizer({ lang, onResult, onError, onEnd }) {
  const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Ctor) return null;
  const recognition = new Ctor();
  recognition.lang = speechLocale(lang);
  recognition.interimResults = false;
  recognition.maxAlternatives = 3;
  recognition.continuous = false;

  recognition.onresult = (event) => {
    const results = event.results?.[0];
    if (!results) return;
    const texts = [];
    for (let i = 0; i < results.length; i += 1) {
      texts.push(results[i].transcript);
    }
    onResult?.(texts);
  };
  recognition.onerror = (event) => onError?.(event.error || "speech_error");
  recognition.onend = () => onEnd?.();
  return recognition;
}
