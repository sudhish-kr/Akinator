/** UI + question translations. Questions keyed by English API text (IDs are UUIDs). */

const UI = {
  en: {
    kicker: "20 questions · Bayesian mind",
    lede: "Think of a character. Answer each question. I will narrow the field until only one remains.",
    startGame: "Start game",
    connecting: "Connecting…",
    adminDashboard: "Admin dashboard",
    leaderboard: "Leaderboard",
    language: "Language",
    english: "English",
    hindi: "हिन्दी",
    question: "Question",
    confidence: "Confidence",
    back: "Back",
    previous: "Previous",
    next: "Next",
    endGame: "End Game",
    endGameTitle: "Are you sure you want to end the game?",
    continueGame: "Continue Game",
    confirmEnd: "End Game",
    yourAnswer: "Your answer",
    selectedAnswer: "Your answer",
    yes: "Yes",
    probably: "Probably",
    dontKnow: "Don't know",
    probablyNot: "Probably not",
    no: "No",
    finalRead: "Final read",
    confident: "confident",
    isThisWho: "Is this who you were thinking of?",
    yesGotIt: "Yes — you got it",
    noTeachMe: "No — teach me",
    learning: "Learning",
    whoWasIt: "Who was it?",
    notNameChoose: (name) =>
      `Not ${name}. Choose the correct character so I can update my model.`,
    chooseCorrect: "Choose the correct character so I can update my model.",
    noCharacters: "No active characters available.",
    backToHome: "Back to home",
    roundComplete: "Round complete",
    playAgain: "Play again",
    home: "Home",
    nailedIt: (name) => `Nailed it — ${name}.`,
    learnedNamed: (name) => `Learned — next time I’ll look for ${name}.`,
    learned: "Learned from that round.",
    leaderboardTitle: "Leaderboard",
    leaderboardLede: "Top runs on this device. Scores appear after you finish a game.",
    leaderboardEmpty: "No scores yet. Finish a game to appear here.",
    rank: "Rank",
    player: "Player",
    result: "Result",
    questionsCol: "Questions",
    backToGame: "Back to game",
    somethingWrong: "Something went wrong",
  },
  hi: {
    kicker: "२० प्रश्न · बायेसियन माइंड",
    lede: "एक पात्र सोचें। प्रत्येक प्रश्न का उत्तर दें। मैं क्षेत्र को तब तक संकीर्ण करूँगा जब तक एक ही न बचे।",
    startGame: "खेल शुरू करें",
    connecting: "कनेक्ट हो रहा है…",
    adminDashboard: "एडमिन डैशबोर्ड",
    leaderboard: "लीडरबोर्ड",
    language: "भाषा",
    english: "English",
    hindi: "हिन्दी",
    question: "प्रश्न",
    confidence: "विश्वास",
    back: "वापस",
    previous: "पिछला",
    next: "अगला",
    endGame: "खेल समाप्त",
    endGameTitle: "क्या आप वाकई खेल समाप्त करना चाहते हैं?",
    continueGame: "खेल जारी रखें",
    confirmEnd: "खेल समाप्त",
    yourAnswer: "आपका उत्तर",
    selectedAnswer: "आपका उत्तर",
    yes: "हाँ",
    probably: "शायद हाँ",
    dontKnow: "पता नहीं",
    probablyNot: "शायद नहीं",
    no: "नहीं",
    finalRead: "अंतिम अनुमान",
    confident: "विश्वास",
    isThisWho: "क्या आप इसी के बारे में सोच रहे थे?",
    yesGotIt: "हाँ — सही है",
    noTeachMe: "नहीं — मुझे सिखाएँ",
    learning: "सीखना",
    whoWasIt: "यह कौन था?",
    notNameChoose: (name) =>
      `${name} नहीं। सही पात्र चुनें ताकि मैं अपना मॉडल अपडेट कर सकूँ।`,
    chooseCorrect: "सही पात्र चुनें ताकि मैं अपना मॉडल अपडेट कर सकूँ।",
    noCharacters: "कोई सक्रिय पात्र उपलब्ध नहीं।",
    backToHome: "होम पर वापस",
    roundComplete: "राउंड पूरा",
    playAgain: "फिर से खेलें",
    home: "होम",
    nailedIt: (name) => `बिल्कुल सही — ${name}।`,
    learnedNamed: (name) => `सीखा — अगली बार मैं ${name} को ढूँढूँगा।`,
    learned: "उस राउंड से सीखा।",
    leaderboardTitle: "लीडरबोर्ड",
    leaderboardLede: "इस डिवाइस पर शीर्ष स्कोर। खेल खत्म होने पर स्कोर दिखेंगे।",
    leaderboardEmpty: "अभी कोई स्कोर नहीं। लीडरबोर्ड में आने के लिए एक खेल पूरा करें।",
    rank: "रैंक",
    player: "खिलाड़ी",
    result: "परिणाम",
    questionsCol: "प्रश्न",
    backToGame: "खेल पर वापस",
    somethingWrong: "कुछ गलत हो गया",
  },
};

/** Hindi for known question English text from API / seed / common bank. */
const QUESTION_HI = {
  "Is this person a scientist?": "क्या यह व्यक्ति एक वैज्ञानिक है?",
  "Did this person win a Nobel Prize?": "क्या इस व्यक्ति ने नोबेल पुरस्कार जीता?",
  "Is this person an athlete?": "क्या यह व्यक्ति एक एथलीट है?",
  "Is this person alive today?": "क्या यह व्यक्ति आज जीवित है?",
  "Is this person known for technology or business?":
    "क्या यह व्यक्ति तकनीक या व्यवसाय के लिए जाना जाता है?",
  "Is the person a real person?": "क्या वह व्यक्ति एक वास्तविक व्यक्ति है?",
  "Is this person a real person?": "क्या यह व्यक्ति एक वास्तविक व्यक्ति है?",
  "Is this a real person?": "क्या यह एक वास्तविक व्यक्ति है?",
  "Is this person male?": "क्या यह व्यक्ति पुरुष है?",
  "Is this person female?": "क्या यह व्यक्ति महिला है?",
  "Is this person fictional?": "क्या यह व्यक्ति काल्पनिक है?",
  "Is this person from India?": "क्या यह व्यक्ति भारत से है?",
  "Is this person an actor?": "क्या यह व्यक्ति एक अभिनेता/अभिनेत्री है?",
  "Is this person a singer?": "क्या यह व्यक्ति एक गायक/गायिका है?",
  "Is this person a politician?": "क्या यह व्यक्ति एक राजनीतिज्ञ है?",
  "Is this person famous?": "क्या यह व्यक्ति प्रसिद्ध है?",
};

const LANG_KEY = "mindguess-lang";
const LEADERBOARD_KEY = "mindguess-leaderboard";

export function getStoredLang() {
  try {
    const v = localStorage.getItem(LANG_KEY);
    return v === "hi" ? "hi" : "en";
  } catch {
    return "en";
  }
}

export function storeLang(lang) {
  try {
    localStorage.setItem(LANG_KEY, lang === "hi" ? "hi" : "en");
  } catch {
    /* ignore */
  }
}

export function t(lang, key, ...args) {
  const pack = UI[lang] || UI.en;
  const val = pack[key] ?? UI.en[key] ?? key;
  return typeof val === "function" ? val(...args) : val;
}

export function translateQuestionText(englishText, lang) {
  if (!englishText || lang !== "hi") return englishText || "";
  const direct = QUESTION_HI[englishText];
  if (direct) return direct;
  const normalized = englishText.trim().replace(/\s+/g, " ");
  return QUESTION_HI[normalized] || englishText;
}

export function answerLabels(lang) {
  return [
    { value: "yes", label: t(lang, "yes") },
    { value: "probably_yes", label: t(lang, "probably") },
    { value: "dont_know", label: t(lang, "dontKnow") },
    { value: "probably_no", label: t(lang, "probablyNot") },
    { value: "no", label: t(lang, "no") },
  ];
}

export function loadLeaderboard() {
  try {
    const raw = localStorage.getItem(LEADERBOARD_KEY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}

export function saveLeaderboardEntry(entry) {
  const list = loadLeaderboard();
  list.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: entry.name || "Player",
    result: entry.result || "finished",
    questions: entry.questions ?? 0,
    at: new Date().toISOString(),
  });
  list.sort((a, b) => a.questions - b.questions || b.at.localeCompare(a.at));
  const top = list.slice(0, 20);
  try {
    localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(top));
  } catch {
    /* ignore */
  }
  return top;
}
