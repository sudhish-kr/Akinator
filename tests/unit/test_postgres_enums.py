"""PostgreSQL-specific bind values used by POST /game/start (create_session).

Alembic created native enums with lowercase *values* (in_progress, yes, …).
SQLAlchemy Enum() persists member *names* (IN_PROGRESS, YES, …) unless
values_callable is set. Health checks never insert a session, so only
/game/start surfaces this as HTTP 500 on Neon/Postgres.
"""

from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect

from app.db.models import GameAnswerValue, GameAnswer, GameSession, GameSessionStatus


def _bind(column, value) -> str:
    processor = column.type.bind_processor(postgresql_dialect())
    assert processor is not None
    return processor(value)


def test_game_session_status_binds_alembic_lowercase_values():
    bound = _bind(GameSession.__table__.c.status, GameSessionStatus.IN_PROGRESS)
    assert bound == "in_progress"
    assert bound != "IN_PROGRESS"
    col = GameSession.__table__.c.status
    assert col.type.enums == [
        "in_progress",
        "guessed_correct",
        "guessed_incorrect",
        "abandoned",
    ]


def test_game_answer_value_binds_alembic_lowercase_values():
    bound = _bind(GameAnswer.__table__.c.answer, GameAnswerValue.DONT_KNOW)
    assert bound == "dont_know"
    assert bound != "DONT_KNOW"
    assert GameAnswer.__table__.c.answer.type.enums == [
        "yes",
        "probably_yes",
        "dont_know",
        "probably_no",
        "no",
    ]
