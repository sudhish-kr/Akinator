import { useCallback, useState } from "react";
import { api } from "./api.js";
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

  const fail = (err) => {
    setError(err?.message || t("common.error"));
    setBusy(false);
  };

  const goHome = () => {
    setScreen("home");
    setSessionId(null);
    setQuestion(null);
    setGuess(null);
    setConfidence(0);
    setQuestionNumber(1);
    setDoneMessage("");
    setError(null);
    setCharacters([]);
  };

  const enterGame = (data, session) => {
    setSessionId(session);
    setQuestion(data.question || data.next_question);
    setQuestionNumber((data.questions_asked ?? 0) + 1);
    setConfidence(data.top_confidence ?? 0);
    setGuess(null);
    setScreen("game");
  };

  const showGuess = async (sid) => {
    const g = await api.getGuess(sid);
    setGuess(g);
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

  const answer = useCallback(
    async (value) => {
      if (!sessionId || !question || busy) return;
      setBusy(true);
      setError(null);
      try {
        const data = await api.submitAnswer(sessionId, question.id, value);
        setConfidence(data.top_confidence ?? 0);
        if (data.status === "ready_to_guess") {
          await showGuess(sessionId);
        } else {
          setQuestion(data.next_question);
          setQuestionNumber(data.questions_asked + 1);
        }
      } catch {
        try {
          const state = await api.getState(sessionId);
          setConfidence(state.top_confidence ?? 0);
          setQuestionNumber(state.questions_asked + 1);
          if (state.status === "ready_to_guess") {
            await showGuess(sessionId);
          } else if (state.next_question) {
            setQuestion(state.next_question);
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
    [sessionId, question, busy, t]
  );

  const onCorrect = useCallback(async () => {
    if (!sessionId || !guess || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api.learn(sessionId, guess.character.id, { wrongGuess: false });
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
    </div>
  );
}
