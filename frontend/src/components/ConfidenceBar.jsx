import { formatConfidencePercent } from "../confidence.js";
import { HIGH_CONF } from "./mascotMood.js";

export default function ConfidenceBar({ confidence, label }) {
  const pct = formatConfidencePercent(confidence);
  const hot = typeof confidence === "number" && confidence >= HIGH_CONF;
  return (
    <div className={`confidence-bar${hot ? " is-hot" : ""}`}>
      <div className="confidence-bar-meta">
        <span className="hud-label">{label}</span>
        <strong className="hud-value" aria-live="polite">
          {pct}%
        </strong>
      </div>
      <div
        className="bar"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-label={label}
      >
        <div className="bar-fill" style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
      </div>
    </div>
  );
}
