/** Configurable per-language question text (keyed by canonical English text from the API).
 *  Add or edit entries here — no backend changes required.
 */
export const QUESTION_TRANSLATIONS = {
  en: {
    // English uses the API/source text by default; optional overrides:
    // "Is this person a scientist?": "Is this person a scientist?",
  },
  hi: {
    "Is this person a scientist?": "क्या यह व्यक्ति वैज्ञानिक हैं?",
    "Did this person win a Nobel Prize?": "क्या इस व्यक्ति ने नोबेल पुरस्कार जीता?",
    "Is this person an athlete?": "क्या यह व्यक्ति खिलाड़ी हैं?",
    "Is this person alive today?": "क्या यह व्यक्ति आज जीवित हैं?",
    "Is this person known for technology or business?":
      "क्या यह व्यक्ति तकनीक या व्यापार के लिए जाने जाते हैं?",
    "Did this person live before 1900?": "क्या यह व्यक्ति 1900 से पहले जीवित थे?",
    "Is this person a composer?": "क्या यह व्यक्ति संगीतकार हैं?",
  },
};

/**
 * Resolve question display text for the active language.
 * Falls back to the source (API) text when no translation is configured.
 */
export function translateQuestion(lang, sourceText) {
  if (!sourceText) return "";
  const table = QUESTION_TRANSLATIONS[lang] || {};
  return table[sourceText] || sourceText;
}
