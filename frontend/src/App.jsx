import { useCallback, useEffect, useRef, useState } from "react";
import Scene from "./Scene.jsx";
import { api } from "./api.js";

const ANSWERS = [
  { value: "yes", label: "Yes" },
  { value: "probably_yes", label: "Probably" },
  { value: "dont_know", label: "Don't know" },
  { value: "probably_no", label: "Probably not" },
  { value: "no", label: "No" },
];

// screen: intro | asking | guess | reveal | result
export default function App() {
  const [screen, setScreen] = useState("intro");
  const [mood, setMood] = useState("idle"); // idle | thinking | celebrate
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [confidence, setConfidence] = useState(0);
  const [guess, setGuess] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cardVisible, setCardVisible] = useState(true);
  const thinkTimer = useRef(null);

  useEffect(() => () => clearTimeout(thinkTimer.current), []);

  const fail = (err) => {
    setError(err.message || "Something went wrong");
    setBusy(false);
    setMood("idle");
  };

  const showToast = (message, ms = 4000) => {
    setError(message);
    setTimeout(() => setError(null), ms);
  };

  const applyNewGame = (data) => {
    setSession(data.session_id);
    setQuestion(data.question);
    setQuestionNumber(1);
    setConfidence(0);
    setGuess(null);
    setResult(null);
    setMood("idle");
    setScreen("asking");
    setCardVisible(true);
  };

  // Re-align the UI with the engine's actual state (e.g. after a stale request).
  // If the session is gone (server restarted), start a fresh game automatically.
  const resync = useCallback(async (sessionId) => {
    try {
      const state = await api.getState(sessionId);
      setConfidence(state.top_confidence ?? 0);
      setQuestionNumber(state.questions_asked + 1);
      if (state.status === "ready_to_guess") {
        const g = await api.makeGuess(sessionId);
        setGuess(g);
        setMood("idle");
        setScreen("guess");
      } else if (state.next_question) {
        setQuestion(state.next_question);
        setMood("idle");
        setCardVisible(true);
        setScreen("asking");
      }
      setError(null);
      return true;
    } catch {
      // Session lost — recover by starting a brand new game
      try {
        const data = await api.startGame();
        applyNewGame(data);
        showToast("Session was lost — started a fresh game");
        return true;
      } catch {
        setError("Cannot reach the mind engine — is the backend running?");
        setScreen("intro");
        setMood("idle");
        return false;
      }
    }
  }, []);

  const startGame = useCallback(async () => {
    setError(null);
    setBusy(true);
    setMood("thinking");
    try {
      const data = await api.startGame();
      applyNewGame(data);
    } catch (err) {
      fail(err);
      setScreen("intro");
    } finally {
      setBusy(false);
    }
  }, []);

  const answer = useCallback(
    async (value) => {
      if (busy || !session || !question) return;
      setBusy(true);
      setError(null);
      setCardVisible(false);
      setMood("thinking");
      try {
        const data = await api.submitAnswer(session, question.id, value);
        setConfidence(data.top_confidence ?? 0);

        // Let the orb "think" briefly so the animation reads
        thinkTimer.current = setTimeout(async () => {
          if (data.status === "ready_to_guess") {
            try {
              const g = await api.makeGuess(session);
              setGuess(g);
              setMood("idle");
              setScreen("guess");
            } catch {
              await resync(session);
            }
          } else {
            setQuestion(data.next_question);
            setQuestionNumber(data.questions_asked + 1);
            setMood("idle");
            setCardVisible(true);
          }
          setBusy(false);
        }, 900);
      } catch (err) {
        // Out of sync with the engine — resync instead of dead-ending
        await resync(session);
        setBusy(false);
        setCardVisible(true);
      }
    },
    [busy, session, question, resync]
  );

  const confirmCorrect = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      await api.confirmGuess(session, true);
      setMood("celebrate");
      setResult({
        title: "I read your mind.",
        sub: `It was ${guess.character.name} — and I knew it with ${(guess.confidence * 100).toFixed(0)}% certainty.`,
      });
      setScreen("result");
    } catch {
      await resync(session);
    } finally {
      setBusy(false);
    }
  }, [busy, session, guess, resync]);

  const openReveal = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const data = await api.listCharacters();
      setCharacters(data.items.filter((c) => c.id !== guess?.character?.id));
      setScreen("reveal");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [busy, guess]);

  const pickActual = useCallback(
    async (characterId) => {
      if (busy) return;
      setBusy(true);
      setMood("thinking");
      try {
        const data = await api.confirmGuess(session, false, characterId);
        if (data.status === "resumed" && data.next_question) {
          // Engine removed its wrong guess and keeps asking
          setQuestion(data.next_question);
          setQuestionNumber((n) => n + 1);
          setMood("idle");
          setCardVisible(true);
          setScreen("asking");
        } else if (data.status === "ready_to_guess") {
          const g = await api.makeGuess(session);
          setGuess(g);
          setMood("idle");
          setScreen("guess");
        } else {
          setMood("idle");
          setResult({
            title: "Well played!",
            sub: "You beat me this time — but I just learned from it. Try me again.",
          });
          setScreen("result");
        }
      } catch {
        await resync(session);
      } finally {
        setBusy(false);
      }
    },
    [busy, session, resync]
  );

  const humanWins = useCallback(() => {
    setMood("idle");
    setResult({
      title: "You win this round.",
      sub: "Your mind stayed hidden... this time. Play again and give me another chance.",
    });
    setScreen("result");
  }, []);

  return (
    <div className="app">
      <Scene confidence={confidence} mood={mood} />

      {error && <div className="toast-error">{error}</div>}

      {screen === "intro" && (
        <div className="overlay">
          <h1 className="title">
            MIND<span>GUESS</span>
          </h1>
          <p className="subtitle">Think of a character. I will read your mind.</p>
          <button className="btn-primary" onClick={startGame} disabled={busy}>
            {busy ? "Connecting..." : "Enter the Mind"}
          </button>
        </div>
      )}

      {screen === "asking" && question && (
        <div className="overlay game">
          <div className="hud">
            <div className="hud-item">
              <span className="hud-label">Question</span>
              <span className="hud-value">{questionNumber}</span>
            </div>
            <div className="hud-item confidence-wrap">
              <span className="hud-label">Mind link</span>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${Math.round(confidence * 100)}%` }} />
              </div>
            </div>
          </div>

          <div className={`question-card ${cardVisible ? "visible" : ""}`}>
            <p>{question.text}</p>
          </div>

          <div className="answers">
            {ANSWERS.map((a) => (
              <button key={a.value} className="btn-answer" disabled={busy} onClick={() => answer(a.value)}>
                {a.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {screen === "guess" && guess && (
        <div className="overlay">
          <p className="guess-intro">I see it clearly now...</p>
          <div className="guess-card">
            <div className="guess-avatar">{guess.character.name.charAt(0)}</div>
            <h2>{guess.character.name}</h2>
            <p className="guess-conf">{(guess.confidence * 100).toFixed(0)}% certain</p>
          </div>
          <p className="guess-question">Am I right?</p>
          <div className="guess-buttons">
            <button className="btn-primary" onClick={confirmCorrect} disabled={busy}>
              Yes, that's it!
            </button>
            <button className="btn-secondary" onClick={openReveal} disabled={busy}>
              No, wrong
            </button>
          </div>
        </div>
      )}

      {screen === "reveal" && (
        <div className="overlay">
          <p className="guess-intro">Who were you thinking of?</p>
          <div className="character-list">
            {characters.map((c) => (
              <button key={c.id} className="character-chip" disabled={busy} onClick={() => pickActual(c.id)}>
                {c.name}
              </button>
            ))}
          </div>
          <button className="btn-secondary" onClick={humanWins} disabled={busy}>
            They're not in your world yet
          </button>
        </div>
      )}

      {screen === "result" && result && (
        <div className="overlay">
          <h2 className="result-title">{result.title}</h2>
          <p className="result-sub">{result.sub}</p>
          <button className="btn-primary" onClick={startGame} disabled={busy}>
            Play Again
          </button>
        </div>
      )}
    </div>
  );
}
