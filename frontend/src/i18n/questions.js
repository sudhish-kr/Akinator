/** Configurable per-language question text (keyed by canonical English text from the API).
 *  Add or edit entries here — no backend changes required.
 *
 *  Also softens hard adult words for kids until the DB rename is applied.
 */
const KID_FRIENDLY_EN = {
  "Are they a knight?": "Does your character wear metal armor?",
  "Is your character a knight?": "Does your character wear metal armor?",
  "Are they a wizard?": "Does your character cast magic spells?",
  "Is your character a wizard?": "Does your character cast magic spells?",
  "Are they a detective?": "Does your character solve mysteries?",
  "Is your character a detective?": "Does your character solve mysteries?",
  "Are they a robot or cyborg?": "Is your character part robot?",
  "Is your character a robot or cyborg?": "Is your character part robot?",
  "Are they an Olympic winner?": "Did your character win sports gold?",
  "Is your character an Olympic winner?": "Did your character win sports gold?",
  "Are they a ninja or samurai?": "Is your character a ninja?",
  "Did they win a Nobel science prize?": "Did your character win a science prize?",
};

export const QUESTION_TRANSLATIONS = {
  en: {
    ...KID_FRIENDLY_EN,
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
    "Are they a knight?": "क्या आपका किरदार धातु का कवच पहनता है?",
    "Does your character wear metal armor?": "क्या आपका किरदार धातु का कवच पहनता है?",
  },
};

/**
 * Resolve question display text for the active language.
 * Falls back to the source (API) text when no translation is configured.
 */
export function translateQuestion(lang, sourceText) {
  if (!sourceText) return "";
  const table = QUESTION_TRANSLATIONS[lang] || {};
  if (table[sourceText]) return table[sourceText];
  // English kid-friendly softens even when lang table has no entry.
  if (KID_FRIENDLY_EN[sourceText]) return KID_FRIENDLY_EN[sourceText];
  return sourceText;
}
