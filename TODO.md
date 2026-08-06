# Production Readiness Audit — TODO

Audit date: 2026-08-06  
Scope: broken imports, dead/duplicate/unused code, API consistency, frontend routing, error handling, migrations, env vars, security, performance.  
**No fixes applied. No features added.**

---

## Critical

- [ ] **Broken Alembic chain — migration `003` missing**  
  `004_auth_tokens.py` sets `down_revision = "003"`, but `migrations/versions/` only has `001`, `002`, `004`. `alembic history` / `upgrade head` fails with `KeyError: '003'`. Fresh deploys cannot migrate.

- [ ] **Default JWT secret is a known placeholder**  
  `app/config.py` defaults `jwt_secret` to `"change-me-in-production"`; `.env.example` ships a similar value. `docker-compose.yml` never sets `JWT_SECRET`. Tokens can be forged if deployed without an override.

- [ ] **Game client never finishes sessions via `/game/guess/confirm`**  
  Frontend (`App.jsx` / `api.js`) only calls `POST /game/learn`. `GameService.learn` updates likelihoods but does **not** set session status, `ended_at`, or guess counters. Sessions stay `in_progress`; `times_guessed_*` and accuracy stats stay wrong. Confirm path exists but is unused by the shipping client.

- [ ] **No production FE↔API wiring**  
  Frontend uses relative API paths. Vite proxy is **dev-only** (`frontend/vite.config.js`). Backend has **no CORS**. Split-host production deploy is undefined / broken unless an undocumented reverse proxy is assumed.

---

## High

- [ ] **Dockerfile omits migrations**  
  `Dockerfile` copies only `pyproject.toml`, `README.md`, and `app/`. Container images cannot run Alembic even after the revision chain is fixed.

- [ ] **docker-compose is production-unsafe**  
  `DEBUG: "true"`, weak DB password `mindguess`, Postgres published on host `5432:5432`, no `JWT_SECRET` / `ENVIRONMENT=production`.

- [ ] **Public unauthenticated catalog + statistics**  
  `GET /characters`, `/questions`, `/statistics` have no auth (`admin.py`). Admin UI reads them without a token. Exposes full knowledge base, accuracy, and weakest characters to anyone.

- [ ] **Game APIs are unauthenticated**  
  Knowledge of `session_id` is enough to answer, guess, and learn. No ownership binding beyond optional user on start.

- [ ] **No rate limiting**  
  Auth login/register and game endpoints have no throttling (brute-force / abuse risk). Documented as deferred in architecture notes.

- [ ] **In-process session cache blocks multi-worker scale**  
  `SessionStore` + `MemoryCache` are process-local. Multiple uvicorn workers / replicas do not share live sessions; rehydration stamps every miss.

- [ ] **Full knowledge matrix loaded per game start/rehydrate**  
  `GameService._load_playable_data` loads all active characters, questions, and likelihoods into memory each start/rehydrate — grows poorly with catalog size.

- [ ] **Question selection cost O(|C| × |Q| × answers)**  
  Entropy simulations run every turn (`selector.py`). Documented bottleneck; will dominate latency as catalogs grow.

- [ ] **Admin lists / Learn picker hard-capped at `page_size=100`**  
  Backend paginates (max 100). Frontend always requests page 1 / size 100 with no paging UI → silent truncation past 100 rows. Stats “learning count” also derived from that capped sample.

- [ ] **Admin auth lifecycle incomplete**  
  Refresh token returned by login is ignored (not stored, not sent on logout). No 401/403 → clear session / redirect. Expired access token leaves UI “logged in” while mutations fail. Access token in `localStorage` (XSS-exfiltrable).

- [ ] **Admin UI role gate is client-only**  
  Role checked from stored JSON in `Login.jsx` / `AdminApp.jsx`. Writes are server-protected (`require_admin`) — good — but forged localStorage still shows admin chrome; public GETs remain available.

- [ ] **Game screens not in the URL**  
  `App.jsx` uses React state (`home|game|guess|learn|done`). Browser Back / refresh mid-game loses progress and returns to home. Admin tabs (`stats|characters|questions`) are also not deep-linkable (`#/admin/characters` still opens Statistics).

- [ ] **Unused Three.js / R3F dependencies**  
  `Scene.jsx` is gone; `package.json` still lists `three`, `@react-three/fiber`, `@react-three/drei`, `@react-three/postprocessing` — install weight and accidental reintroduction risk.

- [ ] **Models vs intended schema hardening drift**  
  Intended `003` (rejected guesses, `last_activity_at`, likelihood CHECKs) never landed on `main`. Cleanup still uses `started_at` only; long active games can be abandoned; idle short games kept. Docs note rejected-guess gap for rehydration.

---

## Medium

- [ ] **Duplicate / parallel answer enums**  
  Engine `Answer` (`engine/constants.py`) vs DB `GameAnswerValue` (`db/models.py`) — drift risk.

- [ ] **Duplicated frontend request helpers**  
  `frontend/src/api.js` and `frontend/src/admin/api.js` share nearly identical `request()` / error parsing.

- [ ] **Near-duplicate admin CRUD pages**  
  `Characters.jsx` and `Questions.jsx` share the same list/search/form/edit/delete pattern (~190 lines each).

- [ ] **Dead backend helpers never called**  
  - `SessionStore.purge_expired` / `MemoryCache.purge_expired` — cleanup worker only abandons DB sessions  
  - `UserRepository.revoke_all_refresh_tokens`  
  - `require_user` in `deps.py`  
  - `decode_access_token` in `auth_service.py`  
  - `CharacterRef` in `engine/models.py`  
  - `consecutive_dont_know_cap` deleted unused in `selector.py`  
  - `passlib` declared but code uses `bcrypt` directly  

- [ ] **`seed_db.py` bypasses Alembic**  
  Uses `Base.metadata.create_all` — schema can diverge from migration history.

- [ ] **Learning path N+1 queries**  
  `learning_service.py` loops per-question DB lookups when loading knowledge.

- [ ] **`get_statistics` loads candidates in Python then sorts**  
  Repository pulls characters with guesses into memory for ranking.

- [ ] **`get_session` always `selectinload`s answers**  
  Extra load even when callers do not need answers.

- [ ] **No global exception handler**  
  Unhandled errors become generic FastAPI 500s; readiness probe catches broad `Exception` without logging.

- [ ] **Answer API accepts free-form `str`**  
  Validation deferred to session manager rather than schema enum — inconsistent error shapes.

- [ ] **OpenAPI docs always enabled**  
  `/docs` / `/redoc` not gated by `DEBUG` / environment.

- [ ] **`DEBUG=true` enables SQLAlchemy echo**  
  May log query detail (`db/session.py`).

- [ ] **Weak password policy**  
  Length-only (`min_length=8`) in auth schemas.

- [ ] **Soft-delete only for characters/questions**  
  No hard DELETE; retired rows can be reactivated via PATCH. Admin “delete” is `is_active: false`.

- [ ] **Frontend routing edge cases**  
  Unknown hashes (`#/foo`) fall through to game. Switching `#/` ↔ `#/admin` remounts and drops in-progress game with no confirm.

- [ ] **Error handling gaps in game UI**  
  Failed `submitAnswer` may recover via `getState` and clear the original error. `GamePage` / `GuessPage` return `null` on missing data → blank shell.

- [ ] **Admin Statistics over-fetches catalogs**  
  Loads full character + question pages only to derive totals / synthetic learning count; inaccurate beyond page cap.

- [ ] **Game endpoints unused by FE**  
  `POST /game/guess/confirm`, `POST /game/suggest-character` exist server-side but have no client callers. Auth `register` / `refresh` also unused by FE.

- [ ] **Stale `dist/` risk if someone deploys from repo without rebuild**  
  `dist/` is gitignored (good); ensure deploy pipeline always rebuilds.

- [ ] **Untracked `requirements.txt` duplicates `pyproject.toml`**  
  Risk of dependency drift between the two sources.

---

## Low

- [ ] **Version mismatch**  
  `app/main.py` advertises `0.2.0`; `pyproject.toml` is `0.1.0`.

- [ ] **Docs API map outdated**  
  `docs/ARCHITECTURE.md` still mentions old paths (`/game/{id}/state`, `POST /game/guess`) and migrations `001`/`002` only.

- [ ] **Admin list endpoints duplicate response shaping**  
  Inline item building vs existing helpers in `admin.py`.

- [ ] **Engine defaults duplicated**  
  Constants in `engine/constants.py` overlap `Settings` defaults in `config.py`.

- [ ] **`.env.example` ships `DEBUG=true`**  
  Easy to copy into a “prod” env file unchanged.

- [ ] **App version / logout semantics**  
  Logout can return success with `revoked: 0` for invalid tokens (intentional soft-fail, but opaque).

- [ ] **`get_optional_user_id` swallows bad JWTs**  
  Expired/invalid bearer treated as anonymous guest.

- [ ] **Dual CSS always loaded**  
  `Root.jsx` imports game + admin CSS on every route.

- [ ] **`StatisticsResponse.lowest_accuracy_characters` unused in UI**  
  Backend returns it; admin Statistics page does not render it.

- [ ] **Guess `image_url` ignored**  
  API returns it; `GuessPage` shows letter avatar only.

- [ ] **Admin entry discoverable on public home**  
  Intentional link to `#/admin` — confirm threat model.

- [ ] **`python-jose` maintenance posture**  
  Prefer evaluating maintained JWT libraries for long-term security support.

- [ ] **No F401/F841 unused-import failures under Ruff**  
  Import hygiene is currently clean; keep in CI.

---

## Suggested fix order (reference only — not started)

1. Restore or re-parent migration `003` so Alembic upgrades.  
2. Align client finish flow with `confirm_guess` (or make `learn` terminal + update counters/status).  
3. Force strong `JWT_SECRET`; disable DEBUG in compose/prod; document FE proxy/CORS.  
4. Auth-gate sensitive catalog/stats; add rate limits.  
5. Pagination + auth refresh/401 handling on admin.  
6. Session store / matrix load before multi-worker scale.  
7. Remove dead Three.js deps and unused helpers.

---

*End of audit. No code changes. No commit.*
