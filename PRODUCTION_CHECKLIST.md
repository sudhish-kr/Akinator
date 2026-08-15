# Production Validation Checklist

**Date:** 2026-08-06  
**Branch:** `cursor/production-readiness-todo` (validation run against local workspace)  
**Scope:** Validate only — no code changes, no commit.

---

## Summary

| Check | Result |
|-------|--------|
| Backend starts successfully | **PASS*** |
| Frontend builds successfully | **PASS** |
| Database migrations succeed | **PASS** |
| All tests pass | **FAIL** |
| Authentication works | **PASS** |
| Game flow works end-to-end | **PASS** |
| Admin dashboard works | **PASS** |
| Learning flow works | **PASS** |
| No broken imports | **PASS** |
| No missing environment variables | **FAIL** |

\*Backend starts only when `JWT_SECRET` is provided in the process environment (or a populated `.env`). The checked-in local `.env` does **not** currently set `JWT_SECRET`.

**Deployment readiness: NOT READY**

---

## Detailed results

### Backend starts successfully — PASS*

| Step | Result | Evidence |
|------|--------|----------|
| Import `app.main` with `JWT_SECRET` set | PASS | `APP_OK MindGuess AI` |
| `GET /health` on live uvicorn (`127.0.0.1:8765`) | PASS | `200 {"status":"ok"}` |
| Reject empty `JWT_SECRET` | PASS (expected) | `Settings(jwt_secret='')` → `ValidationError` |
| Start using only on-disk `.env` | FAIL for current machine | `JWT_SECRET_in_dotenv_file=False` |

### Frontend builds successfully — PASS

| Step | Result | Evidence |
|------|--------|----------|
| `npm run build` | PASS | Vite build OK; `dist/` produced (`BUILD_EXIT=0`) |

Notes:
- `frontend/.env` is **missing**; `VITE_API_BASE_URL` is documented in `frontend/.env.example` only.
- Build still succeeds (empty base → same-origin relative URLs). Split-host deploys need the env var at build time.

### Database migrations succeed — PASS

| Step | Result | Evidence |
|------|--------|----------|
| `alembic history` chain `001→002→003→004` | PASS | Head = `004` |
| Fresh DB `upgrade head` | PASS | `MIGRATE_UP_EXIT=0` |
| `downgrade base` | PASS | `MIGRATE_DOWN_EXIT=0` |
| Re-`upgrade head` | PASS | `MIGRATE_REUP_EXIT=0` |
| Existing `mindguess_dev.db` | PASS | Alembic version `004`; seeded data present (4 characters, 5 questions) |

### All tests pass — FAIL

| Step | Result | Evidence |
|------|--------|----------|
| `pytest -q` | **FAIL** | **77 passed, 1 failed** |

**Failure:**
- `tests/integration/test_game_flow.py::test_rejected_guess_not_reguessed_after_cache_loss`
- Calls outdated paths: `POST /game/guess` (404) and later `GET /game/{id}/state`
- Shipping API uses `GET /game/guess/{session_id}` and `GET /game/state/{session_id}`
- Failure is test/API contract drift, not a live game-client break in this run

### Authentication works — PASS

Live API against uvicorn:

| Step | Result |
|------|--------|
| `POST /auth/register` | PASS (`201`) |
| `POST /auth/login` | PASS (`200`, role `user`) |
| Admin role after elevation | PASS (role `admin` on re-login) |
| `POST /auth/logout` | PASS (`200`) |
| Admin mutation without token | PASS (blocked `401`/`403`) |

### Game flow works end-to-end — PASS

| Step | Result |
|------|--------|
| `POST /game/start` | PASS |
| Answer loop → `ready_to_guess` | PASS |
| `GET /game/guess/{session_id}` | PASS (returned a character) |

### Admin dashboard works — PASS

API surface used by the admin UI (no browser UI automation in this run):

| Step | Result |
|------|--------|
| `GET /statistics` | PASS |
| `GET /characters`, `GET /questions` | PASS |
| `POST /admin/characters` (admin JWT) | PASS (`201`) |
| Soft-delete `PATCH is_active=false` | PASS |
| Unauthenticated admin write blocked | PASS |

### Learning flow works — PASS

| Step | Result | Evidence |
|------|--------|----------|
| Correct path `POST /game/learn` (`wrong_guess=false`) | PASS | `200` + `status=learned` |
| Session closed after learn | PASS | Second learn → `409` (already closed) |
| Wrong-guess path `wrong_guess=true` | PASS | `200` on live API |

### No broken imports — PASS

Imported successfully: `app.main`, `app.config`, auth/game/admin routes, `game_service`, `auth_service`, `session_manager`, bayesian/selector/learning/confidence engines.  
`IMPORT_FAILURES=0`

### No missing environment variables — FAIL

| Variable | Required? | Status |
|----------|-----------|--------|
| `JWT_SECRET` | **Yes** (startup) | **MISSING** from local `.env` and process env by default |
| `DATABASE_URL` | Recommended | Present via `.env` (SQLite) |
| `CORS_ORIGINS` | Recommended for split FE/API | Defaults exist in `Settings` / `.env.example`; CORS preflight verified with default origins |
| `VITE_API_BASE_URL` | Required for split-origin FE | **MISSING** (`frontend/.env` absent) |

CORS verification (after correcting header inspection):

| Step | Result |
|------|--------|
| `OPTIONS /game/start` with Origin `http://127.0.0.1:5173` | PASS — `access-control-allow-origin: http://127.0.0.1:5173` |
| `GET /health` with same Origin | PASS — ACAO echoed |

---

## Blocking issues

1. **`JWT_SECRET` not set in local `.env`** — application will not start until operators set a non-empty secret (required by `app/config.py`).
2. **`frontend/.env` missing `VITE_API_BASE_URL`** — production/split-host frontend will call the wrong origin unless set at build/dev time.
3. **Test suite not green** — 1 failing integration test (`test_rejected_guess_not_reguessed_after_cache_loss`) uses obsolete game routes; blocks “all tests pass” gate.
4. **No admin user in seed DB by default** — `users=0` before validation; admin UI needs an admin account provisioned for real ops (not an import/build failure, but a deploy prerequisite).

---

## Deployment readiness

### Verdict: **NOT READY for production**

Functional core (engine/API game path, learn close, auth, admin mutations, migrations, frontend build, imports, CORS defaults) validated under a **temporary** `JWT_SECRET`.

**Before production deploy, at minimum:**
1. Set a strong `JWT_SECRET` in the deployment environment (never commit it).
2. Set `VITE_API_BASE_URL` for the frontend build targeting the real API.
3. Set `CORS_ORIGINS` to the real frontend origin(s) (no `*`).
4. Fix or update the failing integration test so CI is green.
5. Provision at least one admin user.
6. Confirm Dockerfile/compose include migrations + production `DEBUG=false` (out of this checklist’s pass/fail list, but still deploy risk).

---

## Validation environment notes

- Backend probed on `http://127.0.0.1:8765` with ephemeral process `JWT_SECRET` and `DATABASE_URL=sqlite+aiosqlite:///./mindguess_dev.db`.
- Migrations also verified on a throwaway SQLite file (upgrade/downgrade/re-upgrade).
- Validation uvicorn process was stopped after checks.
- No application source files were modified for this report.

---

*End of production validation report.*
