/** Configurable per-language question text (keyed by canonical English text from the API).
 *  Also softens hard adult words for kids until the DB rename is applied.
 *  Hindi uses exact overrides + pattern templates for natural kid-friendly wording.
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

/** High-traffic exact Hindi overrides (natural, child-friendly). */
const HI_EXACT = {
  "Is this a real person?": "क्या यह एक असली व्यक्ति है?",
  "Is your character a real person?": "क्या आपका किरदार एक असली व्यक्ति है?",
  "Is this a made-up character?": "क्या यह एक बनावटी किरदार है?",
  "Is your character made-up?": "क्या आपका किरदार बनावटी है?",
  "Is this person still alive?": "क्या वे आज जीवित हैं?",
  "Is your character still alive?": "क्या आपका किरदार आज जीवित है?",
  "Are they from India?": "क्या वे भारत से हैं?",
  "Is your character from India?": "क्या आपका किरदार भारत से है?",
  "Is this a sports player?": "क्या वे खिलाड़ी हैं?",
  "Is your character an athlete?": "क्या आपका किरदार खिलाड़ी है?",
  "Does your character play cricket?": "क्या वे क्रिकेट खेलते हैं?",
  "Are they famous for cricket?": "क्या वे क्रिकेट के लिए मशहूर हैं?",
  "Does your character play football?": "क्या वे फ़ुटबॉल खेलते हैं?",
  "Are they famous for football?": "क्या वे फ़ुटबॉल के लिए मशहूर हैं?",
  "Are they famous for soccer?": "क्या वे फ़ुटबॉल के लिए मशहूर हैं?",
  "Is this from anime?": "क्या यह एनिमे से है?",
  "Is your character from anime?": "क्या आपका किरदार एनिमे से है?",
  "Is this from a movie?": "क्या यह फ़िल्म से है?",
  "Is your character from a movie?": "क्या आपका किरदार फ़िल्म से है?",
  "Is this a superhero?": "क्या यह एक सुपरहीरो है?",
  "Is your character a superhero?": "क्या आपका किरदार सुपरहीरो है?",
  "Is your character a man?": "क्या आपका किरदार एक पुरुष है?",
  "Are they a boy or man?": "क्या वे लड़के या पुरुष हैं?",
  "Is your character a woman?": "क्या आपका किरदार एक महिला है?",
  "Are they a girl or woman?": "क्या वे लड़की या महिला हैं?",
  "Is your character famous?": "क्या आपका किरदार मशहूर है?",
  "Are they known today?": "क्या वे आज भी जाने जाते हैं?",
  "Is your character known today?": "क्या आपका किरदार आज भी जाना जाता है?",
  "Are they from African myths?": "क्या वे अफ्रीकी लोककथाओं से हैं?",
  "Is this person a scientist?": "क्या यह व्यक्ति वैज्ञानिक हैं?",
  "Is this a scientist?": "क्या यह एक वैज्ञानिक है?",
  "Is your character a scientist?": "क्या आपका किरदार वैज्ञानिक है?",
  "Is this person an athlete?": "क्या यह व्यक्ति खिलाड़ी हैं?",
  "Is this person alive today?": "क्या यह व्यक्ति आज जीवित हैं?",
  "Is this from a cartoon?": "क्या यह कार्टून से है?",
  "Is this from a TV show?": "क्या यह टीवी शो से है?",
  "Is this from a video game?": "क्या यह वीडियो गेम से है?",
  "Is this from an old legend?": "क्या यह पुरानी लोककथा से है?",
  "Is this from long ago?": "क्या यह बहुत पुराने समय से है?",
  "Is your character from another country?": "क्या आपका किरदार किसी और देश से है?",
  "Are they from another country?": "क्या वे किसी और देश से हैं?",
  "Does your character wear metal armor?": "क्या आपका किरदार धातु का कवच पहनता है?",
  "Does your character cast magic spells?": "क्या आपका किरदार जादुई मंत्र चलाता है?",
  "Does your character solve mysteries?": "क्या आपका किरदार रहस्य सुलझाता है?",
  "Is your character part robot?": "क्या आपका किरदार रोबोट जैसा है?",
  "Did your character win sports gold?": "क्या आपके किरदार ने खेल में सोना जीता?",
  "Is your character a ninja?": "क्या आपका किरदार निंजा है?",
  "Did your character win a science prize?": "क्या आपके किरदार ने विज्ञान का पुरस्कार जीता?",
};

const PLACE = {
  india: "भारत",
  japan: "जापान",
  asia: "एशिया",
  europe: "यूरोप",
  africa: "अफ्रीका",
  australia: "ऑस्ट्रेलिया",
  china: "चीन",
  france: "फ़्रांस",
  germany: "जर्मनी",
  italy: "इटली",
  brazil: "ब्राज़ील",
  argentina: "अर्जेंटीना",
  canada: "कनाडा",
  mexico: "मेक्सिको",
  russia: "रूस",
  egypt: "मिस्र",
  spain: "स्पेन",
  turkey: "तुर्की",
  nigeria: "नाइजीरिया",
  "south korea": "दक्षिण कोरिया",
  "sweden or norway": "स्वीडन या नॉर्वे",
  sweden: "स्वीडन",
  "the united states": "अमेरिका",
  "the united kingdom": "ब्रिटेन",
  "the americas": "अमेरिका महाद्वीप",
  "the middle east": "मध्य पूर्व",
  america: "अमेरिका",
  "the usa": "अमेरिका",
  "the uk": "ब्रिटेन",
  "african myths": "अफ्रीकी लोककथाओं",
  "greek myths": "ग्रीक लोककथाओं",
  "norse myths": "नॉर्स लोककथाओं",
  "egyptian myths": "मिस्र की लोककथाओं",
  "hindu myths": "हिंदू लोककथाओं",
  "chinese myths": "चीनी लोककथाओं",
  "japanese myths": "जापानी लोककथाओं",
  "roman myths": "रोमन लोककथाओं",
  "celtic myths": "केल्टिक लोककथाओं",
  "aztec myths": "एज़टेक लोककथाओं",
  "mayan myths": "माया लोककथाओं",
  "persian myths": "फ़ारसी लोककथाओं",
  "polynesian myths": "पॉलिनेशियन लोककथाओं",
  "inuit myths": "इनुइट लोककथाओं",
  "slavic myths": "स्लाव लोककथाओं",
  "ancient china": "प्राचीन चीन",
  "ancient egypt": "प्राचीन मिस्र",
  "ancient greece or rome": "प्राचीन ग्रीस या रोम",
  "ancient times": "प्राचीन समय",
  "medieval times": "मध्यकाल",
  "viking times": "वाइकिंग समय",
  "victorian times": "विक्टोरियन समय",
};

const NOUN = {
  scientist: "वैज्ञानिक",
  athlete: "खिलाड़ी",
  "sports player": "खिलाड़ी",
  musician: "संगीतकार",
  singer: "गायक",
  actor: "अभिनेता",
  actress: "अभिनेत्री",
  writer: "लेखक",
  teacher: "शिक्षक",
  doctor: "डॉक्टर",
  soldier: "सैनिक",
  pirate: "समुद्री डाकू",
  wizard: "जादूगर",
  "wizard or witch": "जादूगर",
  ninja: "निंजा",
  "ninja or samurai": "निंजा",
  knight: "योद्धा",
  superhero: "सुपरहीरो",
  villain: "खलनायक",
  hero: "हीरो",
  robot: "रोबोट",
  "robot or cyborg": "रोबोट",
  animal: "जानवर",
  "talking animal": "बोलने वाला जानवर",
  alien: "एलियन",
  detective: "जासूस",
  president: "राष्ट्रपति",
  "prime minister": "प्रधानमंत्री",
  "political leader": "राजनीतिक नेता",
  "business leader": "व्यापारिक नेता",
  "business person": "व्यापारी",
  man: "पुरुष",
  woman: "महिला",
  kid: "बच्चा",
  "grown-up": "बड़ा व्यक्ति",
  princess: "राजकुमारी",
  "king or queen": "राजा या रानी",
  "king or prince": "राजा या राजकुमार",
  coach: "कोच",
  "coach, not a player": "कोच (खिलाड़ी नहीं)",
};

const SPORT = {
  cricket: "क्रिकेट",
  football: "फ़ुटबॉल",
  soccer: "फ़ुटबॉल",
  basketball: "बास्केटबॉल",
  tennis: "टेनिस",
  baseball: "बेसबॉल",
  hockey: "हॉकी",
  golf: "गोल्फ़",
  boxing: "मुक्केबाज़ी",
  swimming: "तैराकी",
  running: "दौड़",
  racing: "रेसिंग",
  wrestling: "कुश्ती",
  gymnastics: "जिमनास्टिक्स",
  volleyball: "वॉलीबॉल",
  rugby: "रग्बी",
  cycling: "साइक्लिंग",
  skiing: "स्कीइंग",
  surfing: "सर्फिंग",
  fencing: "फ़ेंसिंग",
  archery: "तीरंदाज़ी",
  "martial arts": "मार्शल आर्ट",
};

function softEn(sourceText) {
  return KID_FRIENDLY_EN[sourceText] || sourceText;
}

function hiPlace(raw) {
  const key = String(raw || "").trim().toLowerCase();
  if (PLACE[key]) return PLACE[key];
  // myths / cartoons keep readable transliteration-ish Hindi wrapper
  if (key.endsWith(" myths")) {
    const base = key.replace(/ myths$/, "");
    return `${PLACE[base] || raw} लोककथाओं`;
  }
  return raw;
}

function hiNoun(raw) {
  const key = String(raw || "").trim().toLowerCase();
  return NOUN[key] || raw;
}

function hiSport(raw) {
  const key = String(raw || "").trim().toLowerCase();
  return SPORT[key] || raw;
}

/** Pattern-based Hindi for questions not in the exact map. */
function translateHiPatterns(text) {
  const t = softEn(text);
  let m;

  m = t.match(/^Are they from (.+)\?$/i);
  if (m) {
    const place = hiPlace(m[1]);
    if (/लोककथा|myth/i.test(m[1]) || /myths$/i.test(m[1])) {
      return `क्या वे ${place} से हैं?`;
    }
    return `क्या वे ${place} से हैं?`;
  }

  m = t.match(/^Is your character from (.+)\?$/i);
  if (m) return `क्या आपका किरदार ${hiPlace(m[1])} से है?`;

  m = t.match(/^Are they famous for (.+)\?$/i);
  if (m) return `क्या वे ${hiSport(m[1])} के लिए मशहूर हैं?`;

  m = t.match(/^Does your character play (.+)\?$/i);
  if (m) return `क्या वे ${hiSport(m[1])} खेलते हैं?`;

  m = t.match(/^Do they play (.+)\?$/i);
  if (m) return `क्या वे ${hiSport(m[1])} खेलते हैं?`;

  m = t.match(/^Are they an? (.+)\?$/i);
  if (m) return `क्या वे ${hiNoun(m[1])} हैं?`;

  m = t.match(/^Is your character an? (.+)\?$/i);
  if (m) return `क्या आपका किरदार ${hiNoun(m[1])} है?`;

  m = t.match(/^Is this an? (.+)\?$/i);
  if (m) return `क्या यह एक ${hiNoun(m[1])} है?`;

  m = t.match(/^Is this from (.+)\?$/i);
  if (m) return `क्या यह ${hiPlace(m[1])} से है?`;

  m = t.match(/^Does your character (.+)\?$/i);
  if (m) {
    const rest = m[1];
    const play = rest.match(/^play (.+)$/i);
    if (play) return `क्या वे ${hiSport(play[1])} खेलते हैं?`;
    const wear = rest.match(/^wear (.+)$/i);
    if (wear) return `क्या वे ${wear[1]} पहनते हैं?`;
    const have = rest.match(/^have (.+)$/i);
    if (have) return `क्या उनके पास ${have[1]} है?`;
    return `क्या आपका किरदार ${rest} है?`;
  }

  m = t.match(/^Do they (.+)\?$/i);
  if (m) return `क्या वे ${m[1]} हैं?`;

  m = t.match(/^Did they win (.+)\?$/i);
  if (m) return `क्या उन्होंने ${m[1]} जीता?`;

  m = t.match(/^Did your character (.+)\?$/i);
  if (m) return `क्या आपके किरदार ने ${m[1]}?`;

  m = t.match(/^Were they (.+)\?$/i);
  if (m) return `क्या वे ${m[1]} थे?`;

  m = t.match(/^Was your character (.+)\?$/i);
  if (m) return `क्या आपका किरदार ${m[1]} था?`;

  m = t.match(/^Can they (.+)\?$/i);
  if (m) return `क्या वे ${m[1]} सकते हैं?`;

  m = t.match(/^Can your character (.+)\?$/i);
  if (m) return `क्या आपका किरदार ${m[1]} सकता है?`;

  m = t.match(/^Are they known for (.+)\?$/i);
  if (m) return `क्या वे ${m[1]} के लिए जाने जाते हैं?`;

  m = t.match(/^Are they linked to (.+)\?$/i);
  if (m) return `क्या उनका संबंध ${m[1]} से है?`;

  m = t.match(/^Are they in (.+)\?$/i);
  if (m) return `क्या वे ${m[1]} में हैं?`;

  m = t.match(/^Is your character (.+)\?$/i);
  if (m) return `क्या आपका किरदार ${m[1]} है?`;

  m = t.match(/^Are they (.+)\?$/i);
  if (m) return `क्या वे ${m[1]} हैं?`;

  return null;
}

export const QUESTION_TRANSLATIONS = {
  en: {
    ...KID_FRIENDLY_EN,
  },
  hi: {
    ...HI_EXACT,
  },
};

/**
 * Resolve question display text for the active language.
 * Falls back to pattern Hindi, then kid-friendly English, then source text.
 */
export function translateQuestion(lang, sourceText) {
  if (!sourceText) return "";
  const softened = softEn(sourceText);
  const table = QUESTION_TRANSLATIONS[lang] || {};

  if (lang === "hi") {
    if (table[sourceText]) return table[sourceText];
    if (table[softened]) return table[softened];
    const patterned = translateHiPatterns(sourceText);
    if (patterned) return patterned;
    const patternedSoft = translateHiPatterns(softened);
    if (patternedSoft) return patternedSoft;
    return softened;
  }

  if (table[sourceText]) return table[sourceText];
  return softened;
}
