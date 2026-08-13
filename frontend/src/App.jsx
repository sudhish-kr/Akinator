import { useCallback, useState } from "react";
import { api } from "./api.js";
import { nextConfidence } from "./confidence.js";
import { canGoBack, popHistory, pushHistory } from "./gameHistory.js";
import { LanguageSwitch, useI18n } from "./i18n/index.jsx";
import HomePage from "./pages/HomePage.jsx";
import GamePage from "./pages/GamePage.jsx";
import GuessPage from "./pages/GuessPage.jsx";
import LearnPage from "./pages/LearnPage.jsx";

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
  /** Snapshots taken before each successful answer — used by Back (no API). */
  const [history, setHistory] = useState([]);
  /** When set, UI is rewound; server pending is this tip (session-safe). */
  const [liveTip, setLiveTip] = useState(null);
  const [endConfirmOpen, setEndConfirmOpen] = useState(false);

  const fail = (err) => {
    setError(err?.message || t("common.error"));
    setBusy(false);
  };

  const clearGameLocal = () => {
    setSessionId(null);
    setQuestion(null);
    setGuess(null);
    setConfidence(0);
    setQuestionNumber(1);
    setDoneMessage("");
    setCharacters([]);
    setHistory([]);
    setLiveTip(null);
    setEndConfirmOpen(false);
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
    setHistory([]);
    setLiveTip(null);
    setEndConfirmOpen(false);
    setScreen("game");
  };

  const showGuess = async (sid) => {
    const g = await api.getGuess(sid);
    setGuess(g);
    setConfidence(nextConfidence(0, g.confidence));
    setHistory([]);
    setLiveTip(null);
    setScreen("guess");
  };

  const startGame = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api.startGame();
      enterGame(data, data.session_id);
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [t]);

  const onBack = useCallback(() => {
    if (busy || !canGoBack(history)) return;
    const popped = popHistory(history);
    if (!popped) return;
    // Preserve server pending tip the first time we rewind.
    setLiveTip((tip) => tip || { question, questionNumber, confidence });
    setHistory(popped.history);
    setQuestion(popped.snapshot.question);
    setQuestionNumber(popped.snapshot.questionNumber);
    setConfidence(popped.snapshot.confidence);
    setError(null);
    setScreen("game");
  }, [busy, history, question, questionNumber, confidence]);

  const returnToCurrent = useCallback(() => {
    if (!liveTip || busy) return;
    setQuestion(liveTip.question);
    setQuestionNumber(liveTip.questionNumber);
    setConfidence(liveTip.confidence);
    setLiveTip(null);
    setError(null);
  }, [liveTip, busy]);

  const answer = useCallback(
    async (value) => {
      if (!sessionId || !question || busy) return;
      // Session-safe: while viewing a previous question, jump to live tip first.
      if (liveTip) {
        returnToCurrent();
        return;
      }
      setBusy(true);
      setError(null);
      const snapshot = {
        question,
        questionNumber,
        confidence,
      };
      try {
        const data = await api.submitAnswer(sessionId, question.id, value);
        setHistory((prev) => pushHistory(prev, snapshot));
        setConfidence((prev) => nextConfidence(prev, data.top_confidence));
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
            setLiveTip(null);
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
    [sessionId, question, questionNumber, confidence, busy, liveTip, returnToCurrent, t]
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
        const data = await api.listCharacters({ category, pageSize: 40 });
        setCharacters((data.items || []).filter((c) => c.id !== guess?.character?.id));
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [guess, t]
  );

  const searchLearnCharacters = useCallback(
    async (q, category) => {
      setBusy(true);
      setError(null);
      try {
        const data = await api.listCharacters({ category, q, pageSize: 40 });
        setCharacters((data.items || []).filter((c) => c.id !== guess?.character?.id));
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [guess, t]
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

  return (
    <div className="shell">
      <div className="atmosphere" aria-hidden="true" />
      <LanguageSwitch className="lang-switch-floating" />

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
          question={question}
          questionNumber={questionNumber}
          confidence={confidence}
          busy={busy}
          canBack={canGoBack(history)}
          viewingPrevious={Boolean(liveTip)}
          onBack={onBack}
          onReturnCurrent={returnToCurrent}
          onEndGame={() => setEndConfirmOpen(true)}
          onAnswer={answer}
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
        <div className="modal-backdrop" role="presentation">
          <div
            className="modal-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="end-game-title"
          >
            <h3 id="end-game-title" className="modal-title">
              {t("game.endConfirmTitle")}
            </h3>
            <div className="modal-actions">
              <button
                type="button"
                className="btn primary"
                onClick={() => setEndConfirmOpen(false)}
              >
                {t("game.endConfirmContinue")}
              </button>
              <button type="button" className="btn ghost" onClick={endGameConfirmed}>
                {t("game.endConfirmEnd")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
