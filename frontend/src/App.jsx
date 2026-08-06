import { useCallback, useState } from "react";
import { api } from "./api.js";
import StartPage from "./pages/StartPage.jsx";
import QuestionPage from "./pages/QuestionPage.jsx";
import GuessPage from "./pages/GuessPage.jsx";
import LearnPage from "./pages/LearnPage.jsx";

/** Screens: start | question | guess | learn | done */
export default function App() {
  const [screen, setScreen] = useState("start");
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
    setError(err?.message || "Something went wrong");
    setBusy(false);
  };

  const resetToStart = () => {
    setScreen("start");
    setSessionId(null);
    setQuestion(null);
    setGuess(null);
    setConfidence(0);
    setQuestionNumber(1);
    setDoneMessage("");
    setError(null);
  };

  const enterQuestion = (data, session) => {
    setSessionId(session);
    setQuestion(data.question || data.next_question);
    setQuestionNumber((data.questions_asked ?? 0) + 1);
    setConfidence(data.top_confidence ?? 0);
    setScreen("question");
  };

  const fetchGuess = async (sid) => {
    const g = await api.getGuess(sid);
    setGuess(g);
    setScreen("guess");
  };

  const startGame = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await api.startGame();
      enterQuestion(data, data.session_id);
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, []);

  const answer = useCallback(
    async (value) => {
      if (!sessionId || !question || busy) return;
      setBusy(true);
      setError(null);
      try {
        const data = await api.submitAnswer(sessionId, question.id, value);
        setConfidence(data.top_confidence ?? 0);
        if (data.status === "ready_to_guess") {
          await fetchGuess(sessionId);
        } else {
          setQuestion(data.next_question);
          setQuestionNumber(data.questions_asked + 1);
        }
      } catch (err) {
        try {
          const state = await api.getState(sessionId);
          setConfidence(state.top_confidence ?? 0);
          if (state.status === "ready_to_guess") {
            await fetchGuess(sessionId);
          } else if (state.next_question) {
            setQuestion(state.next_question);
            setQuestionNumber(state.questions_asked + 1);
            setScreen("question");
          }
          setError(null);
        } catch {
          fail(err);
        }
      } finally {
        setBusy(false);
      }
    },
    [sessionId, question, busy]
  );

  const onCorrect = useCallback(async () => {
    if (!sessionId || !guess || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api.confirmGuess(sessionId, true);
      setDoneMessage(`Correct — it was ${guess.character.name}.`);
      setScreen("done");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [sessionId, guess, busy]);

  const openLearn = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const data = await api.listCharacters();
      const items = (data.items || []).filter((c) => c.id !== guess?.character?.id);
      setCharacters(items);
      setScreen("learn");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [busy, guess]);

  const onLearnPick = useCallback(
    async (characterId) => {
      if (!sessionId || busy) return;
      setBusy(true);
      setError(null);
      try {
        await api.learn(sessionId, characterId, { wrongGuess: true });
        setDoneMessage("Thanks — I learned from that round.");
        setScreen("done");
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [sessionId, busy]
  );

  return (
    <div className="app-shell">
      {error && (
        <div className="toast" role="alert">
          {error}
          <button type="button" className="toast-close" onClick={() => setError(null)}>
            ×
          </button>
        </div>
      )}

      {screen === "start" && <StartPage onStart={startGame} busy={busy} />}

      {screen === "question" && (
        <QuestionPage
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
          onSkip={resetToStart}
        />
      )}

      {screen === "done" && (
        <section className="page page-done">
          <h2>{doneMessage || "Round over"}</h2>
          <button type="button" className="btn primary" onClick={startGame} disabled={busy}>
            Play again
          </button>
        </section>
      )}
    </div>
  );
}
