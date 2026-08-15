import { useId } from "react";
import { messageKeyForState } from "./mascotMood.js";

const MOUTHS = {
  idle: "M86 128 Q100 138 114 128",
  curious: "M88 130 Q100 136 112 130",
  thinking: "M90 132 Q100 128 110 134",
  listening: "M88 130 Q100 134 112 130",
  happy: "M84 126 Q100 146 116 126",
  confused: "M88 134 Q100 126 112 134",
  excited: "M82 124 Q100 150 118 124",
  surprised: "M96 128 a4 5 0 1 0 0.1 0",
  sad: "M88 136 Q100 128 112 136",
};

/**
 * Original green MindGuess mind-orb — interactive states only.
 * Props:
 *  - state: idle|thinking|listening|happy|confused|excited|surprised|sad|curious
 *  - messageKey: optional i18n key override for speech bubble
 *  - look: { x, y } pupil offset in px
 *  - cue: question cue class for subtle styling
 */
export default function Mascot({
  state = "idle",
  t,
  compact = false,
  messageKey,
  look = { x: 0, y: 0 },
  cue = "default",
  confidence,
  entering = false,
}) {
  const uid = useId().replace(/:/g, "");
  const mood = MOUTHS[state] ? state : "idle";
  const key = messageKey || messageKeyForState(mood, { cue, confidence });
  const label = t ? t(key) : mood;
  const gazeX = Number(look?.x) || 0;
  const gazeY = Number(look?.y) || 0;
  const mouth = MOUTHS[mood] || MOUTHS.idle;
  const wideEyes = mood === "excited" || mood === "surprised";

  return (
    <div
      className={`mascot mascot--${mood} mascot-cue--${cue}${compact ? " mascot--compact" : ""}${entering ? " mascot--entering" : ""}`}
      role="img"
      aria-label={label}
      style={{
        "--gaze-x": `${gazeX}px`,
        "--gaze-y": `${gazeY}px`,
      }}
    >
      <div className="mascot-glow" aria-hidden="true" />
      <div className="mascot-particles" aria-hidden="true">
        <span className="mp mp1" />
        <span className="mp mp2" />
        <span className="mp mp3" />
        <span className="mp mp4" />
      </div>

      <svg
        className="mascot-svg"
        viewBox="0 0 200 220"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <radialGradient id={`mg-orb-${uid}`} cx="35%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#7ecfb5" />
            <stop offset="45%" stopColor="#2a8f74" />
            <stop offset="100%" stopColor="#0f4a3c" />
          </radialGradient>
          <radialGradient id={`mg-shine-${uid}`} cx="30%" cy="25%" r="40%">
            <stop offset="0%" stopColor="#fff" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#fff" stopOpacity="0" />
          </radialGradient>
        </defs>

        <ellipse
          className="mascot-floor-shadow"
          cx="100"
          cy="205"
          rx="48"
          ry="8"
          fill="rgba(15,40,34,0.18)"
        />

        <g className="mascot-figure">
          <circle className="mascot-body" cx="100" cy="108" r="72" fill={`url(#mg-orb-${uid})`} />
          <circle cx="100" cy="108" r="72" fill={`url(#mg-shine-${uid})`} />

          <circle
            className="mascot-ring"
            cx="100"
            cy="108"
            r="52"
            fill="none"
            stroke="rgba(244,251,248,0.28)"
            strokeWidth="2"
            strokeDasharray="6 10"
          />

          {/* Soft brows */}
          <path
            className="mascot-brow mascot-brow-l"
            d="M66 84 Q78 80 88 84"
            fill="none"
            stroke="rgba(15,46,38,0.55)"
            strokeWidth="2.4"
            strokeLinecap="round"
          />
          <path
            className="mascot-brow mascot-brow-r"
            d="M112 84 Q122 80 134 84"
            fill="none"
            stroke="rgba(15,46,38,0.55)"
            strokeWidth="2.4"
            strokeLinecap="round"
          />

          <g className={`mascot-eyes${wideEyes ? " is-wide" : ""}`}>
            <ellipse
              className="mascot-eye mascot-eye-l"
              cx="78"
              cy="100"
              rx={wideEyes ? 13 : 11}
              ry={wideEyes ? 15 : 13}
              fill="#f4fbf8"
            />
            <ellipse
              className="mascot-eye mascot-eye-r"
              cx="122"
              cy="100"
              rx={wideEyes ? 13 : 11}
              ry={wideEyes ? 15 : 13}
              fill="#f4fbf8"
            />
            <g className="mascot-pupils">
              <circle className="mascot-pupil mascot-pupil-l" cx="80" cy="102" r="5.5" fill="#0f2e26" />
              <circle className="mascot-pupil mascot-pupil-r" cx="124" cy="102" r="5.5" fill="#0f2e26" />
              <circle className="mascot-glint mascot-glint-l" cx="82" cy="99" r="1.8" fill="#fff" opacity="0.85" />
              <circle className="mascot-glint mascot-glint-r" cx="126" cy="99" r="1.8" fill="#fff" opacity="0.85" />
            </g>
            <rect className="mascot-lid mascot-lid-l" x="66" y="86" width="24" height="14" fill="#2a8f74" />
            <rect className="mascot-lid mascot-lid-r" x="110" y="86" width="24" height="14" fill="#2a8f74" />
          </g>

          <path
            className="mascot-mouth"
            d={mouth}
            fill={mood === "surprised" ? "#0f2e26" : "none"}
            stroke="#0f2e26"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
        </g>

        <g className="mascot-spark">
          <circle cx="148" cy="52" r="5" fill="#b8f0d8" />
          <circle cx="162" cy="40" r="3" fill="#d4f7e8" />
          <circle cx="138" cy="38" r="2.2" fill="#fff" opacity="0.8" />
        </g>
      </svg>

      <div className="mascot-bubble" aria-live="polite">
        <p className="mascot-bubble-text">{label}</p>
      </div>
    </div>
  );
}
