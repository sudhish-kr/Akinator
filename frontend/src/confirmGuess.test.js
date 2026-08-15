/**
 * Regression: "Yes — you got it" must call POST /game/guess/confirm,
 * not /game/learn (wrong-guess path stays on learn).
 */
import assert from "node:assert/strict";
import { mock, test } from "node:test";

test("confirmGuess posts to /game/guess/confirm with correct=true", async () => {
  const calls = [];
  globalThis.fetch = mock.fn(async (url, options) => {
    calls.push({ url: String(url), options });
    return {
      ok: true,
      status: 200,
      json: async () => ({ status: "guessed_correct", next_question: null }),
    };
  });

  // Fresh module load so api.js picks up our fetch mock.
  const { api } = await import(`./api.js?t=${Date.now()}`);
  const out = await api.confirmGuess("11111111-1111-1111-1111-111111111111", {
    correct: true,
  });

  assert.equal(out.status, "guessed_correct");
  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /\/game\/guess\/confirm$/);
  assert.equal(calls[0].options.method, "POST");
  const body = JSON.parse(calls[0].options.body);
  assert.equal(body.correct, true);
  assert.equal(body.session_id, "11111111-1111-1111-1111-111111111111");
});

test("learn wrong-guess still posts to /game/learn", async () => {
  const calls = [];
  globalThis.fetch = mock.fn(async (url, options) => {
    calls.push({ url: String(url), options });
    return {
      ok: true,
      status: 200,
      json: async () => ({ status: "learned", updates: 0 }),
    };
  });

  const { api } = await import(`./api.js?t=${Date.now() + 1}`);
  await api.learn("11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222", {
    wrongGuess: true,
  });

  assert.equal(calls.length, 1);
  assert.match(calls[0].url, /\/game\/learn$/);
  const body = JSON.parse(calls[0].options.body);
  assert.equal(body.wrong_guess, true);
});

test("listRemainingCandidates queries the session candidate pool", async () => {
  const calls = [];
  globalThis.fetch = mock.fn(async (url, options) => {
    calls.push({ url: String(url), options });
    return {
      ok: true,
      status: 200,
      json: async () => ({ items: [{ id: "c1", name: "Smriti Mandhana", probability: 0.6 }], total: 1 }),
    };
  });

  const { api } = await import(`./api.js?t=${Date.now()}-remaining`);
  const out = await api.listRemainingCandidates("11111111-1111-1111-1111-111111111111", {
    category: "Sports",
    q: "Mandhana",
    pageSize: 40,
  });

  assert.equal(out.total, 1);
  assert.equal(out.items[0].name, "Smriti Mandhana");
  assert.equal(calls[0].options.method, "GET");
  assert.match(calls[0].url, /\/game\/candidates\/11111111-1111-1111-1111-111111111111\?/);
  assert.match(calls[0].url, /category=Sports/);
  assert.match(calls[0].url, /q=Mandhana/);
});
