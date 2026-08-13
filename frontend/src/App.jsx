import { useCallback, useState } from "react";
import { api } from "./api.js";
import {
  getStoredLang,
  loadLeaderboard,
  saveLeaderboardEntry,
  storeLang,
  t,
} from "./i18n.js";
import HomePage from "./pages/HomePage.jsx";
import GamePage from "./pages/GamePage.jsx";
import GuessPage from "./pages/GuessPage.jsx";
import LearnPage from "./pages/LearnPage.jsx";
import LeaderboardPage from "./pages/LeaderboardPage.jsx";

/** Screens: home | game | guess | learn | done | leaderboard */
export default function App() {
  const [screen, setScreen] = useState("home");
  const [returnScreen, setReturnScreen] = useState("home");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [lang, setLang] = useState(getStoredLang);
  const [showEndConfirm, setShowEndConfirm] = useState(false);

  const [sessionId, setSessionId] = useState(null);
  const [trail, setTrail] = useState([]);
  const [cursor, setCursor] = useState(0);
  const [guess, setGuess] = useState(null);
  const [characters, setCharacters] = useState([]);
  const [doneMessage, setDoneMessage] = useState("");
  const [leaderboard, setLeaderboard] = useState(loadLeaderboard);

  const fail = (err) => {
    setError(err?.message || t(lang, "somethingWrong"));
    setBusy(false);
  };

  const changeLang = (next) => {
    const value = next === "hi" ? "hi" : "en";
    setLang(value);
    storeLang(value);
  };

  const resetGameState = () => {
    setSessionId(null);
    setTrail([]);
    setCursor(0);
    setGuess(null);
    setDoneMessage("");
    setCharacters([]);
    setShowEndConfirm(false);
  };

  const goHome = () => {
    setScreen("home");
    resetGameState();
    setError(null);
  };

  const openLeaderboard = () => {
    setLeaderboard(loadLeaderboard());
    setReturnScreen(screen === "leaderboard" ? "home" : screen);
    setScreen("leaderboard");
  };

  const closeLeaderboard = () => {
    setScreen(returnScreen === "leaderboard" ? "home" : returnScreen);
  };

  const enterGame = (data, session) => {
    const q = data.question || data.next_question;
    const step = {
      question: q,
      answer: null,
      questionNumber: (data.questions_asked ?? 0) + 1,
      confidence: data.top_confidence ?? 0,
    };
    setSessionId(session);
    setTrail([step]);
    setCursor(0);
    setGuess(null);
    setShowEndConfirm(false);
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
  }, [lang]);

  const answer = useCallback(
    async (value) => {
      if (!sessionId || busy) return;
      const tip = trail[trail.length - 1];
      if (!tip?.question || cursor !== trail.length - 1 || tip.answer) return;

      setBusy(true);
      setError(null);
      try {
        const data = await api.submitAnswer(sessionId, tip.question.id, value);
        const confidence = data.top_confidence ?? 0;

        setTrail((prev) => {
          const next = prev.map((step, i) =>
            i === prev.length - 1 ? { ...step, answer: value, confidence } : step
          );
          if (data.status === "ready_to_guess") {
            return next;
          }
          return [
            ...next,
            {
              question: data.next_question,
              answer: null,
              questionNumber: data.questions_asked + 1,
              confidence,
            },
          ];
        });

        if (data.status === "ready_to_guess") {
          await showGuess(sessionId);
        } else {
          setCursor((c) => c + 1);
        }
      } catch {
        try {
          const state = await api.getState(sessionId);
          const confidence = state.top_confidence ?? 0;
          if (state.status === "ready_to_guess") {
            await showGuess(sessionId);
          } else if (state.next_question) {
            setTrail((prev) => {
              const next = prev.map((step, i) =>
                i === prev.length - 1
                  ? { ...step, answer: value, confidence }
                  : step
              );
              return [
                ...next,
                {
                  question: state.next_question,
                  answer: null,
                  questionNumber: state.questions_asked + 1,
                  confidence,
                },
              ];
            });
            setCursor((c) => c + 1);
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
    [sessionId, trail, cursor, busy, lang]
  );

  const onPrevious = () => {
    if (cursor <= 0) return;
    setCursor((c) => c - 1);
  };

  const onNext = () => {
    if (cursor >= trail.length - 1) return;
    setCursor((c) => c + 1);
  };

  const recordScore = (result) => {
    const asked = trail.filter((s) => s.answer).length;
    setLeaderboard(
      saveLeaderboardEntry({
        name: "Player",
        result,
        questions: asked || Math.max(trail.length - 1, 0),
      })
    );
  };

  const onCorrect = useCallback(async () => {
    if (!sessionId || !guess || busy) return;
    setBusy(true);
    setError(null);
    try {
      await api.learn(sessionId, guess.character.id, { wrongGuess: false });
      recordScore("correct");
      setDoneMessage(t(lang, "nailedIt", guess.character.name));
      setScreen("done");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [sessionId, guess, busy, lang, trail]);

  const openLearn = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const data = await api.listCharacters();
      setCharacters((data.items || []).filter((c) => c.id !== guess?.character?.id));
      setScreen("learn");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(false);
    }
  }, [busy, guess, lang]);

  const onLearnPick = useCallback(
    async (characterId, characterName) => {
      if (!sessionId || busy) return;
      setBusy(true);
      setError(null);
      try {
        await api.learn(sessionId, characterId, { wrongGuess: true });
        recordScore("learned");
        setDoneMessage(
          characterName ? t(lang, "learnedNamed", characterName) : t(lang, "learned")
        );
        setScreen("done");
      } catch (err) {
        fail(err);
      } finally {
        setBusy(false);
      }
    },
    [sessionId, busy, lang, trail]
  );

  const current = trail[cursor] || null;

  return (
    <div className="shell">
      <div className="atmosphere" aria-hidden="true" />

      {error && (
        <div className="toast" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="toast-x"
            onClick={() => setError(null)}
            aria-label="Dismiss"
          >
            ×
          </button>
        </div>
      )}

      {screen === "home" && (
        <HomePage
          lang={lang}
          onStart={startGame}
          onLeaderboard={openLeaderboard}
          onLangChange={changeLang}
          busy={busy}
        />
      )}
      {screen === "leaderboard" && (
        <LeaderboardPage lang={lang} entries={leaderboard} onBack={closeLeaderboard} />
      )}
      {screen === "game" && current && (
        <GamePage
          lang={lang}
          question={current.question}
          questionNumber={current.questionNumber}
          confidence={current.confidence}
          busy={busy}
          selectedAnswer={current.answer}
          canGoPrevious={cursor > 0}
          canGoNext={cursor < trail.length - 1}
          showEndConfirm={showEndConfirm}
          onAnswer={answer}
          onBack={goHome}
          onPrevious={onPrevious}
          onNext={onNext}
          onEndGameRequest={() => setShowEndConfirm(true)}
          onEndConfirm={goHome}
          onEndCancel={() => setShowEndConfirm(false)}
        />
      )}
      {screen === "guess" && (
        <GuessPage
          lang={lang}
          guess={guess}
          busy={busy}
          onCorrect={onCorrect}
          onWrong={openLearn}
          onBack={goHome}
        />
      )}
      {screen === "learn" && (
        <LearnPage
          lang={lang}
          wrongGuessName={guess?.character?.name}
          characters={characters}
          busy={busy}
          onPick={onLearnPick}
          onHome={goHome}
        />
      )}
      {screen === "done" && (
        <section className="page done">
          <div className="lang-toggle done-lang" role="group" aria-label={t(lang, "language")}>
            <button
              type="button"
              className={`btn sm lang-btn${lang === "en" ? " active" : ""}`}
              onClick={() => changeLang("en")}
            >
              {t(lang, "english")}
            </button>
            <button
              type="button"
              className={`btn sm lang-btn${lang === "hi" ? " active" : ""}`}
              onClick={() => changeLang("hi")}
            >
              {t(lang, "hindi")}
            </button>
          </div>
          <h2 className="title">{doneMessage || t(lang, "roundComplete")}</h2>
          <div className="actions">
            <button type="button" className="btn primary" onClick={startGame} disabled={busy}>
              {t(lang, "playAgain")}
            </button>
            <button type="button" className="btn ghost" onClick={goHome} disabled={busy}>
              {t(lang, "home")}
            </button>
            <button type="button" className="btn ghost" onClick={openLeaderboard} disabled={busy}>
              {t(lang, "leaderboard")}
            </button>
          </div>
        </section>
      )}

      {(screen === "game" || screen === "guess" || screen === "learn") && (
        <div className="floating-lang" aria-label={t(lang, "language")}>
          <button
            type="button"
            className={`btn sm lang-btn${lang === "en" ? " active" : ""}`}
            onClick={() => changeLang("en")}
          >
            EN
          </button>
          <button
            type="button"
            className={`btn sm lang-btn${lang === "hi" ? " active" : ""}`}
            onClick={() => changeLang("hi")}
          >
            हिं
          </button>
        </div>
      )}
    </div>
  );
}
