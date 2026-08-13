/**
 * Game navigation + Hindi question translation regressions.
 * Run: npm test
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { canGoBack, popHistory, pushHistory } from "./gameHistory.js";
import { translateQuestion } from "./i18n/questions.js";

describe("gameHistory back stack", () => {
  it("disables back when empty", () => {
    assert.equal(canGoBack([]), false);
    assert.equal(popHistory([]), null);
  });

  it("pushes snapshots and pops previous question state", () => {
    const q1 = { id: "1", text: "Is this a real person?" };
    const q2 = { id: "2", text: "Are they from India?" };
    let hist = [];
    hist = pushHistory(hist, { question: q1, questionNumber: 1, confidence: 0.1 });
    hist = pushHistory(hist, { question: q2, questionNumber: 2, confidence: 0.25 });
    assert.equal(canGoBack(hist), true);
    const once = popHistory(hist);
    assert.equal(once.snapshot.question.id, "2");
    assert.equal(once.snapshot.questionNumber, 2);
    assert.equal(once.snapshot.confidence, 0.25);
    const twice = popHistory(once.history);
    assert.equal(twice.snapshot.question.id, "1");
    assert.equal(canGoBack(twice.history), false);
  });
});

describe("Hindi question translation", () => {
  it("translates core identity questions naturally", () => {
    assert.equal(translateQuestion("hi", "Is this a real person?"), "क्या यह एक असली व्यक्ति है?");
    assert.equal(translateQuestion("hi", "Are they from India?"), "क्या वे भारत से हैं?");
    assert.equal(translateQuestion("hi", "Is this a sports player?"), "क्या वे खिलाड़ी हैं?");
    assert.equal(translateQuestion("hi", "Does your character play cricket?"), "क्या वे क्रिकेट खेलते हैं?");
    assert.equal(
      translateQuestion("hi", "Are they from African myths?"),
      "क्या वे अफ्रीकी लोककथाओं से हैं?"
    );
  });

  it("switches language without changing English source", () => {
    const src = "Are they from Japan?";
    assert.match(translateQuestion("hi", src), /जापान/);
    assert.equal(translateQuestion("en", src), src);
  });

  it("keeps English kid-friendly softens", () => {
    assert.equal(
      translateQuestion("en", "Are they a knight?"),
      "Does your character wear metal armor?"
    );
  });
});
