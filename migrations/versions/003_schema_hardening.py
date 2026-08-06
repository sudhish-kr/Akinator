"""Phase 1 schema hardening: rejected_guesses table, session activity
tracking, and data-integrity CHECK constraints."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rejected_guesses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "session_id", sa.Uuid(), sa.ForeignKey("game_sessions.id"), nullable=False
        ),
        sa.Column(
            "character_id", sa.Uuid(), sa.ForeignKey("characters.id"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "character_id", name="uq_session_rejected_character"),
    )
    op.create_index("ix_rejected_guesses_session_id", "rejected_guesses", ["session_id"])

    op.add_column(
        "game_sessions",
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
    )

    # batch mode: SQLite cannot ALTER TABLE ADD CONSTRAINT; batch rebuilds the table
    with op.batch_alter_table("character_answers") as batch:
        batch.create_check_constraint(
            "ck_likelihood_range", "likelihood >= 0.0 AND likelihood <= 1.0"
        )
        batch.create_check_constraint("ck_sample_size_nonneg", "sample_size >= 0")


def downgrade() -> None:
    with op.batch_alter_table("character_answers") as batch:
        batch.drop_constraint("ck_likelihood_range", type_="check")
        batch.drop_constraint("ck_sample_size_nonneg", type_="check")
    op.drop_column("game_sessions", "last_activity_at")
    op.drop_index("ix_rejected_guesses_session_id", table_name="rejected_guesses")
    op.drop_table("rejected_guesses")
