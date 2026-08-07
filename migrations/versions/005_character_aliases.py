"""Character aliases for knowledge-base search / display."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "character_aliases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "character_id",
            sa.Uuid(),
            sa.ForeignKey("characters.id"),
            nullable=False,
        ),
        sa.Column("alias", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("alias", name="uq_character_alias"),
    )
    op.create_index("ix_character_aliases_character_id", "character_aliases", ["character_id"])


def downgrade() -> None:
    op.drop_index("ix_character_aliases_character_id", table_name="character_aliases")
    op.drop_table("character_aliases")
