import { useEffect, useRef, useState } from "react";
import { useI18n } from "../i18n/index.jsx";
import {
  createRecognizer,
  parseSpeechAnswer,
  speakText,
  speechRecognitionSupported,
  stopSpeaking,
  ttsSupported,
} from "../voice/speech.js";
import GameHeader from "../components/GameHeader.jsx";
import Mascot from "../components/Mascot.jsx";
import QuestionCard from "../components/QuestionCard.jsx";
import {
  CURIOUS_MS,
  GAZE,
  REACTION_MS,
  classifyQuestionCue,
  reactionAfterAnswer,
  reactionMessageKey,
  resolveBaseMood,
} from "../components/mascotMood.js";

const VOICE_PREF_KEY = "mg_voice_mode";

function readVoicePref() {
  try {
    return localStorage.getItem(VOICE_PREF_KEY) === "1";
  } catch {
    return false;
  }
}

export default function GamePage({
  question,
  questionNumber,
  confidence,
  busy,
  canBack = false,
  editingPrevious = false,
  selectedAnswer = null,
  navDirection = "forward",
  onBack,
  onEndGame,
  onAnswer,
  mascotState,
  introPlaying = false,
  introKey = 0,
  onIntroComplete,
}) {
  const { t, tq, lang } = useI18n();
  const [voiceOn, setVoiceOn] = useState(readVoicePref);
  const [listening, setListening] = useState(false);
  const [voiceNote, setVoiceNote] = useState(null);
  const recognitionRef = useRef(null);
  const reactionTimer = useRef(null);
  const curiousTimer = useRef(null);
  const introTimers = useRef([]);
  const prevQuestionId = useRef(null);
  const pendingAnswer = useRef(null);

  const [flashMood, setFlashMood] = useState(null);
  const [flashMessage, setFlashMessage] = useState(null);
  const [look, setLook] = useState(GAZE.center);
  const [cardReady, setCardReady] = useState(!introPlaying);

  const canListen = speechRecognitionSupported();
  const canSpeak = ttsSupported();
  const voiceAvailable = canListen || canSpeak;
  const locked = busy || introPlaying;

  const answers = [
    { value: "yes", label: t("game.yes") },
    { value: "probably_yes", label: t("game.probablyYes") },
    { value: "dont_know", label: t("game.dontKnow") },
    { value: "probably_no", label: t("game.probablyNo") },
    { value: "no", label: t("game.no") },
  ];

  const spokenQuestion = question ? tq(question.text) : "";
  const cue = classifyQuestionCue(question?.text || spokenQuestion);

  const baseMood = resolveBaseMood({
    busy,
    listening,
    confidence,
    override: mascotState || null,
  });
  const mood = flashMood || baseMood;
  const messageKey = flashMessage || undefined;

  const clearIntroTimers = () => {
    introTimers.current.forEach((id) => clearTimeout(id));
    introTimers.current = [];
  };

  useEffect(() => {
    return () => {
      stopSpeaking();
      clearTimeout(reactionTimer.current);
      clearTimeout(curiousTimer.current);
      clearIntroTimers();
      try {
        recognitionRef.current?.stop();
      } catch {
        /* ignore */
      }
    };
  }, []);

  // Start-game mascot entrance (replays every new game via introKey).
  useEffect(() => {
    if (!introPlaying) {
      setCardReady(true);
      return undefined;
    }

    clearIntroTimers();
    prevQuestionId.current = null;
    setCardReady(false);
    setLook(GAZE.center);

    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    setFlashMood(reduced ? "happy" : "excited");
    setFlashMessage(reduced ? "mascot.letsPlay" : "mascot.hereWeGo");

    const landMsgAt = reduced ? 140 : 700;
    const revealAt = reduced ? 240 : 980;
    const doneAt = reduced ? 340 : 1180;

    introTimers.current.push(
      setTimeout(() => {
        setFlashMood("happy");
        setFlashMessage("mascot.letsPlay");
      }, landMsgAt)
    );
    introTimers.current.push(
      setTimeout(() => {
        setCardReady(true);
      }, revealAt)
    );
    introTimers.current.push(
      setTimeout(() => {
        setFlashMood(null);
        setFlashMessage(null);
        onIntroComplete?.();
      }, doneAt)
    );

    return () => clearIntroTimers();
  }, [introPlaying, introKey, onIntroComplete]);

  // New question → curious glance toward the card, then settle.
  useEffect(() => {
    if (!question?.id || busy || introPlaying || !cardReady) return;
    if (prevQuestionId.current === question.id) return;
    const isFirst = prevQuestionId.current == null;
    prevQuestionId.current = question.id;

    const answered = pendingAnswer.current;
    pendingAnswer.current = null;

    clearTimeout(curiousTimer.current);
    clearTimeout(reactionTimer.current);

    if (answered) {
      const react = reactionAfterAnswer(answered);
      setFlashMood(react === "idle" ? null : react);
      setFlashMessage(reactionMessageKey(answered));
      setLook(GAZE.question);
      reactionTimer.current = setTimeout(() => {
        setFlashMood(null);
        setFlashMessage(null);
        setLook(GAZE.center);
      }, REACTION_MS);
      return;
    }

    setLook(GAZE.question);
    setFlashMood("curious");
    setFlashMessage(
      isFirst
        ? "mascot.idle"
        : cue === "country"
          ? "mascot.curiousCountry"
          : cue === "sports"
            ? "mascot.curiousSports"
            : cue === "identity"
              ? "mascot.curiousIdentity"
              : "mascot.curious"
    );
    curiousTimer.current = setTimeout(() => {
      setFlashMood(null);
      setFlashMessage(null);
      setLook(GAZE.center);
    }, CURIOUS_MS);
  }, [question?.id, busy, cue, introPlaying, cardReady]);

  useEffect(() => {
    if (introPlaying || !cardReady) return;
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
  }, [question?.id, spokenQuestion, voiceOn, lang, busy, canSpeak, introPlaying, cardReady]);

  const toggleVoice = () => {
    if (introPlaying) return;
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
    if (!spokenQuestion || locked) return;
    setVoiceNote(null);
    speakText(spokenQuestion, { lang });
  };

  const startListening = () => {
    if (!canListen || locked || listening) return;
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
          handleAnswer(matched);
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

  const handleAnswerHover = (value) => {
    if (locked || flashMood === "thinking") return;
    setLook(GAZE[value] || GAZE.center);
  };

  const handleAnswerLeave = () => {
    if (locked) return;
    setLook(GAZE.center);
  };

  const handleAnswer = (value) => {
    if (locked) return;
    pendingAnswer.current = value;
    clearTimeout(curiousTimer.current);
    clearTimeout(reactionTimer.current);
    setFlashMood("thinking");
    setFlashMessage(value === "dont_know" ? "mascot.thinkingSoft" : "mascot.thinking");
    setLook(GAZE.center);
    onAnswer(value);
  };

  if (!question) return null;

  return (
    <section className={`page game game-stage${introPlaying ? " is-intro" : ""}`}>
      <GameHeader
        t={t}
        canBack={canBack && !introPlaying}
        busy={locked}
        onBack={onBack}
        onEndGame={onEndGame}
        voiceOn={voiceOn}
        onToggleVoice={toggleVoice}
        voiceAvailable={voiceAvailable && !introPlaying}
      />

      <div className="game-layout">
        <aside className="game-mascot-col">
          <Mascot
            key={`intro-${introKey}`}
            state={mood}
            t={t}
            look={look}
            cue={cue}
            messageKey={messageKey}
            confidence={confidence}
            entering={introPlaying}
          />
        </aside>

        <div className="game-card-col">
          <QuestionCard
            t={t}
            questionNumber={questionNumber}
            confidence={confidence}
            questionText={spokenQuestion}
            questionKey={`${question.id}-${editingPrevious ? "edit" : "live"}-${questionNumber}`}
            busy={locked}
            editingPrevious={editingPrevious}
            navDirection={navDirection}
            selectedAnswer={selectedAnswer}
            answers={answers}
            onAnswer={handleAnswer}
            onAnswerHover={handleAnswerHover}
            onAnswerLeave={handleAnswerLeave}
            voiceOn={voiceOn && !introPlaying}
            canSpeak={canSpeak}
            canListen={canListen}
            listening={listening}
            voiceNote={voiceNote}
            onSpeakAgain={speakAgain}
            onStartListening={startListening}
            introWaiting={introPlaying && !cardReady}
            introReady={introPlaying && cardReady}
          />
        </div>
      </div>
    </section>
  );
}
