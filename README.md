# MindGuess AI

Bayesian guessing engine — a 20 Questions-style game built on entropy-based question selection.

## Quick Start

```powershell
cd "C:\Users\ARJUN PANDAT\Projects\mindguess-ai"
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

# Start PostgreSQL
docker compose up -d db

# Apply schema + seed dev data
alembic upgrade head
python scripts/seed_db.py

# Run API
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive API.

## Game Flow

1. `POST /game/start` — begin session, get first question
2. `POST /game/answer` — submit answer, get next question or `ready_to_guess`
3. `POST /game/guess` — engine reveals its top candidate
4. `POST /game/guess/confirm` — user confirms correct/incorrect (triggers self-learning)

## Admin Endpoints

- `GET /characters?page=1&page_size=20`
- `GET /questions?page=1&page_size=20`
- `GET /statistics`

## Run Tests

```powershell
pytest
```

## Project Structure

| Folder | Purpose |
|--------|---------|
| `app/engine/` | Pure algorithm — Bayesian, entropy, confidence |
| `app/db/` | SQLAlchemy models + repository |
| `app/services/` | Game orchestration + self-learning |
| `app/api/` | REST endpoints |
| `app/workers/` | Background session cleanup |
| `tests/` | Unit tests (TDD Section 2.6 golden fixture) |

## Implementation Status

- [x] Phase 1–3: Setup, DB schema, AI engine
- [x] Phase 4: Game APIs
- [x] Phase 5: Self-learning + session abandonment
- [x] Phase 6: Admin list + statistics APIs
- [ ] Auth (JWT) — SDD v1.0
- [ ] Integration tests against PostgreSQL
- [ ] Production deployment
