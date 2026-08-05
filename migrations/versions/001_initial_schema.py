"""Initial schema — 6 tables per TDD v1.1 Section 5."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

game_session_status = postgresql.ENUM(
    "in_progress",
    "guessed_correct",
    "guessed_incorrect",
    "abandoned",
    name="game_session_status",
    create_type=False,
)
game_answer_value = postgresql.ENUM(
    "yes",
    "probably_yes",
    "dont_know",
    "probably_no",
    "no",
    name="game_answer_value",
    create_type=False,
)


def upgrade() -> None:
    game_session_status.create(op.get_bind(), checkfirst=True)
    game_answer_value.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("times_guessed_correctly", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("times_guessed_incorrectly", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_characters_is_active", "characters", ["is_active"])

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.String(512), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("times_asked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_information_gain", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_questions_is_active", "questions", ["is_active"])

    op.create_table(
        "character_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("likelihood", sa.Float(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("character_id", "question_id", name="uq_character_question"),
    )
    op.create_index("ix_character_answers_question_id", "character_answers", ["question_id"])

    op.create_table(
        "game_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", game_session_status, nullable=False, server_default="in_progress"),
        sa.Column("guessed_character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id"), nullable=True),
        sa.Column("actual_character_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("characters.id"), nullable=True),
        sa.Column("questions_asked_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_game_sessions_status", "game_sessions", ["status"])

    op.create_table(
        "game_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("game_sessions.id"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("answer", game_answer_value, nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("entropy_before", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "order_index", name="uq_session_order"),
    )
    op.create_index("ix_game_answers_session_id", "game_answers", ["session_id"])


def downgrade() -> None:
    op.drop_table("game_answers")
    op.drop_table("game_sessions")
    op.drop_table("character_answers")
    op.drop_table("questions")
    op.drop_table("characters")
    op.drop_table("users")
    game_answer_value.drop(op.get_bind(), checkfirst=True)
    game_session_status.drop(op.get_bind(), checkfirst=True)
