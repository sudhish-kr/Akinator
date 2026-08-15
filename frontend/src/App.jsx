import { useCallback, useState } from "react";
import { api } from "./api.js";
import { nextConfidence } from "./confidence.js";
import {
  answersForReplay,
  backEditIndex,
  canGoBack,
  pushTrail,
} from "./gameHistory.js";
import { LanguageSwitch, useI18n } from "./i18n/index.jsx";
import EndGameModal from "./components/EndGameModal.jsx";
import Mascot from "./components/Mascot.jsx";
import HomePage from "./pages/HomePage.jsx";
import GamePage from "./pages/GamePage.jsx";
import GuessPage from "./pages/GuessPage.jsx";
import LearnPage from "./pages/LearnPage.jsx";

/**
 * Restart a session and replay answers via existing start/answer APIs.
 * Used when the player edits a past answer (backend has no undo/revise).
 */
async function replayAnswerPath(answers) {
  const start = await api.startGame();
  let sid = start.session_id;
  let q = start.question || start.next_question;
  let conf = nextConfidence(0, start.top_confidence);
  let n = (start.questions_asked ?? 0) + 1;
  const trail = [];

  for (const ans of answers) {
    if (!q?.id) {
      throw new Error("Missing question during answer replay");
    }
    trail.push({
      question: q,
      questionNumber: n,
      confidence: conf,
      answer: ans,
    });
    const data = await api.submitAnswer(sid, q.id, ans);
    conf = nextConfidence(conf, data.top_confidence);
    if (data.status === "ready_to_guess") {
      return { sid, trail, ready: true, confidence: conf };
    }
    q = data.next_question;
    n = data.questions_asked + 1;
  }

  return {
    sid,
    trail,
    ready: false,
    question: q,
    questionNumber: n,
    confidence: conf,
  };
}

/** Screens: home | game | guess | learn | done */
export default function App() {
  const { t } = useI18n();
  const [screen, setScreen] = useState("home");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const [sessionId, setSessionId] = useState(null);
  const [question, setQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [confidence, setConfidence] = useState(0);
  const [guess, setGuess] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [doneMessage, setDoneMessage] = useState("");
  /** Answered steps for Back / edit (includes selected answer). */
  const [trail, setTrail] = useState([]);
  /** Index into trail while editing a past answer; null = live pending question. */
  const [editIndex, setEditIndex] = useState(null);
  /** Live pending tip saved when first going Back (session still valid if answers unchanged). */
  const [livePending, setLivePending] = useState(null);
  const [navDirection, setNavDirection] = useState("forward");
  const [endConfirmOpen, setEndConfirmOpen] = useState(false);
  /** True while start-game mascot entrance plays (every new game). */
  const [introPlaying, setIntroPlaying] = useState(false);
  const [introKey, setIntroKey] = useState(0);

  const fail = (err) => {
    setError(err?.message || t("common.error"));
    setBusy(false);
    setIntroPlaying(false);
  };

  const clearGameLocal = () => {
    setSessionId(null);
    setQuestion(null);
    setGuess(null);
    setConfidence(0);
    setQuestionNumber(1);
    setDoneMessage("");
    setCharacters([]);
    setTrail([]);
    setEditIndex(null);
    setLivePending(null);
    setNavDirection("forward");
    setEndConfirmOpen(false);
    setIntroPlaying(false);
  };

  const goHome = () => {
    setScreen("home");
    clearGameLocal();
    setError(null);
  };

  /** End game without learning / correct-guess — local clear only (no abandon API). */
  const endGameConfirmed = () => {
    setEndConfirmOpen(false);
    goHome();
  };

  const enterGame = (data, session) => {
    setSessionId(session);
    setQuestion(data.question || data.next_question);
    setQuestionNumber((data.questions_asked ?? 0) + 1);
    setConfidence(nextConfidence(0, data.top_confidence));
    setGuess(null);
    setTrail([]);
    setEditIndex(null);
    setLivePending(null);
    setNavDirection("forward");
    setEndConfirmOpen(false);
    setIntroKey((k) => k + 1);
    setIntroPlaying(true);
    setScreen("game");
  };

  const finishIntro = useCallback(() => {
    setIntroPlaying(false);
  }, []);

  const showGuess = async (sid) => {
    const g = await api.getGuess(sid);
    setGuess(g);
    setConfidence(nextConfidence(0, g.confidence));
    setTrail([]);
    setEditIndex(null);
    setLivePending(null);
    setIntroPlaying(false);
    setScreen("guess");
  };

  const startGame = useCallback(async () => {
    if (busy || introPlaying) return;
    setBusy(true);
    setError(null);
    try {
      const data = await api.startGame();
      enterGame(data, data.session_id);
    } catch (err) {
      fail(err);
      setScreen("home");
    } finally {
      setBusy(false);
    }
  }, [t, busy, introPlaying]);

  const onBack = useCallback(() => {
    if (busy || introPlaying || !canGoBack(trail, editIndex)) return;
    const nextIndex = backEditIndex(trail, editIndex);
    if (nextIndex == null) return;
    if (editIndex == null) {
      setLivePending({ question, questionNumber, confidence });
    }
    setEditIndex(nextIndex);
    setNavDirection("back");
    setError(null);
    setScreen("game");
  }, [busy, introPlaying, trail, editIndex, question, questionNumber, confidence]);

  const restoreLivePending = useCallback(() => {
    if (!livePending) return;
    setQuestion(livePending.question);
    setQuestionNumber(livePending.questionNumber);
    setConfidence(livePending.confidence);
    setEditIndex(null);
    setLivePending(null);
    setNavDirection("forward");
    setError(null);
  }, [livePending]);

  const answer = useCallback(
    async (value) => {
      if (busy || introPlaying) return;

      // Editing a previous answer — no duplicate submit of the live pending question.
      if (editIndex != null) {
        const step = trail[editIndex];
        if (!step) return;

        // Unchanged answer: walk forward through trail, or restore live pending.
        if (value === step.answer) {
          if (editIndex < trail.length - 1) {
            setEditIndex(editIndex + 1);
            setNavDirection("forward");
            return;
          }
          if (livePending) {
            restoreLivePending();
            return;
          }
          return;
        }

        // Changed answer: restart session and replay prefix + new answer.
        setBusy(true);
        setError(null);
        try {
          const answers = answersForReplay(trail, editIndex, value);
          const result = await replayAnswerPath(answers);
          setSessionId(result.sid);
          setTrail(result.trail);
          setEditIndex(null);
          setLivePending(null);
          setNavDirection("forward");
          setIntroPlaying(false);
          if (result.ready) {
            await showGuess(result.sid);
          } else {
            setQuestion(result.question);
            setQuestionNumber(result.questionNumber);
            setConfidence(result.confidence);
            setScreen("game");
          }
        } catch (err) {
          fail(err);
        } finally {
          setBusy(false);
        }
        return;
      }

      if (!sessionId || !question) return;
      setBusy(true);
      setError(null);
      try {
        const data = await api.submitAnswer(sessionId, question.id, value);
        setTrail((prev) =>
          pushTrail(prev, {
            question,
            questionNumber,
            confidence,
            answer: value,
          })
        );
        setConfidence((prev) => nextConfidence(prev, data.top_confidence));
        setNavDirection("forward");
        if (data.status === "ready_to_guess") {
          await showGuess(sessionId);
        } else {
          setQuestion(data.next_question);
          setQuestionNumber(data.questions_asked + 1);
        }
      } catch {
        try {
          const state = await api.getState(sessionId);
          setConfidence((prev) => nextConfidence(prev, state.top_confidence));
          setQuestionNumber(state.questions_asked + 1);
          if (state.status === "ready_to_guess") {
            await showGuess(sessionId);
          } else if (state.next_question) {
            setQuestion(state.next_question);
            setEditIndex(null);
            setLivePending(null);
            setScreen("game");
          }
          setError(null);
        } catch (err) {
          fail(err);
        }
      } finally {
        setBusy(false);
      }
    },
    [
      sessionId,
      question,
      questionNumber,
      confidence,
      busy,
      introPlaying,
      editIndex,
      trail,
      livePending,
      restoreLivePending,
      t,
    ]
  );

  const onCorrect = useCallback(async () => {
    if (!sessionId || !guess || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api.confirmGuess(sessionId, { correct: true });
      setDoneMessage(t("done.nailed", { name: guess.character.name }));
      setScreen("done");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [sessionId, guess, busy, t]);

  const openLearn = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      setCharacters([]);
      setScreen("learn");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [busy, t]);

  const loadLearnSuggestions = useCallback(
    async (category) => {
      setBusy(true);
      setError(null);
      try {
        const excludeId = guess?.character?.id;
        if (sessionId) {
          const remaining = await api.listRemainingCandidates(sessionId, {
            category,
            pageSize: 40,
          });
          const items = (remaining.items || []).filter((c) => c.id !== excludeId);
          if (items.length > 0) {
            setCharacters(items);
            return;
          }
        }
        const data = await api.listCharacters({ category, pageSize: 40 });
        setCharacters((data.items || []).filter((c) => c.id !== excludeId));
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [guess, sessionId, t]
  );

  const searchLearnCharacters = useCallback(
    async (q, category) => {
      setBusy(true);
      setError(null);
      try {
        const excludeId = guess?.character?.id;
        if (sessionId) {
          const remaining = await api.listRemainingCandidates(sessionId, {
            category,
            q,
            pageSize: 40,
          });
          const items = (remaining.items || []).filter((c) => c.id !== excludeId);
          if (items.length > 0) {
            setCharacters(items);
            return;
          }
        }
        const data = await api.listCharacters({ category, q, pageSize: 40 });
        setCharacters((data.items || []).filter((c) => c.id !== excludeId));
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [guess, sessionId, t]
  );

  const onLearnPick = useCallback(
    async (characterId, characterName) => {
      if (!sessionId || busy) return;
      setBusy(true);
      setError(null);
      try {
        await api.learn(sessionId, characterId, { wrongGuess: true });
        setDoneMessage(
          characterName
            ? t("done.learnedNamed", { name: characterName })
            : t("done.learned")
        );
        setScreen("done");
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [sessionId, busy, t]
  );

  const showFloatingLang = screen !== "game";

  return (
    <div className={`shell shell-${screen}`}>
      <div className="atmosphere" aria-hidden="true">
        <span className="particle p1" />
        <span className="particle p2" />
        <span className="particle p3" />
        <span className="particle p4" />
      </div>
      {showFloatingLang && <LanguageSwitch className="lang-switch-floating" />}

      {error && (
        <div className="toast" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="toast-x"
            onClick={() => setError(null)}
            aria-label={t("common.dismiss")}
          >
            ×
          </button>
        </div>
      )}

      {screen === "home" && <HomePage onStart={startGame} busy={busy} />}
      {screen === "game" && (
        <GamePage
          question={
            editIndex != null ? trail[editIndex]?.question : question
          }
          questionNumber={
            editIndex != null ? trail[editIndex]?.questionNumber : questionNumber
          }
          confidence={
            editIndex != null ? trail[editIndex]?.confidence : confidence
          }
          selectedAnswer={editIndex != null ? trail[editIndex]?.answer : null}
          editingPrevious={editIndex != null}
          navDirection={navDirection}
          busy={busy}
          canBack={canGoBack(trail, editIndex)}
          onBack={onBack}
          onEndGame={() => setEndConfirmOpen(true)}
          onAnswer={answer}
          introPlaying={introPlaying}
          introKey={introKey}
          onIntroComplete={finishIntro}
        />
      )}
      {screen === "guess" && (
        <GuessPage guess={guess} busy={busy} onCorrect={onCorrect} onWrong={openLearn} />
      )}
      {screen === "learn" && (
        <LearnPage
          wrongGuessName={guess?.character?.name}
          characters={characters}
          busy={busy}
          onPick={onLearnPick}
          onHome={goHome}
          onLoadSuggestions={loadLearnSuggestions}
          onSearch={searchLearnCharacters}
        />
      )}
      {screen === "done" && (
        <section className="page done">
          <div className="done-mascot-wrap is-celebrate">
            <Mascot state="happy" t={t} compact messageKey="mascot.correct" />
          </div>
          <h2 className="title">{doneMessage || t("done.title")}</h2>
          <div className="actions">
            <button type="button" className="btn primary" onClick={startGame} disabled={busy}>
              {t("done.playAgain")}
            </button>
            <button type="button" className="btn ghost" onClick={goHome} disabled={busy}>
              {t("done.home")}
            </button>
          </div>
        </section>
      )}

      {endConfirmOpen && (
        <EndGameModal
          t={t}
          onContinue={() => setEndConfirmOpen(false)}
          onEnd={endGameConfirmed}
        />
      )}
    </div>
  );
}
