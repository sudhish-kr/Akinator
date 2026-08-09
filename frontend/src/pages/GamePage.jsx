import { useEffect, useRef, useState } from "react";
import { formatConfidencePercent } from "../confidence.js";
import { useI18n } from "../i18n/index.jsx";
import {
  createRecognizer,
  parseSpeechAnswer,
  speakText,
  speechRecognitionSupported,
  stopSpeaking,
  ttsSupported,
} from "../voice/speech.js";

const VOICE_PREF_KEY = "mg_voice_mode";

function readVoicePref() {
  try {
    return localStorage.getItem(VOICE_PREF_KEY) === "1";
  } catch {
    return false;
  }
}

export default function GamePage({ question, questionNumber, confidence, busy, onAnswer }) {
  const { t, tq, lang } = useI18n();
  const [voiceOn, setVoiceOn] = useState(readVoicePref);
  const [listening, setListening] = useState(false);
  const [voiceNote, setVoiceNote] = useState(null);
  const recognitionRef = useRef(null);
  const canListen = speechRecognitionSupported();
  const canSpeak = ttsSupported();
  const voiceAvailable = canListen || canSpeak;

  const answers = [
    { value: "yes", label: t("game.yes") },
    { value: "probably_yes", label: t("game.probablyYes") },
    { value: "dont_know", label: t("game.dontKnow") },
    { value: "probably_no", label: t("game.probablyNo") },
    { value: "no", label: t("game.no") },
  ];

  const spokenQuestion = question ? tq(question.text) : "";

  useEffect(() => {
    return () => {
      stopSpeaking();
      try {
        recognitionRef.current?.stop();
      } catch {
        /* ignore */
      }
    };
  }, []);

  useEffect(() => {
    if (!voiceOn || !question || busy || !canSpeak) return;
    let cancelled = false;
    (async () => {
      setVoiceNote(null);
      await speakText(spokenQuestion, { lang });
      if (cancelled) return;
    })();
    return () => {
      cancelled = true;
      stopSpeaking();
    };
  }, [question?.id, spokenQuestion, voiceOn, lang, busy, canSpeak]);

  const toggleVoice = () => {
    const next = !voiceOn;
    setVoiceOn(next);
    setVoiceNote(null);
    try {
      localStorage.setItem(VOICE_PREF_KEY, next ? "1" : "0");
    } catch {
      /* ignore */
    }
    if (!next) {
      stopSpeaking();
      try {
        recognitionRef.current?.stop();
      } catch {
        /* ignore */
      }
      setListening(false);
    } else if (!voiceAvailable) {
      setVoiceNote(t("game.voiceUnsupported"));
    }
  };

  const speakAgain = () => {
    if (!spokenQuestion || busy) return;
    setVoiceNote(null);
    speakText(spokenQuestion, { lang });
  };

  const startListening = () => {
    if (!canListen || busy || listening) return;
    stopSpeaking();
    setVoiceNote(null);

    const recognition = createRecognizer({
      lang,
      onResult: (transcripts) => {
        let matched = null;
        for (const text of transcripts) {
          matched = parseSpeechAnswer(text, lang);
          if (matched) break;
        }
        if (matched) {
          setVoiceNote(null);
          onAnswer(matched);
        } else {
          setVoiceNote(t("game.voiceUnrecognized"));
        }
      },
      onError: () => {
        setVoiceNote(t("game.voiceUnrecognized"));
        setListening(false);
      },
      onEnd: () => setListening(false),
    });

    if (!recognition) {
      setVoiceNote(t("game.voiceUnsupported"));
      return;
    }

    recognitionRef.current = recognition;
    setListening(true);
    try {
      recognition.start();
    } catch {
      setListening(false);
      setVoiceNote(t("game.voiceUnsupported"));
    }
  };

  if (!question) return null;
  const pct = formatConfidencePercent(confidence);

  return (
    <section className="page game">
      <header className="game-hud">
        <div>
          <span className="hud-label">{t("game.question")}</span>
          <strong className="hud-value">{questionNumber}</strong>
        </div>
        <div className="hud-conf">
          <span className="hud-label">{t("game.confidence")}</span>
          <div className="bar" aria-hidden="true">
            <div className="bar-fill" style={{ width: `${pct}%` }} />
          </div>
          <strong className="hud-value">{pct}%</strong>
        </div>
      </header>

      <div className="voice-bar">
        <button
          type="button"
          className={`btn ghost voice-toggle ${voiceOn ? "on" : ""}`}
          onClick={toggleVoice}
          aria-pressed={voiceOn}
        >
          {voiceOn ? t("game.voiceOn") : t("game.voiceOff")}
        </button>
        {voiceOn && canSpeak && (
          <button type="button" className="btn ghost" disabled={busy} onClick={speakAgain}>
            {t("game.speak")}
          </button>
        )}
        {voiceOn && canListen && (
          <button
            type="button"
            className={`btn primary voice-mic ${listening ? "listening" : ""}`}
            disabled={busy || listening}
            onClick={startListening}
          >
            {listening ? t("game.listening") : t("game.listen")}
          </button>
        )}
      </div>

      {voiceOn && <p className="voice-hint">{t("game.voiceHint")}</p>}
      {voiceNote && <p className="voice-note">{voiceNote}</p>}

      <h2 className="question">{spokenQuestion}</h2>

      <div className="answers" role="group" aria-label={t("game.answersAria")}>
        {answers.map((a) => (
          <button
            key={a.value}
            type="button"
            className="btn answer"
            disabled={busy}
            onClick={() => onAnswer(a.value)}
          >
            {a.label}
          </button>
        ))}
      </div>
    </section>
  );
}
