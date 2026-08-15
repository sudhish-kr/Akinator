import { LanguageSwitch } from "../i18n/index.jsx";

export default function GameHeader({
  t,
  canBack,
  busy,
  onBack,
  onEndGame,
  voiceOn,
  onToggleVoice,
  voiceAvailable,
}) {
  return (
    <header className="game-header">
      <div className="game-header-brand">
        {canBack ? (
          <button
            type="button"
            className="btn ghost game-nav-btn game-nav-back"
            disabled={busy}
            onClick={onBack}
          >
            {t("game.back")}
          </button>
        ) : (
          <button
            type="button"
            className="btn ghost game-nav-btn game-nav-back"
            disabled
            aria-disabled="true"
          >
            {t("game.back")}
          </button>
        )}

        <span className="game-logo" aria-hidden="true">
          <svg viewBox="0 0 32 32" width="28" height="28">
            <circle cx="16" cy="16" r="14" fill="#1f6f5b" />
            <circle cx="16" cy="16" r="7" fill="none" stroke="#b8f0d8" strokeWidth="1.6" />
            <circle cx="16" cy="16" r="2.4" fill="#f4fbf8" />
          </svg>
        </span>
        <span className="game-header-name">
          Mind<span>Guess</span>
        </span>
      </div>

      <div className="game-header-controls">
        <LanguageSwitch className="lang-switch-header" />

        {voiceAvailable && (
          <button
            type="button"
            className={`btn ghost voice-chip ${voiceOn ? "on" : ""}`}
            onClick={onToggleVoice}
            aria-pressed={voiceOn}
          >
            {voiceOn ? `🔊 ${t("game.voiceOn")}` : `🔇 ${t("game.voiceOff")}`}
          </button>
        )}

        <button
          type="button"
          className="btn ghost game-nav-btn game-nav-end"
          disabled={busy}
          onClick={onEndGame}
        >
          {t("game.endGame")}
        </button>
      </div>
    </header>
  );
}
