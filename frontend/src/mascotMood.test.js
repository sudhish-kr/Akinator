/**
 * Mascot mood helpers — pure frontend, no API.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  classifyQuestionCue,
  reactionAfterAnswer,
  reactionMessageKey,
  resolveBaseMood,
} from "./components/mascotMood.js";

describe("mascotMood", () => {
  it("classifies question cues from text", () => {
    assert.equal(classifyQuestionCue("Is your character from India?"), "country");
    assert.equal(classifyQuestionCue("Does your character play cricket?"), "sports");
    assert.equal(classifyQuestionCue("Is your character a real person?"), "identity");
    assert.equal(classifyQuestionCue("Do they wear a hat?"), "default");
  });

  it("maps answers to short reactions", () => {
    assert.equal(reactionAfterAnswer("yes"), "happy");
    assert.equal(reactionAfterAnswer("probably_yes"), "curious");
    assert.equal(reactionAfterAnswer("dont_know"), "listening");
    assert.equal(reactionAfterAnswer("probably_no"), "confused");
    assert.equal(reactionAfterAnswer("no"), "confused");
    assert.equal(reactionMessageKey("yes"), "mascot.happyYes");
    assert.equal(reactionMessageKey("dont_know"), "mascot.dontKnow");
  });

  it("resolves base mood from busy/listening/confidence", () => {
    assert.equal(resolveBaseMood({ busy: true }), "thinking");
    assert.equal(resolveBaseMood({ busy: false, listening: true }), "listening");
    assert.equal(resolveBaseMood({ busy: false, confidence: 0.5 }), "excited");
    assert.equal(resolveBaseMood({ busy: false, confidence: 0.1 }), "idle");
  });
});
