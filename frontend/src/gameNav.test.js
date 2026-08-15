/**
 * Game navigation + Hindi question translation regressions.
 * Run: npm test
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  answersForReplay,
  backEditIndex,
  canGoBack,
  popHistory,
  pushTrail,
} from "./gameHistory.js";
import { translateQuestion } from "./i18n/questions.js";

describe("gameHistory back / edit trail", () => {
  it("disables back when empty", () => {
    assert.equal(canGoBack([]), false);
    assert.equal(canGoBack([], null), false);
    assert.equal(popHistory([]), null);
  });

  it("stores answers and supports multi-step back", () => {
    const q1 = { id: "1", text: "Is this a real person?" };
    const q2 = { id: "2", text: "Are they from India?" };
    const q3 = { id: "3", text: "Is this a sports player?" };
    let trail = [];
    trail = pushTrail(trail, {
      question: q1,
      questionNumber: 1,
      confidence: 0.1,
      answer: "yes",
    });
    trail = pushTrail(trail, {
      question: q2,
      questionNumber: 2,
      confidence: 0.25,
      answer: "no",
    });
    trail = pushTrail(trail, {
      question: q3,
      questionNumber: 3,
      confidence: 0.4,
      answer: "probably_yes",
    });

    assert.equal(canGoBack(trail, null), true);
    const i3 = backEditIndex(trail, null);
    assert.equal(i3, 2);
    assert.equal(trail[i3].answer, "probably_yes");
    assert.equal(canGoBack(trail, i3), true);

    const i2 = backEditIndex(trail, i3);
    assert.equal(i2, 1);
    assert.equal(trail[i2].answer, "no");

    const i1 = backEditIndex(trail, i2);
    assert.equal(i1, 0);
    assert.equal(trail[i1].answer, "yes");
    assert.equal(canGoBack(trail, i1), false);
    assert.equal(backEditIndex(trail, i1), null);
  });

  it("builds replay answers that invalidate later steps", () => {
    const trail = [
      { question: { id: "1" }, questionNumber: 1, confidence: 0.1, answer: "yes" },
      { question: { id: "2" }, questionNumber: 2, confidence: 0.2, answer: "no" },
      { question: { id: "3" }, questionNumber: 3, confidence: 0.3, answer: "dont_know" },
      { question: { id: "4" }, questionNumber: 4, confidence: 0.4, answer: "yes" },
    ];
    assert.deepEqual(answersForReplay(trail, 2, "no"), ["yes", "no", "no"]);
    assert.deepEqual(answersForReplay(trail, 0, "probably_yes"), ["probably_yes"]);
  });

  it("ignores trail pushes without an answer", () => {
    const trail = pushTrail([], {
      question: { id: "1", text: "Q" },
      questionNumber: 1,
      confidence: 0,
    });
    assert.equal(trail.length, 0);
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

describe("polish UI contracts", () => {
  it("keeps Back visible but disabled on the first question", async () => {
    const fs = await import("node:fs/promises");
    const src = await fs.readFile(new URL("./components/GameHeader.jsx", import.meta.url), "utf8");
    assert.match(src, /aria-disabled="true"/);
    assert.match(src, /canBack/);
  });

  it("does not delay Start Game behind a second API timer", async () => {
    const fs = await import("node:fs/promises");
    const src = await fs.readFile(new URL("./pages/HomePage.jsx", import.meta.url), "utf8");
    assert.match(src, /startingRef/);
    assert.match(src, /onStart\(\)/);
    assert.doesNotMatch(src, /setTimeout\(\s*\(\)\s*=>\s*\{\s*onStart/);
  });
});
