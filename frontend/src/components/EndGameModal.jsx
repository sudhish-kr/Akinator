export default function EndGameModal({ t, onContinue, onEnd }) {
  return (
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
          <button type="button" className="btn primary" onClick={onContinue}>
            {t("game.endConfirmContinue")}
          </button>
          <button type="button" className="btn ghost" onClick={onEnd}>
            {t("game.endConfirmEnd")}
          </button>
        </div>
      </div>
    </div>
  );
}
